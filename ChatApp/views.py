import json
import logging
from datetime import datetime

import redis
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from .forms import CustomUserCreationForm, CustomAuthenticationForm

from .forms import StartConversationForm
from .models import Conversation, CustomUser

logger = logging.getLogger(__name__)


# ---------------------------- Register ----------------------------

@csrf_exempt
@ratelimit(key='ip', rate='5/h', method='POST', block=True)
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            logger.info(f"User '{user.email}' registered successfully.")
            return redirect('chat:conversations_list')
        else:
            logger.error("Form submission is not valid. Errors:")
            for field, errors in form.errors.items():
                for error in errors:
                    logger.error(f"{field}: {error}")
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/authentication/register.html', {'form': form})


# ---------------------------- Login ----------------------------

@csrf_exempt
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def user_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
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

    return render(request, 'users/authentication/login.html', {'form': form})


# ---------------------------- Logout ----------------------------

def user_logout(request):
    logout(request)
    logger.info("User logged out.")
    return redirect('chat:login')


# ---------------------------- Conversation List ----------------------------

@login_required
@csrf_exempt
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
@csrf_exempt
@ratelimit(key='user', rate='5/m', method='GET', block=True)
def conversation_view(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in [conversation.user1, conversation.user2]:
        return HttpResponseForbidden("You do not have permission to access this conversation.")

    participant = conversation.user2 if conversation.user1 == request.user else conversation.user1

    messages = fetch_messages_from_redis(conversation)

    return render(request, 'chat/conversation/conversation_view.html', {
        'conversation': conversation,
        'participant': participant,
        'messages': messages,
        'conversation_id': conversation_id,
    })


# ---------------------------- Start New Conversation ----------------------------

@login_required
@csrf_exempt
def start_conversation(request):
    if request.method == 'POST':
        form = StartConversationForm(request.POST)
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
        form = StartConversationForm()

    return render(request, 'chat/conversation/conversation_start.html', {'form': form})


# ---------------------------- Search users by email ----------------------------

@login_required
@csrf_exempt
@ratelimit(key='user', rate='5/m', method='GET', block=True)
def search_users(request):
    if 'q' in request.GET:
        search_term = request.GET['q']
        users = CustomUser.objects.filter(email__icontains=search_term).exclude(id=request.user.id)[:10]
        user_data = [{'id': user.id, 'email': user.email} for user in users]
        return JsonResponse(user_data, safe=False)
    else:
        return JsonResponse([], safe=False)
