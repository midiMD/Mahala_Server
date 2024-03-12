from rest_framework import serializers
from .models import Profile, House, Item,User
from rest_framework.fields import EmailField,CharField

class HouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = House
        fields = ('id', 'postcode', 'house_number', 'latitude', 'longitude')


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = Emai
    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
    
class ProfileSerializer(serializers.ModelSerializer):
    house = HouseSerializer()  # Nested serializer for the House
    user  = UserSerializer()
    class Meta:
        model = Profile
        fields = ('user', 'house')
        read_only_fields = ('user',)


class ItemSerializer(serializers.ModelSerializer):
    owner = ProfileSerializer(read_only=True)  # Read-only for owner field

    class Meta:
        model = Item
        fields = ('id', 'owner', 'price_per_day', 'name', 'category', 'image')

