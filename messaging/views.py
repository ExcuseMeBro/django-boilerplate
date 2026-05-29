from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).distinct()

    def perform_create(self, serializer):
        conversation = serializer.save()
        conversation.participants.add(self.request.user)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(conversation__participants=self.request.user).select_related('sender', 'conversation')

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    def _assert_sender(self, instance):
        # A participant may read every message in a conversation, but may only
        # mutate the ones they sent.
        if instance.sender_id != self.request.user.pk:
            raise PermissionDenied(_("Faqat o'z xabaringizni o'zgartira olasiz."))

    def perform_update(self, serializer):
        self._assert_sender(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._assert_sender(instance)
        instance.delete()
