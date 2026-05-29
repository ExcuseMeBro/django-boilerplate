import logging
import random
import re
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTPVerification, DeviceToken, Notification, NotificationSettings, AppConfig

User = get_user_model()
logger = logging.getLogger(__name__)


class SendOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)

    def validate_phone(self, value):
        value = value.strip().replace(' ', '')
        if not re.fullmatch(r'\+?[0-9]{9,15}', value):
            raise serializers.ValidationError(_("Telefon raqam noto'g'ri."))
        return value

    def validate(self, attrs):
        phone = attrs['phone']
        now = timezone.now()
        cooldown_after = now - timezone.timedelta(seconds=settings.OTP_RESEND_COOLDOWN_SECONDS)
        if OTPVerification.objects.filter(phone=phone, created_at__gte=cooldown_after).exists():
            raise serializers.ValidationError({'phone': _("Yangi OTP kod so'rashdan oldin kuting.")})

        day_start = now - timezone.timedelta(hours=24)
        daily_count = OTPVerification.objects.filter(phone=phone, created_at__gte=day_start).count()
        if daily_count >= settings.OTP_MAX_DAILY_PER_PHONE:
            raise serializers.ValidationError({'phone': _('Kunlik OTP limiti tugagan.')})
        return attrs

    def save(self, **kwargs):
        phone = self.validated_data['phone']
        code = settings.OTP_DEFAULT_CODE if settings.DEBUG else ''.join(
            random.SystemRandom().choice('0123456789') for _ in range(settings.OTP_LENGTH)
        )
        otp = OTPVerification.objects.create(
            phone=phone,
            code=code,
            expires_at=timezone.now() + timezone.timedelta(seconds=settings.OTP_EXPIRY_SECONDS),
        )
        # SMS provider hook. Console mode keeps boilerplate deploy-safe.
        if settings.SMS_BACKEND == 'console':
            logger.info('OTP for %s: %s', phone, code)
        return otp


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=10)

    def validate(self, attrs):
        phone = attrs['phone'].strip().replace(' ', '')
        code = attrs['code'].strip()
        if not re.fullmatch(r'\+?[0-9]{9,15}', phone):
            raise serializers.ValidationError({'phone': _("Telefon raqam noto'g'ri.")})
        otp = OTPVerification.objects.filter(phone=phone, is_used=False).order_by('-created_at').first()
        if not otp:
            raise serializers.ValidationError({'code': _('Faol OTP kod topilmadi.')})
        if otp.is_expired:
            raise serializers.ValidationError({'code': _("OTP kod muddati o'tgan.")})
        if otp.attempts >= settings.OTP_MAX_VERIFY_ATTEMPTS:
            raise serializers.ValidationError({'code': _('Urinishlar soni tugagan.')})
        if otp.code != code:
            otp.attempts += 1
            otp.save(update_fields=['attempts'])
            raise serializers.ValidationError({'code': _("OTP kod noto'g'ri.")})
        attrs['otp'] = otp
        attrs['phone'] = phone
        return attrs

    def save(self, **kwargs):
        otp = self.validated_data['otp']
        phone = self.validated_data['phone']
        otp.is_used = True
        otp.save(update_fields=['is_used'])
        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={'username': phone, 'is_phone_verified': True},
        )
        if not user.is_phone_verified:
            user.is_phone_verified = True
            user.save(update_fields=['is_phone_verified'])
        NotificationSettings.objects.get_or_create(user=user)
        refresh = RefreshToken.for_user(user)
        return {
            'user': user,
            'created': created,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'phone', 'username', 'first_name', 'last_name', 'full_name',
            'avatar', 'language', 'role', 'is_phone_verified', 'date_of_birth',
            'gender', 'balance', 'created_at',
        ]
        read_only_fields = ['id', 'phone', 'role', 'is_phone_verified', 'balance', 'created_at']


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['id', 'token', 'platform', 'device_id', 'device_name', 'app_version', 'is_active', 'created_at']
        read_only_fields = ['id', 'is_active', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'type', 'title', 'body', 'data', 'is_read', 'created_at']
        read_only_fields = ['id', 'type', 'title', 'body', 'data', 'created_at']


class AppConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppConfig
        fields = [
            'app_name', 'support_phone', 'support_email', 'min_supported_version',
            'force_update', 'maintenance_mode', 'about_title', 'about_description',
            'updated_at',
        ]
