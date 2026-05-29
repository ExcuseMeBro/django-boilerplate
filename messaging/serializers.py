from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_phone = serializers.CharField(source='sender.phone', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_phone', 'text', 'is_read', 'created_at']
        read_only_fields = ['id', 'sender', 'sender_phone', 'is_read', 'created_at']

    def validate_conversation(self, conversation):
        # Block posting into a conversation the caller is not part of (IDOR).
        user = self.context['request'].user
        if not conversation.participants.filter(pk=user.pk).exists():
            raise serializers.ValidationError(_('Siz bu suhbat ishtirokchisi emassiz.'))
        return conversation


class ConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'participants', 'is_active', 'last_message', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        return MessageSerializer(msg).data if msg else None
