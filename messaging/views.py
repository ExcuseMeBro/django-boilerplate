from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer, ParticipantSerializer

User = get_user_model()


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def _assert_owner(self, conversation):
        # Membership is enough to read a conversation, but renaming it, deleting it
        # (which cascades to everyone's messages) or changing who can see it is not
        # something one participant may do to the others.
        if conversation.created_by_id != self.request.user.pk:
            raise PermissionDenied(_('Faqat suhbat yaratuvchisi buni qila oladi.'))

    def perform_update(self, serializer):
        self._assert_owner(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._assert_owner(instance)
        instance.delete()

    @action(detail=True, methods=['post'], url_path='participants')
    def add_participant(self, request, pk=None):
        conversation = self.get_object()
        self._assert_owner(conversation)
        serializer = ParticipantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation.participants.add(serializer.validated_data['user'])
        return Response(self.get_serializer(conversation).data)

    @action(detail=True, methods=['delete'], url_path=r'participants/(?P<user_id>[^/.]+)')
    def remove_participant(self, request, pk=None, user_id=None):
        conversation = self.get_object()
        # Anyone may leave; only the owner may remove somebody else.
        if str(request.user.pk) != str(user_id):
            self._assert_owner(conversation)
        try:
            member = conversation.participants.get(pk=user_id)
        except (User.DoesNotExist, DjangoValidationError, ValueError):
            raise NotFound(_('Ishtirokchi topilmadi.'))
        if member.pk == conversation.created_by_id:
            raise PermissionDenied(_("Suhbat yaratuvchisini olib tashlab bo'lmaydi."))
        conversation.participants.remove(member)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
