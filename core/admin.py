from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import (
    User,
    OTPVerification,
    DeviceToken,
    Notification,
    NotificationSettings,
    AppConfig,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = ['phone', 'full_name_display', 'role', 'language', 'is_phone_verified', 'is_staff', 'is_active', 'created_at']
    list_filter = ['role', 'language', 'is_phone_verified', 'is_staff', 'is_active']
    search_fields = ['phone', 'username', 'first_name', 'last_name', 'email']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    fieldsets = BaseUserAdmin.fieldsets + (
        (_("Qo'shimcha ma'lumotlar"), {
            'fields': ('phone', 'avatar', 'language', 'role', 'is_phone_verified', 'date_of_birth', 'gender', 'balance'),
        }),
    )

    @admin.display(description=_("To'liq ism"))
    def full_name_display(self, obj):
        return obj.full_name


class OTPStatusFilter(admin.SimpleListFilter):
    title = _('Holat')
    parameter_name = 'otp_status'

    def lookups(self, request, model_admin):
        return [
            ('active', _('Faol')),
            ('expired', _("Muddati o'tgan")),
            ('used', _('Ishlatilgan')),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'active':
            return queryset.filter(is_used=False, expires_at__gte=now)
        if self.value() == 'expired':
            return queryset.filter(expires_at__lt=now)
        if self.value() == 'used':
            return queryset.filter(is_used=True)
        return queryset


@admin.register(OTPVerification)
class OTPVerificationAdmin(ModelAdmin):
    list_display = ['phone', 'code', 'status_badge', 'attempts', 'created_at', 'expires_at']
    list_filter = [OTPStatusFilter, 'is_used', 'created_at']
    search_fields = ['phone', 'code']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['phone', 'code', 'attempts', 'created_at', 'expires_at', 'is_used']
    actions = ['delete_expired', 'delete_used']

    def has_add_permission(self, request):
        return False

    @admin.display(description=_('Holat'))
    def status_badge(self, obj):
        if obj.is_used:
            return format_html(
                '<span style="background:#d1fae5;color:#065f46;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:600;">{}</span>',
                _('Ishlatilgan'),
            )
        if obj.is_expired:
            return format_html(
                '<span style="background:#fee2e2;color:#991b1b;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:600;">{}</span>',
                _("Muddati o'tgan"),
            )
        remaining = int((obj.expires_at - timezone.now()).total_seconds())
        minutes, seconds = divmod(max(remaining, 0), 60)
        return format_html(
            '<span style="background:#dbeafe;color:#1e40af;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:600;">{} ({}:{:02d})</span>',
            _('Faol'),
            minutes,
            seconds,
        )

    @admin.action(description=_("Muddati o'tgan OTP kodlarni o'chirish"))
    def delete_expired(self, request, queryset):
        deleted, _ = OTPVerification.objects.filter(expires_at__lt=timezone.now()).delete()
        self.message_user(request, _("%(count)d ta muddati o'tgan OTP kod o'chirildi.") % {'count': deleted})

    @admin.action(description=_("Ishlatilgan OTP kodlarni o'chirish"))
    def delete_used(self, request, queryset):
        deleted, _ = OTPVerification.objects.filter(is_used=True).delete()
        self.message_user(request, _("%(count)d ta ishlatilgan OTP kod o'chirildi.") % {'count': deleted})


@admin.register(DeviceToken)
class DeviceTokenAdmin(ModelAdmin):
    list_display = ['user', 'platform', 'token_short', 'is_active', 'last_used_at', 'created_at']
    list_filter = ['platform', 'is_active', 'created_at']
    search_fields = ['user__phone', 'user__username', 'token', 'device_id', 'device_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'last_used_at']

    @admin.display(description='Token')
    def token_short(self, obj):
        return f'{obj.token[:24]}...' if len(obj.token) > 24 else obj.token


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ['user', 'type_badge', 'title', 'is_read', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['user__phone', 'title', 'body']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    actions = ['mark_as_read']

    COLORS = {
        'system': ('#f3f4f6', '#374151'),
        'chat': ('#dcfce7', '#166534'),
        'reminder': ('#fef9c3', '#854d0e'),
        'promotion': ('#f3e8ff', '#7e22ce'),
    }

    @admin.display(description=_('Tur'))
    def type_badge(self, obj):
        bg, color = self.COLORS.get(obj.type, ('#f3f4f6', '#374151'))
        label = dict(Notification.TYPE_CHOICES).get(obj.type, obj.type)
        return format_html('<span style="background:{};color:{};padding:2px 10px;border-radius:20px;font-size:12px;font-weight:600;">{}</span>', bg, color, label)

    @admin.action(description=_("Tanlangan bildirishnomalarni o'qilgan deb belgilash"))
    def mark_as_read(self, request, queryset):
        updated = queryset.filter(is_read=False).update(is_read=True)
        self.message_user(request, _("%(count)d ta bildirishnoma o'qilgan deb belgilandi.") % {'count': updated})


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(ModelAdmin):
    list_display = ['user', 'push_enabled', 'chat_messages', 'reminders', 'promotions']
    list_filter = ['push_enabled', 'chat_messages', 'reminders', 'promotions']
    search_fields = ['user__phone', 'user__username']


@admin.register(AppConfig)
class AppConfigAdmin(ModelAdmin):
    fieldsets = [
        (_('Ilova'), {'fields': ['app_name', 'min_supported_version', 'force_update', 'maintenance_mode']}),
        (_('Yordam'), {'fields': ['support_phone', 'support_email']}),
        (_('Haqida'), {'fields': ['about_title', 'about_description']}),
        (_('Oxirgi yangilash'), {'fields': ['updated_at']}),
    ]
    readonly_fields = ['updated_at']

    def has_add_permission(self, request):
        return not AppConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
