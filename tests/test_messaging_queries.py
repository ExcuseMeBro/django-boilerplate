"""Budgets include pagination COUNT, but exclude JWT's constant user lookup."""
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework_simplejwt.tokens import RefreshToken

from messaging.models import Conversation, Message

pytestmark = pytest.mark.django_db


def seed_rooms(users, count, messages_per_room=2):
    rooms = Conversation.objects.bulk_create([
        Conversation(created_by=users[0], title=f'Room {i}') for i in range(count)
    ])
    Conversation.participants.through.objects.bulk_create([
        Conversation.participants.through(conversation_id=room.pk, user_id=user.pk)
        for room in rooms for user in users[:2]
    ])
    messages = Message.objects.bulk_create([
        Message(conversation=room, sender=users[i % 2], text=f'Message {i}')
        for room in rooms for i in range(messages_per_room)
    ])
    return rooms, messages


@pytest.mark.parametrize('count', [1, 20, 45])
@pytest.mark.parametrize(('resource', 'budget'), [('conversations', 4), ('messages', 2)])
def test_paginated_list_query_budget(api, users, count, resource, budget):
    rooms, messages = seed_rooms(users, count)
    hidden = Conversation.objects.create(created_by=users[2], title='Hidden')
    hidden.participants.add(users[2])
    Message.objects.create(conversation=hidden, sender=users[2], text='Hidden')
    api.force_authenticate(users[0])
    expected = count if resource == 'conversations' else count * 2
    for page in [1, 2] if expected > 20 else [1]:
        with CaptureQueriesContext(connection) as queries:
            response = api.get(f'/api/v1/{resource}/', {'page': page})
        assert response.status_code == 200
        assert response.data['count'] == expected
        assert len(response.data['results']) == min(20, expected - (page - 1) * 20)
        assert len(queries) == budget, [q['sql'] for q in queries]
        assert sum('COUNT(' in q['sql'].upper() for q in queries) == 1
        if resource == 'conversations':
            latest = {str(room.pk): str(messages[i * 2 + 1].pk) for i, room in enumerate(rooms)}
            for result in response.data['results']:
                assert {str(pk) for pk in result['participants']} == {str(user.pk) for user in users[:2]}
                assert result['last_message']['id'] == latest[result['id']]
                assert result['last_message']['sender_phone'] == users[1].phone
        else:
            assert all(row['text'] != 'Hidden' for row in response.data['results'])
            assert {row['sender_phone'] for row in response.data['results']} <= {u.phone for u in users[:2]}


def test_latest_message_none_for_empty_room(api, users, room):
    api.force_authenticate(users[0])
    with CaptureQueriesContext(connection) as queries:
        response = api.get('/api/v1/conversations/')
    assert len(queries) == 4
    assert response.data['results'][0]['last_message'] is None


@pytest.mark.parametrize(('resource', 'budget'), [('conversations', 5), ('messages', 3)])
def test_jwt_adds_one_constant_auth_query(api, users, resource, budget):
    seed_rooms(users, 25)
    token = RefreshToken.for_user(users[0])
    api.credentials(HTTP_AUTHORIZATION='Bearer ' + str(token.access_token))
    with CaptureQueriesContext(connection) as queries:
        response = api.get(f'/api/v1/{resource}/')
    assert response.status_code == 200
    assert len(queries) == budget
