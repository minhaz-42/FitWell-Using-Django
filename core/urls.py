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
    path('confirm-email/<str:token>/', views.confirm_email, name='confirm_email'),
    path('resend-confirmation/', views.resend_confirmation_email, name='resend_confirmation'),
    
    # Health Assessment Features
    path('health/', views.health_assessment, name='health'),
    path('health/api/', views.health_assessment_api, name='health_api'),
    path('health/history/', views.assessment_history, name='assessment_history'),
    path('health/assessment/<int:assessment_id>/', views.assessment_detail, name='assessment_detail'),
    
    # Chat Features
    path('chat/', views.chat_assistant, name='chat'),
    path('features/', views.features, name='features'),
    path('api/chat/', views.chat_api, name='chat_api'),
     path('api/ocr/', views.ocr_api, name='ocr_api'),
    path('api/conversations/', views.conversation_list_api, name='conversation_list'),
    path('api/conversations/<uuid:conversation_id>/', views.conversation_detail_api, name='conversation_detail'),
     path('api/conversations/<uuid:conversation_id>/rename/', views.rename_conversation_api, name='rename_conversation'),
     path('api/conversations/<uuid:conversation_id>/pin/', views.pin_conversation_api, name='pin_conversation'),
    path('api/conversations/<uuid:conversation_id>/read/', views.mark_conversation_read_api, name='mark_read'),
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
    
    # Favorite Meals APIs
    path('api/favorite-meals/', views.favorite_meals_list_api, name='favorite_meals_list'),
    path('api/favorite-meals/add/', views.favorite_meals_add_api, name='favorite_meals_add'),
    path('api/favorite-meals/<int:favorite_id>/delete/', views.favorite_meals_delete_api, name='favorite_meals_delete'),
    path('api/available-meals/', views.available_meals_api, name='available_meals'),
    
    # Nutrition Articles APIs
    path('api/nutrition-articles/', views.nutrition_articles_list_api, name='nutrition_articles_list'),
    path('api/nutrition-articles/<int:article_id>/', views.nutrition_articles_detail_api, name='nutrition_articles_detail'),
    
    # Progress Tracking APIs
    path('api/progress-tracking/', views.progress_tracking_list_api, name='progress_tracking_list'),
    path('api/progress-tracking/add/', views.progress_tracking_add_api, name='progress_tracking_add'),
    path('api/progress-tracking/<int:entry_id>/delete/', views.progress_tracking_delete_api, name='progress_tracking_delete'),
    
    # PDF Export
    path('export/progress-tracking/pdf/', views.export_progress_tracking_pdf, name='export_progress_tracking_pdf'),
    path('export/health-assessment/pdf/', views.export_health_assessment_pdf, name='export_health_assessment_pdf'),
    
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