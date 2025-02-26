from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from api.models import CustomUser
from django.db.models import Q, Index

class Room(models.Model):
    user_1 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='rooms_as_user_1')
    user_2 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='rooms_as_user_2')
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_time = models.DateTimeField(null=True)

    class Meta:
        indexes = [
            Index(fields=['user_1']),
            Index(fields=['user_2']),
            Index(fields=['last_message_time']),
        ]
    def __str__(self):
         return f' Room between {self.user_1.full_name} and {self.user_2.full_name}'

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    unread = models.BooleanField(default=True)

    class Meta:
        indexes = [
            Index(fields=['room', 'timestamp']),
            Index(fields=['sender']),
            Index(fields=['unread']),
        ]