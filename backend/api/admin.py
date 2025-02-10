
# Register your models here.
from django.contrib import admin
from .models import  Category, House, Item,CustomUser, ItemImage



@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('place_id', 'house_number', "street",'postcode', 'lat', 'lng')

@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email',"house","password","is_verified")
    


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_id', 'name')

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'price_per_day', 'title', 'get_categories')
    def get_categories(self,obj):
        return ", ".join([category.name for category in obj.categories.all()])
    get_categories.short_description = "Categories"
    

@admin.register(ItemImage)
class ItemImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'is_thumbnail', 'image')
