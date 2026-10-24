import uuid

from django.conf import settings
from django.db import models


#---------------------------------APPLICATION----------------------------------

def generate_public_id():
    return f'CR-{uuid.uuid4().hex[:8].upper()}'


STATUS_CHOICES = [
    ('review', 'На рассмотрении'),
    ('additional_info', 'Требуется уточнение'),
    ('counter_offer', 'Предложены другие условия'),
    ('declined', 'Отказ'),
    ('disbursed', 'Кредит выдан'),
]

RISK_CHOICES = [
    ('low', 'Низкий'),
    ('medium', 'Средний'),
    ('high', 'Высокий'),
]


class Application(models.Model):
    public_id = models.CharField(max_length=11, unique=True, default=generate_public_id, editable=False, verbose_name='Номер заявки')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='review', db_index=True, verbose_name='Статус')

    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='client_applications', verbose_name='Клиент')
    credit = models.ForeignKey('Credit', on_delete=models.PROTECT, related_name='applications', verbose_name='Кредитный продукт')

    company_name = models.CharField(max_length=255, verbose_name='Компания')
    inn = models.CharField(max_length=12, db_index=True, verbose_name='ИНН')
    registration_date = models.DateField(null=True, blank=True, verbose_name='Дата регистрации бизнеса')
    avg_monthly_revenue = models.PositiveBigIntegerField(verbose_name='Средняя выручка в месяц (₽)')
    avg_monthly_expenses = models.PositiveBigIntegerField(verbose_name='Средние расходы в месяц (₽)')
    existing_monthly_debt = models.PositiveBigIntegerField(default=0, verbose_name='Платежи по другим кредитам в месяц (₽)')

    requested_amount = models.PositiveBigIntegerField(verbose_name='Запрошенная сумма (₽)')
    requested_term_months = models.PositiveSmallIntegerField(verbose_name='Запрошенный срок (мес.)')

    score = models.IntegerField(null=True, blank=True, verbose_name='Скоринговый балл')
    risk_level = models.CharField(max_length=10, choices=RISK_CHOICES, blank=True, default='', verbose_name='Уровень риска')
    scoring_factors = models.JSONField(default=list, blank=True, verbose_name='Факторы скоринга')
    debt_load = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Долговая нагрузка (ПДН)')
    safe_limit_min = models.PositiveBigIntegerField(null=True, blank=True, verbose_name='Безопасный лимит от (₽)')
    safe_limit_max = models.PositiveBigIntegerField(null=True, blank=True, verbose_name='Безопасный лимит до (₽)')

    approved_amount = models.PositiveBigIntegerField(null=True, blank=True, verbose_name='Одобренная сумма (₽)')
    approved_term_months = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Одобренный срок (мес.)')
    approved_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Ставка (% годовых)')
    monthly_payment = models.PositiveBigIntegerField(null=True, blank=True, verbose_name='Ежемесячный платёж (₽)')
    decision_reason_code = models.CharField(max_length=50, blank=True, default='', verbose_name='Код причины решения')
    decision_comment = models.TextField(blank=True, default='', verbose_name='Комментарий банка')
    requested_documents = models.JSONField(default=list, blank=True, verbose_name='Запрошенные документы')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Изменена')
    decided_at = models.DateTimeField(null=True, blank=True, verbose_name='Решение принято')

    class Meta:
        verbose_name = 'Кредитная заявка'
        verbose_name_plural = 'Кредитные заявки'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.public_id} ({self.get_status_display()})'

#----------------------------CREDIT--------------------------------

class Credit(models.Model):
    id = models.SlugField(primary_key=True, max_length=50, verbose_name='Код продукта')
    name = models.CharField(max_length=255, verbose_name='Название')
    purpose = models.CharField(max_length=500, blank=True, default='', verbose_name='Цель кредита')
    description = models.TextField(blank=True, default='', verbose_name='Описание')

    min_amount = models.PositiveBigIntegerField(verbose_name='Минимальная сумма (₽)')
    max_amount = models.PositiveBigIntegerField(verbose_name='Максимальная сумма (₽)')
    min_term_months = models.PositiveSmallIntegerField(verbose_name='Минимальный срок (мес.)')
    max_term_months = models.PositiveSmallIntegerField(verbose_name='Максимальный срок (мес.)')
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Базовая ставка (% годовых)')

    min_business_age_months = models.PositiveSmallIntegerField(default=0, verbose_name='Минимальный возраст бизнеса (мес.)')
    min_monthly_revenue = models.PositiveBigIntegerField(default=0, verbose_name='Минимальная выручка в месяц (₽)')

    is_active = models.BooleanField(default=True, verbose_name='Доступен клиентам')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Изменён')

    class Meta:
        verbose_name = 'Кредитный продукт'
        verbose_name_plural = 'Кредитные продукты'
        ordering = ['name']
        constraints = [
            models.CheckConstraint(condition=models.Q(min_amount__lte=models.F('max_amount')), name='credit_amount_range'),
            models.CheckConstraint(condition=models.Q(min_term_months__lte=models.F('max_term_months')), name='credit_term_range'),
        ]

    def __str__(self):
        return self.name


#-----------------------------------------------NOTIFICATION-----------------------------------

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', verbose_name='Получатель')
    application = models.ForeignKey('Application', on_delete=models.CASCADE, related_name='notifications', verbose_name='Заявка', null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='Решение по заявке')
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Текст уведомления')

    is_read = models.BooleanField(default=False, db_index=True, verbose_name='Прочитано')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Когда прочитано')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({"прочитано" if self.is_read else "не прочитано"})'