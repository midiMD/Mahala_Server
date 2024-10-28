
# Register your models here.
from django.contrib import admin
from .models import  House, Item,CustomUser, ItemImage



@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('place_id', 'house_number', "street",'postcode', 'lat', 'lng')

@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email', 'password',"house")

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'price_per_day', 'title', 'category')

@admin.register(ItemImage)
class ItemImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'is_thumbnail', 'image')