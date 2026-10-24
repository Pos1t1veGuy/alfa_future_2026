import uuid
from django.conf import settings
from django.db import models

class Profile(models.Model):
    ROLE_CHOICES = [('client', 'Предприниматель'), ('bank_manager', 'Банковский сотрудник'), ('admin', 'Администратор')]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    company_name = models.CharField(max_length=255, blank=True, default='')
    inn = models.CharField(max_length=12, blank=True, default='')
    phone = models.CharField(max_length=32, blank=True, default='')
    def __str__(self): return self.user.email or self.user.username

class Product(models.Model):
    id = models.SlugField(primary_key=True, max_length=50)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    rate = models.CharField(max_length=30, default='от 18,5%')
    max_amount = models.PositiveBigIntegerField(default=5000000)
    term = models.CharField(max_length=60, default='до 24 месяцев')
    icon = models.CharField(max_length=8, default='◈')
    min_term_months = models.PositiveSmallIntegerField(default=3)
    max_term_months = models.PositiveSmallIntegerField(default=24)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name

class LoanApplication(models.Model):
    STATUSES = [('draft','Черновик'),('submitted','Заявка принята'),('review','Рассматривается'),('additional_info','Нужны уточнения'),('approved','Одобрено'),('declined','Не одобрено')]
    id = models.CharField(primary_key=True, max_length=24, default='', editable=False)
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loan_applications')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    amount = models.PositiveBigIntegerField()
    term_months = models.PositiveSmallIntegerField()
    purpose = models.CharField(max_length=500, default='Пополнение оборотных средств')
    company = models.CharField(max_length=255, blank=True)
    inn = models.CharField(max_length=12, blank=True)
    contact_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    status = models.CharField(max_length=24, choices=STATUSES, default='submitted')
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='managed_applications')
    decision_comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f'CR-{uuid.uuid4().hex[:6].upper()}'
        super().save(*args, **kwargs)
    def __str__(self): return self.id

class ApplicationHistory(models.Model):
    application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=24)
    author = models.CharField(max_length=255, blank=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['created_at']

class UploadedDocument(models.Model):
    application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='documents')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_documents')
    file = models.FileField(upload_to='application-documents/%Y/%m/')
    filename = models.CharField(max_length=255)
    size = models.PositiveBigIntegerField(default=0)
    status = models.CharField(max_length=24, default='UPLOADED')
    created_at = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    application = models.ForeignKey(LoanApplication, null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=180)
    body = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
