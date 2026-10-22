from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, RegisterView, MeView, ProductsView, ApplicationsView, ApplicationDetailView, NotificationsView, NotificationReadView, SafeLimitView, DocumentOCRView, DocumentUploadView, logout_view

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='api-login'),
    path('auth/register/', RegisterView.as_view(), name='api-register'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='api-refresh'),
    path('auth/logout/', logout_view, name='api-logout'),
    path('me/', MeView.as_view(), name='api-me'),
    path('products/', ProductsView.as_view(), name='api-products'),
    path('applications/', ApplicationsView.as_view(), name='api-applications'),
    path('applications/<str:pk>/', ApplicationDetailView.as_view(), name='api-application-detail'),
    path('bank/applications/', ApplicationsView.as_view(), name='api-bank-applications'),
    path('notifications/', NotificationsView.as_view(), name='api-notifications'),
    path('notifications/read-all/', NotificationsView.as_view(), name='api-notifications-read-all'),
    path('notifications/<int:pk>/read/', NotificationReadView.as_view(), name='api-notification-read'),
    path('safe-limit/calculate/', SafeLimitView.as_view(), name='api-safe-limit'),
    path('documents/', DocumentUploadView.as_view(), name='api-document-upload'),
    path('documents/<int:pk>/ocr/', DocumentOCRView.as_view(), name='api-document-ocr'),
]
