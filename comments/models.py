from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Comment(models.Model):
    sender_name = models.CharField(default='Иванов', max_length=255)  # Имя пользователя из ВК
    content = models.TextField()  # Текст комментария
    answer = models.TextField(default='Ответ')  # Текст ответа
    created_at = models.DateTimeField()  # Дата создания комментария
    status = models.CharField(max_length=50, default='Новое')  # Статус создания комментария
    category = models.CharField(max_length=100, blank=True, null=True)  # Категория
    responsible = models.CharField(max_length=255, blank=True, null=True)  # Ответственный
    deadline = models.DateTimeField(blank=True, null=True)  # Срок исполнения

    def __str__(self):
        return f"{self.sender_name}: {self.content[:20]} - {self.created_at}"

class ErrorLog(models.Model):
    message = models.TextField()  # Описание ошибки
    timestamp = models.DateTimeField(default=timezone.now)  # Время возникновения ошибки
    status = models.CharField(max_length=20, default='Неисправность')  # Статус ошибки
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.timestamp}: {self.message} ({self.status})"
