from django.contrib import admin
from .models import  Message,Room

# Register your models here.
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', "sender",'content', 'unread', 'timestamp')

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_1', "user_2")