import pytest
from django.core.cache import cache
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def isolated_cache(settings):
    # No external cache/provider calls; throttles remain enabled and deterministic.
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
    settings.STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    }
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def users(db, django_user_model):
    return [django_user_model.objects.create_user(username=f'user{i}', phone=f'+99890000000{i}') for i in range(3)]


@pytest.fixture
def room(users):
    from messaging.models import Conversation
    conversation = Conversation.objects.create(title='Private', created_by=users[0])
    conversation.participants.set(users[:2])
    return conversation
