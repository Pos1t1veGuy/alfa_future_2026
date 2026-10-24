from django.db import models

# Create your models here.

import uuid

from django.conf import settings
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.utils import timezone


def generate_application_id():
    """Публичный номер заявки, например CR-A1B2C3D4."""
    return f"CR-{uuid.uuid4().hex[:8].upper()}"


class Company(models.Model):
    """Организация клиента."""

    name = models.CharField(max_length=255, verbose_name="Название компании")
    inn = models.CharField(
        max_length=12,
        blank=True,
        default="",
        db_index=True,
        verbose_name="ИНН",
    )
    phone = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="Телефон",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Credit(models.Model):
    """Кредитный продукт из каталога."""

    id = models.SlugField(
        primary_key=True,
        max_length=50,
        verbose_name="ID продукта",
    )
    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, default="")
    rate = models.CharField(
        max_length=100,
        verbose_name="Процентная ставка",
    )
    max_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Максимальная сумма",
    )
    term = models.CharField(
        max_length=100,
        verbose_name="Описание срока",
    )
    icon = models.CharField(max_length=50, blank=True, default="")
    min_term_months = models.PositiveSmallIntegerField(default=1)
    max_term_months = models.PositiveSmallIntegerField(default=36)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Кредитный продукт"
        verbose_name_plural = "Кредитные продукты"
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(min_term_months__lte=models.F("max_term_months")),
                name="credit_valid_term_range",
            ),
        ]

    def __str__(self):
        return self.name


class Application(models.Model):
    """Заявка клиента на кредит."""

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Отправлена"
        REVIEW = "review", "Рассматривается"
        ADDITIONAL_INFO = "additional_info", "Нужны уточнения"
        APPROVED = "approved", "Одобрена"
        DECLINED = "declined", "Отклонена"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    public_id = models.CharField(
        max_length=11,
        unique=True,
        default=generate_application_id,
        editable=False,
        db_index=True,
    )

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="credit_applications",
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_credit_applications",
    )
    credit = models.ForeignKey(
        Credit,
        on_delete=models.PROTECT,
        related_name="applications",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="applications",
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    term_months = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
    )
    purpose = models.TextField(blank=True, default="")

    # Контактные данные фиксируются на момент подачи заявки.
    # Поэтому последующее изменение профиля не перепишет старую заявку.
    company_name = models.CharField(max_length=255)
    inn = models.CharField(max_length=12, blank=True, default="")
    contact_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32, blank=True, default="")

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
        db_index=True,
    )
    manager_name = models.CharField(max_length=255, blank=True, default="")
    decision_comment = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Кредитная заявка"
        verbose_name_plural = "Кредитные заявки"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["client", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="application_amount_positive",
            ),
        ]

    def __str__(self):
        return self.public_id

    def save(self, *args, **kwargs):
        # Не позволяем сроку выходить за рамки выбранного продукта.
        if self.credit_id:
            if not (
                self.credit.min_term_months
                <= self.term_months
                <= self.credit.max_term_months
            ):
                raise ValueError("Срок не соответствует условиям продукта.")

            if self.amount > self.credit.max_amount:
                raise ValueError("Сумма превышает лимит продукта.")

        super().save(*args, **kwargs)


class ApplicationHistory(models.Model):
    """История изменений заявки."""

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="history_items",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="application_history_actions",
    )

    old_status = models.CharField(max_length=20, blank=True, default="")
    new_status = models.CharField(max_length=20, choices=Application.Status.choices)
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "История заявки"
        verbose_name_plural = "История заявок"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.application.public_id}: {self.new_status}"


class ApplicationDocument(models.Model):
    """Документ, прикреплённый к заявке."""

    class Status(models.TextChoices):
        UPLOADED = "UPLOADED", "Загружен"

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    file = models.FileField(
        upload_to="credit_documents/%Y/%m/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf", "jpg", "jpeg", "png"],
            ),
        ],
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Документ заявки"
        verbose_name_plural = "Документы заявок"
        ordering = ["-created_at"]

    def __str__(self):
        return self.file.name.rsplit("/", 1)[-1] if self.file else "Документ"


class Notification(models.Model):
    """Уведомление пользователя."""

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.recipient_id}: {self.title}"