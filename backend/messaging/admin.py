from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(ModelAdmin):
    list_display = ['id', 'title', 'participant_count', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'participants__phone', 'participants__username']
    ordering = ['-updated_at']
    filter_horizontal = ['participants']
    date_hierarchy = 'created_at'

    @admin.display(description=_('Ishtirokchilar'))
    def participant_count(self, obj):
        return obj.participants.count()


@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'text_short', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['text', 'sender__phone', 'sender__username']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['conversation', 'sender']

    @admin.display(description=_('Matn'))
    def text_short(self, obj):
        return obj.text[:80]
