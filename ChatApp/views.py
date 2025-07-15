import json
import logging
from datetime import datetime

# pragma: no cover
import redis
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.urls import reverse, NoReverseMatch
from django.contrib.postgres.search import SearchVector
from django.db.models import Q
from django.db.models.functions import Length
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django_ratelimit.decorators import ratelimit
from .forms import CustomUserCreationForm, CustomAuthenticationForm

from .forms import StartConversationForm, ChatRoomForm
from .models import Conversation, CustomUser, AuditLog, ChatRoom, RoomMessage

logger = logging.getLogger(__name__)


# ---------------------------- Register ----------------------------

@ratelimit(key='ip', rate='5/h', method='POST', block=True)
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            import pyotp
            user.totp_secret = pyotp.random_base32()
            user.save(update_fields=['totp_secret'])
            logger.info(f"User '{user.email}' registered successfully with 2FA secret.")
            return render(request, 'users/authentication/2fa_setup.html', {'secret': user.totp_secret})
        else:
            logger.error("Form submission is not valid. Errors:")
            for field, errors in form.errors.items():
                for error in errors:
                    logger.error(f"{field}: {error}")
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/authentication/register.html', {'form': form})


# ---------------------------- Login ----------------------------

@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def user_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            logger.info(f"User '{user.email}' logged in successfully.")
            return redirect('chat:conversations_list')
        else:
            logger.error("Invalid login credentials. Errors:")
            for field, errors in form.errors.items():
                for error in errors:
                    logger.error(f"{field}: {error}")
            return render(request, 'users/authentication/login.html', {'form': form})
    else:
        form = CustomAuthenticationForm()

    oidc_url = saml_url = None
    try:
        oidc_url = reverse('socialaccount_login', args=['openid_connect'])
    except NoReverseMatch:
        pass
    try:
        saml_url = reverse('saml2_login')
    except NoReverseMatch:
        pass

    return render(
        request,
        'users/authentication/login.html',
        {'form': form, 'oidc_login_url': oidc_url, 'saml_login_url': saml_url},
    )


# ---------------------------- Logout ----------------------------

def user_logout(request):
    logout(request)
    logger.info("User logged out.")
    return redirect('chat:login')


# ---------------------------- Conversation List ----------------------------

@login_required
@ratelimit(key='user', rate='10/h', method='GET', block=True)
def conversations_list(request):
    try:
        conversations = Conversation.objects.filter(Q(user1=request.user) | Q(user2=request.user))

        conversation_data = []
        for conversation in conversations:
            if conversation.user1 == request.user:
                participant = conversation.user2
            else:
                participant = conversation.user1
            conversation_data.append({
                'id': conversation.id,
                'participant': participant,
            })
        logger.info(f"User '{request.user.email}' fetched conversation list successfully.")

    except Exception as e:
        conversation_data = []
        logger.error(f"An error occurred while fetching conversation list: {str(e)}")

    return render(request, 'chat/conversation/conversations_list.html', {'conversations': conversation_data})


# ---------------------------- Fetch messages from Redis ----------------------------

def fetch_messages_from_redis(conversation):
    try:
        redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)
        conversation_key = f"conversation_{conversation.id}"
        message_strings = redis_client.lrange(conversation_key, 0, -1)
        messages = []
        for message_string in message_strings:
            message_data = json.loads(message_string.decode("utf-8"))
            message_data['formatted_timestamp'] = datetime.strptime(message_data['timestamp'],
                                                                    "%Y-%m-%d %H:%M:%S.%f").strftime("%m/%d/%Y %H:%M")
            messages.append(message_data)
        logger.info(f"Fetched messages for conversation {conversation.id}.")

    except redis.ConnectionError as e:
        messages = []
        logger.error(f"Redis connection error: {str(e)}")

    except Exception as e:
        messages = []
        logger.error(f"An error occurred while fetching messages from Redis: {str(e)}")

    finally:
        if 'redis_client' in locals():
            redis_client.close()

    return messages


# ---------------------------- Conversation View ----------------------------

@login_required
@ratelimit(key='user', rate='5/m', method='GET', block=True)
def conversation_view(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in [conversation.user1, conversation.user2]:
        return HttpResponseForbidden("You do not have permission to access this conversation.")

    return render(request, 'chat/conversation/conversation_view.html', {
        'conversation': conversation,
    })


@login_required
def conversations_sidebar(request):
    query = request.GET.get('q', '').strip()
    conversations = Conversation.objects.filter(Q(user1=request.user) | Q(user2=request.user))
    data = []
    for convo in conversations:
        participant = convo.user2 if convo.user1 == request.user else convo.user1
        if query and query.lower() not in participant.email.lower():
            continue
        last_msg = convo.messages.order_by('-timestamp').first()
        preview = last_msg.content[:30] + '…' if last_msg else ''
        data.append({'id': convo.id, 'participant': participant, 'preview': preview})
    return render(request, 'chat/conversation/sidebar.html', {'conversations': data})


@login_required
def conversation_messages(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in [conversation.user1, conversation.user2]:
        return HttpResponseForbidden("You do not have permission to access this conversation.")

    participant = conversation.user2 if conversation.user1 == request.user else conversation.user1
    messages = fetch_messages_from_redis(conversation)

    return render(request, 'chat/conversation/messages_partial.html', {
        'conversation': conversation,
        'participant': participant,
        'messages': messages,
    })


# ---------------------------- Start New Conversation ----------------------------

@login_required
def start_conversation(request):
    if request.method == 'POST':
        form = StartConversationForm(request.POST, request=request)
        if form.is_valid():
            participants = form.cleaned_data['participants']
            existing_conversation = Conversation.objects.filter(
                Q(user1=request.user, user2=participants) | Q(user1=participants, user2=request.user)
            )

            if existing_conversation.exists():
                return redirect('chat:view_conversation', conversation_id=existing_conversation.first().id)
            else:
                conversation = Conversation.objects.create(user1=request.user, user2=participants)
                logger.info(f"Started a new conversation {conversation.id}.")
                return redirect('chat:view_conversation', conversation_id=conversation.id)
    else:
        form = StartConversationForm(request=request)

    return render(request, 'chat/conversation/conversation_start.html', {'form': form})


# ---------------------------- Search users by email ----------------------------


@login_required
def search_users(request):
    try:
        if 'q' in request.GET:
            search_term = request.GET['q'].strip()
            if search_term:
                search_query = Q(email__icontains=search_term)
                users = CustomUser.objects.filter(search_query).exclude(id=request.user.id)[:10]
                user_data = [{'id': user.id, 'email': user.email} for user in users]
                return JsonResponse(user_data, safe=False)
        return JsonResponse([], safe=False)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred while processing the request'}, status=500)


@login_required
def audit_logs_view(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    logs = AuditLog.objects.all()[:100]
    data = [
        {
            'timestamp': log.timestamp.isoformat(),
            'user': log.user.email if log.user else None,
            'action': log.action,
            'details': log.details,
            'hash': log.hash,
            'previous_hash': log.previous_hash,
        }
        for log in logs
    ]
    return JsonResponse(data, safe=False)


# ---------------------------- Chat Rooms ----------------------------

@login_required
def rooms_list(request):
    rooms = ChatRoom.objects.all()
    return render(request, 'chat/rooms/rooms_list.html', {'rooms': rooms})


@login_required
def create_room(request):
    if request.method == 'POST':
        form = ChatRoomForm(request.POST)
        if form.is_valid():
            room = form.save()
            room.members.add(request.user)
            return redirect('chat:room_view', room_id=room.id)
    else:
        form = ChatRoomForm()
    return render(request, 'chat/rooms/create_room.html', {'form': form})


@login_required
def join_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    room.members.add(request.user)
    return redirect('chat:room_view', room_id=room.id)


@login_required
def room_view(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if request.user not in room.members.all():
        return HttpResponseForbidden('You are not a member of this room.')
    return render(request, 'chat/rooms/room_view.html', {'room': room})


@login_required
def room_messages(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if request.user not in room.members.all():
        return HttpResponseForbidden('You are not a member of this room.')
    messages = RoomMessage.objects.filter(room=room)
    return render(request, 'chat/rooms/messages_partial.html', {
        'room': room,
        'messages': messages,
    })
