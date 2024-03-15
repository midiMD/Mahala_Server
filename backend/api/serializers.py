from rest_framework import serializers
from .models import House, Item,User
from rest_framework.fields import EmailField,CharField
from .utils import *

class HouseSerializer(serializers.ModelSerializer):
    postcode = CharField(max_length=10)
    house_number = CharField(max_length=10)
    street = CharField(max_length=200)
    apartment_number = CharField(max_length=10,allow_blank=True)
    class Meta:
        model = House
        fields = ('postcode', 'house_number', "street","apartment_number")
    def create(self,validated_data):
        google_fetched_data= fetch_house_info(**validated_data)
        house = House.objects.create(**validated_data,**google_fetched_data)
        house.save()
        return house


class UserSerializer(serializers.ModelSerializer):
    password = CharField(write_only=True,required =True)
    email = EmailField(required=True)
    username = CharField(required=True)
    house = HouseSerializer(required=True,many = False)
    class Meta:
        model = User
        fields = ("username", "email", "password","house")

    def create(self, validated_data):
        house_data = validated_data.pop('house')

        house, _ = House.objects.get_or_create(**house_data)  # Create if needed
        house.save()
        user = User.objects.create_user(**validated_data, house=house)
        user.save()
        return user
    

class ItemSerializer(serializers.ModelSerializer):
    owner = UserSerializer(many=False,required =True)  # Read-only for owner field
    
    class Meta:
        model = Item
        fields = ('id', 'owner', 'price_per_day', 'name', 'category', 'image')
    def create(self, validated_data):

        owner_data = validated_data.pop('owner')
        owner, _ = User.objects.get(owner_data)
        item = Item.objects.create(owner=owner, **validated_data)
        return item


