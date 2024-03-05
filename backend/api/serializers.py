from rest_framework import serializers
from .models import Profile, House, Item

class HouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = House
        fields = ('id', 'postcode', 'house_number', 'latitude', 'longitude')

class ProfileSerializer(serializers.ModelSerializer):
    house = HouseSerializer()  # Nested serializer for the House

    class Meta:
        model = Profile
        fields = ('user', 'house')
        read_only_fields = ('user',)


class ItemSerializer(serializers.ModelSerializer):
    owner = ProfileSerializer(read_only=True)  # Read-only for owner field

    class Meta:
        model = Item
        fields = ('id', 'owner', 'price_per_day', 'name', 'category', 'image')