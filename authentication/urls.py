from django.urls import path

from authentication import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('add_2fa/', views.AddTwoFactorView.as_view(), name='add-2fa'),
    path('verify_2fa/', views.VerifyTwoFactorView.as_view(), name='verify-2fa'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('request_password_reset/', views.RequestPasswordResetView.as_view(), name='request-password-reset'),
    path('password_reset/', views.DoPasswordResetView.as_view(), name='do-password-reset'),
    path('verify_email/', views.VerifyEmailView.as_view(), name='verify-email'),
    path('change_password/', views.ChangePasswordView.as_view(), name='change-password'),
]