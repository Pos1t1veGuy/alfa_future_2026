from django.contrib import admin
from django.urls import path, include

from AUTH.views import MeView

urlpatterns = [
    path("api/admin/", admin.site.urls),
    path("api/v1/auth/", include("AUTH.urls")),
    path("api/v1/me/", MeView.as_view(), name="me-short"),
    path("api/v1/", include("Credits.urls")),
]
