from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import Conversation, Message

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    sender_phone = serializers.CharField(source='sender.phone', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_phone', 'text', 'is_read', 'created_at']
        read_only_fields = ['id', 'sender', 'sender_phone', 'is_read', 'created_at']

    def validate_conversation(self, conversation):
        if self.instance is not None and conversation != self.instance.conversation:
            raise serializers.ValidationError(_("Xabarni boshqa suhbatga ko'chirib bo'lmaydi."))
        # Block posting into a conversation the caller is not part of (IDOR).
        user = self.context['request'].user
        if not conversation.participants.filter(pk=user.pk).exists():
            raise serializers.ValidationError(_('Siz bu suhbat ishtirokchisi emassiz.'))
        return conversation


class ParticipantSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())


class ConversationSerializer(serializers.ModelSerializer):
    # Membership is not a plain field: editing it grants or revokes access to the
    # whole message history, so it moves only through the participants actions.
    participants = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    participant_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, required=False, queryset=User.objects.all(),
    )
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'title', 'created_by', 'participants', 'participant_ids',
            'is_active', 'last_message', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'participants', 'created_at', 'updated_at']

    def validate(self, attrs):
        if self.instance is not None and 'participant_ids' in attrs:
            raise serializers.ValidationError({
                'participant_ids': _("Ishtirokchilarni participants endpoint orqali o'zgartiring."),
            })
        return attrs

    def create(self, validated_data):
        members = validated_data.pop('participant_ids', [])
        conversation = Conversation.objects.create(**validated_data)
        conversation.participants.set({*members, conversation.created_by})
        return conversation

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        return MessageSerializer(msg).data if msg else None
