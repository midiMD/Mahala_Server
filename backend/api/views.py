from django.shortcuts import get_object_or_404
from json import JSONDecodeError
from django.http import Http404, JsonResponse
from django.contrib.auth.decorators import login_required
from rest_framework import views, status,permissions
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework.authentication import TokenAuthentication,SessionAuthentication
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import update_last_login
from . import models
from .serializers import UserSerializer,ItemSerializer

from geopy.distance import geodesic  # To calculate distance

class AvailableItemsView(views.APIView):
    authentication_classes = [SessionAuthentication,TokenAuthentication] # Will automatically handle the authorisation token checking
    permission_classes = [permissions.IsAuthenticated]
    '''
    must have in Header of request Authorization: Token <token value>
    '''
    def get(self, request):
        user= request.user #if token is valid, it will return the user

        user_house = user.house

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
    '''
    To DO: Create token upon succesful registration
    '''
    def post(self, request):
        try:
            data = JSONParser().parse(request)
            serializer = UserSerializer(data=data)
            serializer.is_valid(raise_exception=True)  # Raise error for invalid data
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except JSONDecodeError:
            return Response(serializer.errors,status = status.HTTP_400_BAD_REQUEST)


class LoginView(views.APIView):
    # This view should be accessible also for unauthenticated users.
    permission_classes = (permissions.AllowAny,)
    authentication_classes = [TokenAuthentication]
    def post(self, request):
        try:
            data = JSONParser().parse(request)
            user = get_object_or_404(models.CustomUser,email = data['email'])
            print(user)
            if not user.check_password(data['password']):
                return Response({"detail":"Not found."},status = status.HTTP_404_NOT_FOUND)
            token, created = Token.objects.get_or_create(user=user)
            update_last_login(user=user,sender = self)
            serializer = UserSerializer(instance = user)
            return Response({"status": status.HTTP_200_OK, "Token": token.key,"user": serializer.data})
        except JSONDecodeError:
            return Response(serializer.errors,status = status.HTTP_400_BAD_REQUEST)

class LogoutView(views.APIView):
    authentication_classes = [SessionAuthentication,TokenAuthentication] # Will automatically handle the authorisation token checking
    permission_classes = [permissions.IsAuthenticated]
    def get(self,request):
        request.user.auth_token.delete()
        return Response(status = status.HTTP_200_OK)