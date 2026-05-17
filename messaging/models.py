from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Conversation(models.Model):
    """Simple room for chat or support conversations."""

    title = models.CharField(max_length=200, blank=True, verbose_name=_('Sarlavha'))
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations', verbose_name=_('Ishtirokchilar'))
    is_active = models.BooleanField(default=True, verbose_name=_('Faol'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Yaratilgan vaqt'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Yangilangan vaqt'))

    class Meta:
        db_table = 'conversations'
        ordering = ['-updated_at']
        verbose_name = _('Suhbat')
        verbose_name_plural = _('Suhbatlar')

    def __str__(self):
        return self.title or f'Suhbat #{self.pk}'


class Message(models.Model):
    """Message stored for HTTP API and WebSocket streams."""

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', verbose_name=_('Suhbat'))
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages', verbose_name=_('Yuboruvchi'))
    text = models.TextField(verbose_name=_('Matn'))
    is_read = models.BooleanField(default=False, verbose_name=_("O'qilgan"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Yaratilgan vaqt'))

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']
        verbose_name = _('Xabar')
        verbose_name_plural = _('Xabarlar')

    def __str__(self):
        return f'{self.sender}: {self.text[:40]}'
