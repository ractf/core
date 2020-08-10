from django.urls import path, include
from rest_framework.routers import DefaultRouter

from authentication import views

router = DefaultRouter()
router.register(r'', views.InviteViewSet, basename='invites')

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('add_2fa/', views.AddTwoFactorView.as_view(), name='add-2fa'),
    path('verify_2fa/', views.VerifyTwoFactorView.as_view(), name='verify-2fa'),
    path('remove_2fa/', views.VerifyTwoFactorView.as_view(), name='remove-2fa'),
    path('login_2fa/', views.LoginTwoFactorView.as_view(), name='login-2fa'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('request_password_reset/', views.RequestPasswordResetView.as_view(), name='request-password-reset'),
    path('password_reset/', views.DoPasswordResetView.as_view(), name='do-password-reset'),
    path('verify_email/', views.VerifyEmailView.as_view(), name='verify-email'),
    path('resend_email/', views.ResendEmailView.as_view(), name='resend-email'),
    path('change_password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('generate_invites/', views.GenerateInvitesView.as_view(), name='generate-invites'),
    path('invites/', include(router.urls), name='invites'),
    path('regenerate_backup_codes', views.RegenerateBackupCodesView.as_view(), name='regenerate-backup-codes')
]
