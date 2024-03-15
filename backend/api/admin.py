
# Register your models here.
from django.contrib import admin
from .models import  House, Item,User



@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('place_id', 'house_number', "street",'postcode', 'lat', 'lng')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'password')