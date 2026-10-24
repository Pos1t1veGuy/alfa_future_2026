from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.http import FileResponse, Http404
from django.urls import path, reverse
from django.utils.html import format_html

from .models import ApplicationHistory, LoanApplication, Notification, Product, Profile, UploadedDocument


admin.site.site_header = 'Альфа-Бизнес · администрирование'
admin.site.site_title = 'Альфа-Бизнес'
admin.site.index_title = 'Управление кредитным кабинетом'


class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 0
    max_num = 1
    fields = ('role', 'company_name', 'inn', 'phone')


User = get_user_model()


class AlfaUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    list_select_related = ('profile',)
    list_filter = ('is_staff', 'is_active', 'profile__role')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'profile__company_name', 'profile__inn')

    @admin.display(description='Роль', ordering='profile__role')
    def role(self, obj):
        return getattr(getattr(obj, 'profile', None), 'get_role_display', lambda: '—')()


admin.site.unregister(User)
admin.site.register(User, AlfaUserAdmin)


class ApplicationHistoryInline(admin.TabularInline):
    model = ApplicationHistory
    extra = 0
    can_delete = False
    fields = ('status', 'author', 'comment', 'created_at')
    readonly_fields = fields
    ordering = ('created_at',)


class UploadedDocumentInline(admin.TabularInline):
    model = UploadedDocument
    extra = 0
    can_delete = False
    fields = ('filename', 'size', 'status', 'user', 'created_at', 'preview_link')
    readonly_fields = fields

    @admin.display(description='Файл')
    def preview_link(self, obj):
        if not obj or not obj.pk:
            return '—'
        url = reverse('admin:core_uploadeddocument_preview', args=(obj.pk,))
        return format_html('<a href="{}" target="_blank" rel="noopener">Открыть</a>', url)


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'client', 'product', 'amount', 'term_months', 'status', 'manager', 'updated_at')
    list_filter = ('status', 'product', 'created_at', 'updated_at')
    search_fields = ('id', 'company', 'inn', 'client__username', 'client__email', 'contact_name', 'manager__username')
    autocomplete_fields = ('client', 'product', 'manager')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    list_select_related = ('client', 'product', 'manager')
    inlines = (UploadedDocumentInline, ApplicationHistoryInline)
    fieldsets = (
        ('Заявка', {'fields': ('id', 'status', 'product', 'amount', 'term_months', 'purpose')}),
        ('Клиент', {'fields': ('client', 'company', 'inn', 'contact_name', 'phone')}),
        ('Решение банка', {'fields': ('manager', 'decision_comment')}),
        ('Служебные данные', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'application', 'user', 'size', 'status', 'created_at', 'preview_link')
    list_filter = ('status', 'created_at')
    search_fields = ('filename', 'application__id', 'application__company', 'user__username', 'user__email')
    readonly_fields = ('application', 'user', 'file', 'filename', 'size', 'status', 'created_at', 'preview_link')
    list_select_related = ('application', 'user')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/preview/', self.admin_site.admin_view(self.preview), name='core_uploadeddocument_preview'),
        ]
        return custom_urls + urls

    def preview(self, request, pk):
        document = self.get_object(request, str(pk))
        if not document or not document.file:
            raise Http404('Документ не найден.')
        try:
            document.file.open('rb')
        except FileNotFoundError as exc:
            raise Http404('Файл не найден в хранилище.') from exc
        return FileResponse(document.file, as_attachment=False, filename=document.filename)

    @admin.display(description='Файл')
    def preview_link(self, obj):
        if not obj or not obj.pk:
            return '—'
        url = reverse('admin:core_uploadeddocument_preview', args=(obj.pk,))
        return format_html('<a href="{}" target="_blank" rel="noopener">Открыть</a>', url)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'rate', 'max_amount', 'min_term_months', 'max_term_months', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('id', 'name')
    list_filter = ('is_active',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'application', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('title', 'body', 'user__username', 'application__id')
    list_select_related = ('user', 'application')
    readonly_fields = ('created_at',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'company_name', 'inn', 'phone')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'company_name', 'inn')
    list_select_related = ('user',)
