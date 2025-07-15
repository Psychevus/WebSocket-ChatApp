from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'chat'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='chat:login', permanent=False)),

    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    path('create/', views.start_conversation, name='start_conversation'),
    path('view/<int:conversation_id>/', views.conversation_view, name='view_conversation'),
    path('sidebar/', views.conversations_sidebar, name='sidebar'),
    path('messages/<int:conversation_id>/', views.conversation_messages, name='conversation_messages'),
    path('conversations/', views.conversations_list, name='conversations_list'),
    path('search-users/', views.search_users, name='search_users'),
    path('rooms/', views.rooms_list, name='rooms_list'),
    path('rooms/create/', views.create_room, name='create_room'),
    path('rooms/join/<int:room_id>/', views.join_room, name='join_room'),
    path('rooms/<int:room_id>/', views.room_view, name='room_view'),
    path('rooms/messages/<int:room_id>/', views.room_messages, name='room_messages'),
]
