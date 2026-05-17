"""Core models shared by mobile-first Django projects."""

from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Phone-first user model, compatible with OTP auth."""

    LANGUAGE_CHOICES = [
        ('uz', _("O'zbek")),
        ('en', _('English')),
        ('ru', _('Rus')),
    ]
    GENDER_CHOICES = [
        ('male', _('Erkak')),
        ('female', _('Ayol')),
    ]
    ROLE_CHOICES = [
        ('user', _('Foydalanuvchi')),
        ('staff', _('Xodim')),
        ('admin', _('Admin')),
    ]

    phone = models.CharField(max_length=20, unique=True, verbose_name=_('Telefon'))
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name=_('Avatar'))
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='uz', verbose_name=_('Til'))
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user', verbose_name=_('Rol'))
    is_phone_verified = models.BooleanField(default=False, verbose_name=_('Telefon tasdiqlangan'))
    date_of_birth = models.DateField(null=True, blank=True, verbose_name=_("Tug'ilgan sana"))
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, verbose_name=_('Jinsi'))
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'), verbose_name=_('Balans'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Yaratilgan vaqt'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Yangilangan vaqt'))

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = _('Foydalanuvchi')
        verbose_name_plural = _('Foydalanuvchilar')

    def __str__(self):
        return self.phone or self.username

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.phone or self.username


class OTPVerification(models.Model):
    """One-time password for phone verification."""

    phone = models.CharField(max_length=20, db_index=True, verbose_name=_('Telefon'))
    code = models.CharField(max_length=10, verbose_name=_('Kod'))
    is_used = models.BooleanField(default=False, verbose_name=_('Ishlatilgan'))
    attempts = models.PositiveIntegerField(default=0, verbose_name=_('Urinishlar'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Yaratilgan vaqt'))
    expires_at = models.DateTimeField(verbose_name=_('Tugash vaqti'))

    class Meta:
        db_table = 'otp_verifications'
        ordering = ('-created_at',)
        verbose_name = _('OTP kod')
        verbose_name_plural = _('OTP kodlar')

    def __str__(self):
        return f'{self.phone} - {self.code}'

    @property
    def is_expired(self):
        from django.utils import timezone
        return self.expires_at < timezone.now()

    @property
    def is_active(self):
        return not self.is_used and not self.is_expired


class DeviceToken(models.Model):
    """FCM/APNs token registry."""

    PLATFORM_CHOICES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_tokens', verbose_name=_('Foydalanuvchi'))
    token = models.CharField(max_length=500, unique=True, db_index=True, verbose_name='Token')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='ios', verbose_name=_('Platforma'))
    device_id = models.CharField(max_length=255, blank=True, verbose_name=_('Qurilma ID'))
    device_name = models.CharField(max_length=255, blank=True, verbose_name=_('Qurilma nomi'))
    app_version = models.CharField(max_length=50, blank=True, verbose_name=_('Ilova versiyasi'))
    is_active = models.BooleanField(default=True, verbose_name=_('Faol'))
    last_used_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Oxirgi foydalanish'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Yaratilgan vaqt'))

    class Meta:
        db_table = 'device_tokens'
        verbose_name = _('Qurilma tokeni')
        verbose_name_plural = _('Qurilma tokenlari')

    def __str__(self):
        return f'{self.user} - {self.platform}'


class NotificationSettings(models.Model):
    """Per-user notification preferences."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    push_enabled = models.BooleanField(default=True, verbose_name=_('Push yoqilgan'))
    chat_messages = models.BooleanField(default=True, verbose_name=_('Chat xabarlari'))
    reminders = models.BooleanField(default=True, verbose_name=_('Eslatmalar'))
    promotions = models.BooleanField(default=False, verbose_name=_('Aksiyalar'))

    class Meta:
        db_table = 'notification_settings'
        verbose_name = _('Bildirishnoma sozlamasi')
        verbose_name_plural = _('Bildirishnoma sozlamalari')

    def __str__(self):
        return f'{self.user} settings'


class Notification(models.Model):
    """In-app notification row."""

    TYPE_CHOICES = [
        ('system', _('Tizim')),
        ('chat', _('Chat')),
        ('reminder', _('Eslatma')),
        ('promotion', _('Aksiya')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name=_('Foydalanuvchi'))
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system', verbose_name=_('Tur'))
    title = models.CharField(max_length=200, verbose_name=_('Sarlavha'))
    body = models.TextField(verbose_name=_('Matn'))
    data = models.JSONField(default=dict, blank=True, verbose_name=_("Qo'shimcha ma'lumot"))
    is_read = models.BooleanField(default=False, verbose_name=_("O'qilgan"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Yaratilgan vaqt'))

    class Meta:
        db_table = 'notifications'
        ordering = ('-created_at',)
        verbose_name = _('Bildirishnoma')
        verbose_name_plural = _('Bildirishnomalar')

    def __str__(self):
        return f'{self.user} - {self.title}'


class AppConfig(models.Model):
    """Singleton app settings editable from Unfold admin."""

    app_name = models.CharField(max_length=100, default='Unfold Boilerplate', verbose_name=_('Ilova nomi'))
    support_phone = models.CharField(max_length=30, blank=True, verbose_name=_('Yordam telefoni'))
    support_email = models.EmailField(blank=True, verbose_name=_('Yordam emaili'))
    min_supported_version = models.CharField(max_length=20, blank=True, verbose_name=_('Minimal versiya'))
    force_update = models.BooleanField(default=False, verbose_name=_('Majburiy yangilash'))
    maintenance_mode = models.BooleanField(default=False, verbose_name=_('Texnik tanaffus'))
    about_title = models.CharField(max_length=200, default='Unfold Boilerplate', verbose_name=_('Haqida sarlavha'))
    about_description = models.TextField(blank=True, verbose_name=_('Haqida matni'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Yangilangan vaqt'))

    class Meta:
        db_table = 'app_config'
        verbose_name = _('App Config')
        verbose_name_plural = _('App Config')

    def __str__(self):
        return self.app_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
