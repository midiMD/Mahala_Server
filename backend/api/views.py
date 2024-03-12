from django.shortcuts import get_object_or_404
from django.http import Http404
from django.contrib.auth.decorators import login_required
from rest_framework import views, status
from rest_framework.response import Response
from . import models
from .serializers import ProfileSerializer,ItemSerializer

class ProfileView(views.APIView):
    def get(self, request, pk, format=None):
        profile = get_object_or_404(models.Profile, pk=pk)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        profile = get_object_or_404(models.Profile, pk=pk)
        serializer = ProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from geopy.distance import geodesic  # To calculate distance

@login_required
class ItemsView(views.APIView):
    def get(self, request):
        # Get user's house from session (replace 'house_id' with your session key)
        user_house_id = request.session.get('house_id')
        user_house = get_object_or_404(models.House, pk=user_house_id)

        # Get all items
        all_items = models.Item.objects.all()
        nearby_items = []

        # Calculate distance for each item's owner's house
        for item in all_items:
            owner_house = item.owner.house
            if owner_house:  # Check if owner has a house
                distance = geodesic(user_house.coordinates, owner_house.coordinates).m
                if distance <= 300:
                    nearby_items.append(item)

        serializer = ItemSerializer(nearby_items, many=True)  # Serialize nearby items
        return Response(serializer.data)
