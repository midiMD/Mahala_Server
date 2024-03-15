from django.shortcuts import get_object_or_404
from json import JSONDecodeError
from django.http import Http404, JsonResponse
from django.contrib.auth.decorators import login_required
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

from . import models
from .serializers import UserSerializer,ItemSerializer


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

class UserRegistrationView(views.APIView):
    def post(self, request):
        try:
            data = JSONParser().parse(request)
            serializer = UserSerializer(data=data)
            serializer.is_valid(raise_exception=True)  # Raise error for invalid data
            
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except JSONDecodeError:
            return JsonResponse({"result": "error","message": "Json decoding error"}, status= 400)

        