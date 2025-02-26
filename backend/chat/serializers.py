from rest_framework import serializers

from api.models import CustomUser
from .models import Room, Message
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'full_name']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer()

    class Meta:
        model = Message
        fields = ['id', 'content', 'sender', 'timestamp', 'unread']

class RoomSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_messages = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['id', 'other_user', 'last_message', 'unread_messages']

    def get_other_user(self, obj):
        current_user = self.context['user']
        print(f'current_user: {current_user}')
        other_user = obj.user_2 if obj.user_1 == current_user else obj.user_1
        return UserSerializer(other_user).data

    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-timestamp').first()
        return MessageSerializer(last_message).data if last_message else None

    def get_unread_messages(self, obj):
        current_user = self.context['user']
        return obj.messages.filter(unread=True).exclude(sender=current_user).exists()