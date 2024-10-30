import boto3
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

from api.utils import MarketViewItem
from api.storage import S3ItemImagesStorage
from . import models
from .serializers import UserSerializer,ItemSerializer, MarketItemSerializer

from geopy.distance import geodesic  # To calculate distance
CATCHMENT_RADIUS = 100000 # in meters 
class MarketView(views.APIView):
    authentication_classes = [SessionAuthentication,TokenAuthentication] # Will automatically handle the authorisation token checking
    permission_classes = [permissions.IsAuthenticated]
    '''
    must have in Header of request Authorization: Token <token value>
    '''
    def get(self, request):
        user= request.user #if token is valid, it will return the user

        user_house = user.house
        search_query = request.GET.get('search_query')
        category = request.GET.get('category')

        # Get all items. Improvement would be to get the owners that are in the required area then filter the Items by those owners
        all_items = models.Item.objects.all()
        nearby_items = []  # List of nearby items
        s3 = S3ItemImagesStorage()
        # Calculate distance for each item's owner's house
        for item in all_items:
            if item.owner == user:
                continue
            owner_house = item.owner.house
            if owner_house:  # Check if owner has a house
                distance = geodesic((user_house.lat, user_house.lng), (owner_house.lat, owner_house.lng)).m
                if distance <= CATCHMENT_RADIUS:
                    #get thumbnail image from ItemImage table
                    item_image = models.ItemImage.objects.filter(item = item, is_thumbnail = True).first()
                    #create pre signed url
                    pre_signed_url = s3.url(item_image.image.name, expire=3600)
                    print(f'pre signed url: {pre_signed_url}')
                    #formatting of url is shite, temp fix
                    pre_signed_url = pre_signed_url.replace("https://","")
                    market_item = MarketViewItem(id = item.id,distance = distance,title=item.title, owner_name=item.owner.full_name, price_per_day=item.price_per_day, image_url=pre_signed_url)
                    nearby_items.append(market_item)

        # Django Rest Framework can automatically deal with single object inputed and a list of them, we don't need to modify the serializer
        serializer = MarketItemSerializer(nearby_items, many=True)  # Serialize nearby items
        return Response(serializer.data)

class UserView(views.APIView):
    # First app call if a token is present
    authentication_classes = [SessionAuthentication,TokenAuthentication] # Will automatically handle the authorisation token checking
    permission_classes = [permissions.IsAuthenticated]
    '''
    must have in Header of request Authorization: Token <token value>
    '''
    def get(self, request):
        user= request.user #if token is valid, it will return the user

        user_house = user.house 

        # Get all items
        
        serializer = UserSerializer(user,context = {'request': request})  # Serialize nearby items
        response = Response(serializer.data)
        return response

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

class AddItemView(views.APIView):
    authentication_classes = [SessionAuthentication,TokenAuthentication] # Will automatically handle the authorisation token checking
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        try:
            data = JSONParser().parse(request)
            print(f'User: {request.user}')
            serializer = ItemSerializer(data=data)
            serializer.is_valid(raise_exception=True)  # Raise error for invalid data
            print("Add item validated")
            serializer.save(owner = request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except JSONDecodeError:
            print(serializer.errors)
            return Response(serializer.errors,status = status.HTTP_400_BAD_REQUEST)

class TestView(views.APIView):
    def get(self,request):
        # get the first record in ItemImage table
        item_image = models.ItemImage.objects.first()
        s3 = item_image.image.storage
        file_name = item_image.image.name
        print(f's3:{s3}')
        print(f'file name: {file_name}')
        if s3.exists(file_name):
            print(f'Image {file_name} exists in s3')
        else:
            print("image doesn't exist")
                  
        
        
        # try:
        #     s3.connection.meta.client.head_object(Bucket= "mahala-item-images",Key = file_name)
        #     print(f'Image {file_name} exists in s3')
        # except Exception as e:
        #     print(e)
        #     print("Doesn't exist")
        return Response(status = status.HTTP_200_OK)