"""Unfold admin dashboard callback.

Builds the data shown on /admin/ index: KPI cards, a 7-day activity chart,
and recent-activity tables. Falls back to dummy data when the database is
empty so a fresh install still has a populated dashboard.
"""

import json
from datetime import timedelta
from types import SimpleNamespace

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import DeviceToken, Notification, OTPVerification, User


_PURPLE = '#9333ea'
_GREEN = '#22c55e'
_BLUE = '#3b82f6'


def _dummy_recent_users(now):
    return [
        SimpleNamespace(phone='+998901234567', full_name='Ali Valiyev', created_at=now - timedelta(hours=2)),
        SimpleNamespace(phone='+998935550101', full_name='Dilnoza Karimova', created_at=now - timedelta(hours=6)),
        SimpleNamespace(phone='+998901112233', full_name='Jasur Ergashev', created_at=now - timedelta(days=1)),
        SimpleNamespace(phone='+998977778899', full_name='Madina Yusupova', created_at=now - timedelta(days=2)),
        SimpleNamespace(phone='+998935557788', full_name='Sardor Tursunov', created_at=now - timedelta(days=3)),
    ]


def _dummy_recent_notifications(now):
    types = [
        ('system', _('Tizim yangilandi')),
        ('chat', _('Yangi xabar keldi')),
        ('reminder', _('Eslatma: profilingizni to\'ldiring')),
        ('promotion', _('20% chegirma aksiyasi')),
        ('system', _('Parol muvaffaqiyatli o\'zgartirildi')),
    ]
    return [
        SimpleNamespace(
            title=title,
            type=t,
            user=SimpleNamespace(phone='+99890000000' + str(i)),
            created_at=now - timedelta(hours=i * 3),
            is_read=i % 2 == 0,
        )
        for i, (t, title) in enumerate(types, start=1)
    ]


def _seven_day_series(today, queryset_factory):
    return [queryset_factory(today - timedelta(days=i)) for i in range(6, -1, -1)]


def dashboard_callback(request, context):
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)

    total_users = User.objects.count()
    new_users_week = User.objects.filter(date_joined__gte=week_ago).count()
    otp_today = OTPVerification.objects.filter(created_at__date=today).count()
    active_devices = DeviceToken.objects.filter(is_active=True).count()
    unread_notifications = Notification.objects.filter(is_read=False).count()

    # Dummy fallbacks so empty DB still shows a meaningful dashboard.
    if total_users == 0:
        total_users, new_users_week = 1284, 47
    if otp_today == 0:
        otp_today = 312
    if active_devices == 0:
        active_devices = 968
    if unread_notifications == 0:
        unread_notifications = 23

    labels = [(today - timedelta(days=i)).strftime('%d.%m') for i in range(6, -1, -1)]
    signups = _seven_day_series(today, lambda d: User.objects.filter(date_joined__date=d).count())
    otps = _seven_day_series(today, lambda d: OTPVerification.objects.filter(created_at__date=d).count())
    if not any(signups):
        signups = [12, 18, 9, 24, 31, 22, 27]
    if not any(otps):
        otps = [80, 95, 70, 110, 140, 120, 130]

    chart_data = json.dumps({
        'labels': labels,
        'datasets': [
            {'label': str(_('Yangi userlar')), 'data': signups, 'backgroundColor': _PURPLE, 'borderColor': _PURPLE},
            {'label': str(_('OTP so\'rovlar')), 'data': otps, 'backgroundColor': _GREEN, 'borderColor': _GREEN},
        ],
    })

    recent_users = list(User.objects.order_by('-date_joined')[:5]) or _dummy_recent_users(now)
    recent_notifications = (
        list(Notification.objects.select_related('user').order_by('-created_at')[:5])
        or _dummy_recent_notifications(now)
    )

    context.update({
        'kpis': [
            {
                'title': _('Foydalanuvchilar'),
                'value': f'{total_users:,}'.replace(',', ' '),
                'footer': _('+%(n)d oxirgi 7 kunda') % {'n': new_users_week},
                'icon': 'group',
            },
            {
                'title': _('OTP (bugun)'),
                'value': f'{otp_today:,}'.replace(',', ' '),
                'footer': _("Bugungi so'rovlar"),
                'icon': 'pin',
            },
            {
                'title': _('Faol qurilmalar'),
                'value': f'{active_devices:,}'.replace(',', ' '),
                'footer': _('FCM / APNs tokenlar'),
                'icon': 'devices',
            },
            {
                'title': _("O'qilmagan bildirishnomalar"),
                'value': f'{unread_notifications:,}'.replace(',', ' '),
                'footer': _("Yetkazib berilmagan"),
                'icon': 'notifications',
            },
        ],
        'chart_data': chart_data,
        'recent_users': recent_users,
        'recent_notifications': recent_notifications,
    })
    return context
