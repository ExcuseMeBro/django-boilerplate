from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import DeviceToken, Notification, NotificationSettings, OTPVerification
from messaging.models import Conversation, Message

pytestmark = pytest.mark.django_db
BASE = '/api/v1/'
PHONE = '+998901234567'


def otp(**kwargs):
    return OTPVerification.objects.create(
        phone=PHONE, code='654321', expires_at=timezone.now() + timedelta(minutes=2), **kwargs,
    )


def test_send_otp_normalizes_and_enforces_cooldown_and_daily_limit(api, settings):
    settings.OTP_STATIC_CODE = ''
    settings.DEBUG = True
    settings.SMS_BACKEND = 'console'
    # There is no real SMS/push adapter yet: mock the only delivery hook (logger).
    with patch('core.serializers.logger') as delivery:
        response = api.post(BASE + 'auth/otp/send/', {'phone': '+998 90 1234567'})
        assert response.status_code == 201
        row = OTPVerification.objects.get(phone=PHONE)
        assert len(row.code) == settings.OTP_LENGTH and row.code.isdigit()
        assert row.expires_at > timezone.now() and not row.is_used
        delivery.info.assert_called_once()
    assert api.post(BASE + 'auth/otp/send/', {'phone': PHONE}).status_code == 400
    OTPVerification.objects.update(created_at=timezone.now() - timedelta(minutes=5))
    settings.OTP_MAX_DAILY_PER_PHONE = 1
    assert api.post(BASE + 'auth/otp/send/', {'phone': PHONE}).status_code == 400
    assert OTPVerification.objects.count() == 1


@pytest.mark.parametrize('phone', ['bad', '../etc/passwd', '+123', '1234567890123456', '123456789\nX'])
def test_send_rejects_invalid_phone(api, phone):
    assert api.post(BASE + 'auth/otp/send/', {'phone': phone}).status_code == 400
    assert not OTPVerification.objects.exists()


def test_otp_success_replay_refresh_rotation_logout_and_profile(api):
    row = otp()
    response = api.post(BASE + 'auth/otp/verify/', {'phone': PHONE, 'code': row.code})
    assert response.status_code == 200 and response.data['created'] is True
    row.refresh_from_db()
    assert row.is_used
    assert NotificationSettings.objects.filter(user__phone=PHONE).count() == 1
    api.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['access'])
    profile = api.get(BASE + 'auth/me/')
    assert profile.status_code == 200 and profile.data['phone'] == PHONE
    assert profile.data['is_phone_verified'] is True
    assert api.post(BASE + 'auth/otp/verify/', {'phone': PHONE, 'code': row.code}).status_code == 400
    refresh = api.post(BASE + 'auth/token/refresh/', {'refresh': response.data['refresh']})
    assert refresh.status_code == 200
    assert api.post(BASE + 'auth/token/refresh/', {'refresh': response.data['refresh']}).status_code == 401
    assert api.post(BASE + 'auth/logout/', {'refresh': refresh.data['refresh']}).status_code == 204
    assert api.post(BASE + 'auth/token/refresh/', {'refresh': refresh.data['refresh']}).status_code == 401
    assert api.post(BASE + 'auth/logout/', {'refresh': 'invalid'}).status_code == 400


def test_existing_user_verified_without_duplicate(api, django_user_model):
    user = django_user_model.objects.create_user(username='existing', phone=PHONE)
    row = otp()
    response = api.post(BASE + 'auth/otp/verify/', {'phone': PHONE, 'code': row.code})
    assert response.status_code == 200 and response.data['created'] is False
    user.refresh_from_db()
    assert user.is_phone_verified and django_user_model.objects.count() == 1


@pytest.mark.parametrize('state', ['missing', 'expired', 'used', 'exhausted', 'wrong'])
def test_otp_rejections_do_not_create_user(api, django_user_model, settings, state):
    row = None if state == 'missing' else otp()
    if state == 'expired':
        row.expires_at = timezone.now() - timedelta(seconds=1)
    elif state == 'used':
        row.is_used = True
    elif state == 'exhausted':
        row.attempts = settings.OTP_MAX_VERIFY_ATTEMPTS
    if row:
        row.save()
    response = api.post(BASE + 'auth/otp/verify/', {'phone': PHONE, 'code': '000000' if state == 'wrong' else '654321'})
    assert response.status_code == 400
    assert not django_user_model.objects.exists()
    if row:
        row.refresh_from_db()
        assert row.is_used == (state == 'used')
        if state == 'wrong':
            assert row.attempts == 1


def test_otp_attempt_limit_blocks_correct_code(api, settings):
    settings.OTP_MAX_VERIFY_ATTEMPTS = 2
    row = otp()
    for _ in range(2):
        assert api.post(BASE + 'auth/otp/verify/', {'phone': PHONE, 'code': '000000'}).status_code == 400
    assert api.post(BASE + 'auth/otp/verify/', {'phone': PHONE, 'code': row.code}).status_code == 400
    row.refresh_from_db()
    assert row.attempts == 2 and not row.is_used


@pytest.mark.parametrize('path', ['auth/me/', 'notifications/', 'conversations/', 'messages/'])
def test_private_endpoints_require_auth(api, path):
    assert api.get(BASE + path).status_code == 401
    api.credentials(HTTP_AUTHORIZATION='Bearer invalid')
    assert api.get(BASE + path).status_code == 401


def test_profile_cannot_escalate_or_target_another_user(api, users):
    api.force_authenticate(users[0])
    response = api.patch(BASE + 'auth/me/', {
        'id': str(users[1].pk), 'phone': users[1].phone, 'role': 'admin',
        'balance': '999999', 'is_phone_verified': True, 'first_name': 'Updated',
    })
    assert response.status_code == 200
    users[0].refresh_from_db()
    users[1].refresh_from_db()
    assert users[0].first_name == 'Updated' and users[1].first_name == ''
    assert users[0].role == 'user' and users[0].balance == 0 and not users[0].is_phone_verified
    assert response.data['id'] == str(users[0].pk)
    assert users[0].phone == '+998900000000'


def test_notifications_are_scoped_and_read_is_idempotent(api, users):
    mine = [Notification.objects.create(user=users[0], title=str(i)) for i in range(2)]
    other = Notification.objects.create(user=users[1], title='Private')
    api.force_authenticate(users[0])
    listing = api.get(BASE + 'notifications/')
    assert listing.data['count'] == 2
    assert {row['id'] for row in listing.data['results']} == {str(row.pk) for row in mine}
    assert api.post(BASE + f'notifications/{other.pk}/read/').data == {'updated': 0}
    assert api.post(BASE + f'notifications/{mine[0].pk}/read/').data == {'updated': 1}
    assert api.post(BASE + f'notifications/{mine[0].pk}/read/').data == {'updated': 0}
    assert api.post(BASE + 'notifications/read/').data == {'updated': 1}
    assert api.post(BASE + 'notifications/read/').data == {'updated': 0}
    other.refresh_from_db()
    assert not other.is_read
    assert not Notification.objects.filter(user=users[0], is_read=False).exists()


def test_device_registration_upserts_and_never_accepts_owner_from_client(api, users):
    api.force_authenticate(users[0])
    payload = {'token': 'synthetic-device-token', 'platform': 'ios', 'user': str(users[1].pk)}
    assert api.post(BASE + 'devices/token/', payload).status_code == 201
    assert api.post(BASE + 'devices/token/', payload).status_code == 201
    assert DeviceToken.objects.get().user == users[0]
    api.force_authenticate(users[1])
    assert api.post(BASE + 'devices/token/', payload).status_code == 201
    assert DeviceToken.objects.get().user == users[1]


def test_conversation_creation_includes_caller_and_ignores_spoofed_owner(api, users):
    api.force_authenticate(users[0])
    response = api.post(BASE + 'conversations/', {
        'title': 'New', 'participant_ids': [str(users[1].pk)], 'created_by': str(users[2].pk),
    }, format='json')
    assert response.status_code == 201
    room = Conversation.objects.get()
    assert room.created_by == users[0]
    assert set(room.participants.all()) == set(users[:2])


@pytest.mark.parametrize('method', ['get', 'patch', 'delete'])
def test_outsider_cannot_access_conversation_or_message(api, users, room, method):
    message = Message.objects.create(conversation=room, sender=users[0], text='Private')
    api.force_authenticate(users[2])
    for resource in [f'conversations/{room.pk}/', f'messages/{message.pk}/']:
        assert getattr(api, method)(BASE + resource, {}, format='json').status_code == 404
    assert api.get(BASE + 'conversations/').data['count'] == 0
    assert api.get(BASE + 'messages/').data['count'] == 0
    assert api.post(BASE + 'messages/', {'conversation': str(room.pk), 'text': 'Intrusion'}).status_code == 400
    assert api.post(BASE + f'conversations/{room.pk}/participants/', {'user': str(users[2].pk)}).status_code == 404
    assert Message.objects.get().text == 'Private'


@pytest.mark.parametrize('method', ['patch', 'delete'])
def test_members_cannot_mutate_other_peoples_resources(api, users, room, method):
    message = Message.objects.create(conversation=room, sender=users[0], text='Original')
    api.force_authenticate(users[1])
    assert getattr(api, method)(BASE + f'conversations/{room.pk}/', {'title': 'Changed'}).status_code == 403
    assert getattr(api, method)(BASE + f'messages/{message.pk}/', {'text': 'Changed'}).status_code == 403
    room.refresh_from_db()
    message.refresh_from_db()
    assert room.title == 'Private' and message.text == 'Original'
    assert api.get(BASE + f'conversations/{room.pk}/').status_code == 200
    assert api.get(BASE + f'messages/{message.pk}/').status_code == 200


def test_owner_membership_changes_and_member_leave(api, users, room):
    url = BASE + f'conversations/{room.pk}/participants/'
    api.force_authenticate(users[1])
    assert api.post(url, {'user': str(users[2].pk)}).status_code == 403
    assert api.delete(url + f'{users[0].pk}/').status_code == 403
    api.force_authenticate(users[0])
    assert api.patch(BASE + f'conversations/{room.pk}/', {'participant_ids': []}, format='json').status_code == 400
    assert api.post(url, {'user': str(users[2].pk)}).status_code == 200
    assert room.participants.filter(pk=users[2].pk).exists()
    assert api.delete(url + 'invalid-id/').status_code == 404
    assert api.delete(url + f'{users[0].pk}/').status_code == 403
    assert api.delete(url + f'{users[2].pk}/').status_code == 204
    assert not room.participants.filter(pk=users[2].pk).exists()
    api.force_authenticate(users[1])
    assert api.delete(url + f'{users[1].pk}/').status_code == 204
    assert api.get(BASE + f'conversations/{room.pk}/').status_code == 404


def test_sender_can_edit_delete_but_not_move_message_and_owner_can_delete_room(api, users, room):
    api.force_authenticate(users[0])
    response = api.post(BASE + 'messages/', {
        'conversation': str(room.pk), 'sender': str(users[1].pk), 'is_read': True, 'text': 'Hello',
    })
    assert response.status_code == 201
    message = Message.objects.get()
    assert message.sender == users[0] and not message.is_read
    other_room = Conversation.objects.create(created_by=users[0])
    other_room.participants.add(users[0])
    url = BASE + f'messages/{message.pk}/'
    assert api.patch(url, {'conversation': str(other_room.pk)}).status_code == 400
    assert api.patch(url, {'text': 'Edited'}).status_code == 200
    message.refresh_from_db()
    assert message.text == 'Edited' and message.conversation == room
    assert api.delete(url).status_code == 204
    assert not Message.objects.exists()
    assert api.patch(BASE + f'conversations/{room.pk}/', {'title': 'Renamed'}).status_code == 200
    assert api.delete(BASE + f'conversations/{room.pk}/').status_code == 204
    assert not Conversation.objects.filter(pk=room.pk).exists()


def test_real_jwt_cannot_impersonate_other_user(api, users):
    token = RefreshToken.for_user(users[0])
    api.credentials(HTTP_AUTHORIZATION='Bearer ' + str(token.access_token))
    assert api.get(BASE + 'auth/me/', {'id': str(users[1].pk)}).data['id'] == str(users[0].pk)
