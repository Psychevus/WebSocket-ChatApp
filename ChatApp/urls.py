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
    path('conversations/', views.conversations_list, name='conversations_list'),
    path('search-users/', views.search_users, name='search_users'),
]
