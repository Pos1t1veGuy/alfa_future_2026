from django.conf import settings
from django.db import models


class Profile(models.Model):
    ROLE_CHOICES = [
        ("client", "Предприниматель"),
        ("bank_manager", "Сотрудник банка"),
        ("admin", "Администратор"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="client")
    company_name = models.CharField(max_length=255, blank=True, default="")
    inn = models.CharField(max_length=12, blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")

    def __str__(self):
        return f"{self.user.email or self.user.username} ({self.role})"