from rest_framework import serializers
from .models import House, Item, CustomUser
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

    house = HouseSerializer(required=True,many = False)
    class Meta:
        model = CustomUser
        fields = ("id","full_name", "email", "password","house")
        extra_kwargs = {'password': {'write_only': True}}


    def create(self, validated_data):
        house_data = validated_data.pop('house')

        house, _ = House.objects.get_or_create(**house_data)  # Create if needed
        house.save()
        user = CustomUser.objects.create_user(**validated_data, house=house)
        user.save()
        return user


from django.contrib.auth import authenticate


# class LoginSerializer(serializers.Serializer):
#     """
#     This serializer defines two fields for authentication:
#       * username
#       * password.
#     It will try to authenticate the user with when validated.
#     """
#     email = serializers.EmailField()
#     password = serializers.CharField(write_only=True)

#     def validate(self, data):
#         username = data.get('email')
#         password = data.get('password')

#         if username and password:
#             print(username)
#             print(password)
#             print(self.context.get("request"))
#             user = authenticate(request=self.context.get('request'),
#                                 username=username, password=password)
#             if not user:
#                 msg = ('Unable to log in with provided credentials.')
#                 raise serializers.ValidationError(msg, code='authorization')
#         else:
#             msg = ('Must include "username" and "password".')
#             raise serializers.ValidationError(msg, code='authorization')

#         data['user'] = user
#         return data
    

class ItemSerializer(serializers.ModelSerializer):
    owner = UserSerializer(many=False,required =True)  # Read-only for owner field
    
    class Meta:
        model = Item
        fields = ('id', 'owner', 'price_per_day', 'name', 'category', 'image')
    def create(self, validated_data):

        owner_data = validated_data.pop('owner')
        owner, _ = CustomUser.objects.get(owner_data)
        item = Item.objects.create(owner=owner, **validated_data)
        return item


