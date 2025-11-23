from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Core pages
    path('', views.home, name='home'),
    
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Health Assessment Features
    path('health/', views.health_assessment, name='health'),
    path('health/api/', views.health_assessment_api, name='health_api'),
    path('health/history/', views.assessment_history, name='assessment_history'),
    path('health/assessment/<int:assessment_id>/', views.assessment_detail, name='assessment_detail'),
    
    # Chat Features
    path('chat/', views.chat_assistant, name='chat'),
    path('api/chat/', views.chat_api, name='chat_api'),
     path('api/ocr/', views.ocr_api, name='ocr_api'),
    path('api/conversations/', views.conversation_list_api, name='conversation_list'),
    path('api/conversations/<uuid:conversation_id>/', views.conversation_detail_api, name='conversation_detail'),
     path('api/conversations/<uuid:conversation_id>/rename/', views.rename_conversation_api, name='rename_conversation'),
     path('api/conversations/<uuid:conversation_id>/pin/', views.pin_conversation_api, name='pin_conversation'),
    path('api/conversations/<uuid:conversation_id>/delete/', views.delete_conversation_api, name='delete_conversation'),
    path('api/conversations/clear/', views.clear_conversations_api, name='clear_conversations'),
    
    # Voice Features
    path('api/text_to_speech/', views.text_to_speech_api, name='text_to_speech'),
    path('api/speech_to_text/', views.speech_to_text_api, name='speech_to_text'),
    
    # Profile & Settings
    path('profile/', views.profile_view, name='profile'),
    path('api/profile/', views.profile_api, name='profile_api'),
    path('profile/delete/', views.delete_account, name='delete_account'),
    path('api/set_language/', views.set_language_api, name='set_language'),
    
    # Test/Debug Routes
    path('test/ocr-button/', views.test_ocr_button, name='test_ocr_button'),
    
    # Password Reset (optional)
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='core/password_reset.html'), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='core/password_reset_done.html'), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='core/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='core/password_reset_complete.html'), 
         name='password_reset_complete'),
]