from dataclasses import asdict
import botocore
from django.db import transaction
from django.conf import settings
from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from json import JSONDecodeError
from django.http import Http404, JsonResponse
from django.contrib.auth.decorators import login_required
from rest_framework import views, status,permissions
from rest_framework.response import Response
from rest_framework.parsers import JSONParser,MultiPartParser,FormParser
from rest_framework.authentication import TokenAuthentication,SessionAuthentication
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import update_last_login
from rest_framework import generics
from api.exceptions import authentication_failed
from rest_framework.renderers import JSONRenderer
from api.utils import InventoryItem, MarketViewItem, generate_random_password
from api.storage import S3ItemImagesStorage
from . import models
from .serializers import InventoryItemSerializer, ItemDeleteSerializer, PasswordChangeSerializer, UploadItemSerializer, UserSerializer,ItemSerializer, MarketItemSerializer
from drf_standardized_errors.handler import exception_handler
from rest_framework.exceptions import PermissionDenied,APIException,ParseError,NotFound
from django.core.mail import send_mail


from geopy.distance import geodesic  # To calculate distance
CATCHMENT_RADIUS = 10000 # in meters 
class MarketView(views.APIView):
    authentication_classes = [SessionAuthentication,TokenAuthentication] # Will automatically handle the authorisation token checking
    permission_classes = [permissions.IsAuthenticated]
    #renderer_classes = [JSONRenderer]
    
    '''
    must have in Header of request Authorization: Token <token value>
    '''
    def get_items(self, user,search_query, category):
        user_house = user.house

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
                    nearby_items.append(asdict(market_item))
        return nearby_items

    def get(self,request):
        user= request.user #if token is valid, it will return the user
        search_query = request.GET.get('search_query')
        category = request.GET.get('category')
        items = self.get_items(user=user, search_query=search_query, category=category)
        serializer = MarketItemSerializer(items,many=True)  # Serialize nearby items
        response = Response(serializer.data)
        return response

class MarketItemDetailView(views.APIView):
    #respond with extra information that was not sent in MarketView
    # currently, that's just the description of the item 
    authentication_classes = [SessionAuthentication,TokenAuthentication] # Will automatically handle the authorisation token checking
    permission_classes = [permissions.IsAuthenticated]
    def get(self,request):
        user = request.user
        user_house = user.house
        # data = JSONParser().parse(request)
        # item_id = data["id"]
        
        item_id = request.GET.get("id")
        item = models.Item.objects.get(pk = item_id)
        #validate the item id to check whether the request is legitimate and isn't trying to access items outside its catchment area
        item_owner_house = item.owner.house
        if item_owner_house:  # Check if owner has a house
            distance = geodesic((user_house.lat, user_house.lng), (item_owner_house.lat, item_owner_house.lng)).m
            if distance > CATCHMENT_RADIUS:
                raise PermissionDenied(detail= "Forbidden Access.", code = "forbidden")
        return Response({"id":item_id,
            "description":item.description})

    

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
        
        serializer = UserSerializer(user,context = {'request': request})  
        response = Response(serializer.data)
        return response

class UserRegistrationView(views.APIView):
    '''
    
    '''
    def post(self, request):
        try:
            data = JSONParser().parse(request)
            serializer = UserSerializer(data=data)
            serializer.is_valid(raise_exception=True)  # Raise error for invalid data
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)

            # return Response(serializer.data, status=status.HTTP_201_CREATED)
        except JSONDecodeError:
            return Response(serializer.errors,status = status.HTTP_400_BAD_REQUEST)

class ValidateTokenView(views.APIView):
    authentication_classes = [SessionAuthentication,TokenAuthentication] # Will automatically handle the authorisation token checking
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user  # DRF automatically sets this if the token is valid    
        if not user:
            raise authentication_failed
        return Response({"is_address_verified":user.house_is_verified},status=status.HTTP_202_ACCEPTED)
class GetUserView(views.APIView):
    authentication_classes = [SessionAuthentication,TokenAuthentication] # Will automatically handle the authorisation token checking
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user  # DRF automatically sets this if the token is valid    
        if not user:
            raise authentication_failed
        return Response({"user":user},status=status.HTTP_202_ACCEPTED)

class LoginView(views.APIView):
    # This view should be accessible also for unauthenticated users.
    permission_classes = (permissions.AllowAny,)
    authentication_classes = [TokenAuthentication]
    def post(self, request):
        try:
            data = JSONParser().parse(request)
            user = models.CustomUser.objects.filter(email=data['email']).first()
            
            # user = get_object_or_404(models.CustomUser,email = data['email'])
            if not user:
                raise authentication_failed
            print(user)
            if not user.check_password(data['password']):
                raise authentication_failed
            token, created = Token.objects.get_or_create(user=user)
            update_last_login(user=user,sender = self)
            serializer = UserSerializer(instance = user)
            #return Response({"Token": token.key,"user": serializer.data})
            return Response({"Token":token.key,"is_address_verified":user.house_is_verified})
        except JSONDecodeError:
            return Response(serializer.errors,status = status.HTTP_400_BAD_REQUEST)

class LogoutView(views.APIView):
    authentication_classes = [SessionAuthentication,TokenAuthentication] # Will automatically handle the authorisation token checking
    permission_classes = [permissions.IsAuthenticated]
    def get(self,request):
        request.user.auth_token.delete()
        return Response(status = status.HTTP_200_OK)
class UploadItemView(views.APIView):
    authentication_classes = [SessionAuthentication,TokenAuthentication] # Will automatically handle the authorisation token checking
    permission_classes = [permissions.IsAuthenticated]#
    parser_classes = (MultiPartParser, FormParser)  # Handle multipart/form-data
    def post(self, request):

        try:
            with transaction.atomic(): #reverts if any exception
                user = request.user
                data = request.data
                #data["owner"] = user
                #First we create Item record then we create ItemImage record 
                serializer = UploadItemSerializer(data = data)
                serializer.is_valid(raise_exception=True)  # Raise error for invalid data
                #print(serializer.validated_data)
                #data = serializer.validated_data
                #print(data)
                objects_created = serializer.save(owner = user)
                # print(objects_created)
                #print(objects_created)
                return Response(status=status.HTTP_201_CREATED)
        except JSONDecodeError as e:
            print(e)
            raise ValidationError(message=e)

        except botocore.exceptions.EndpointConnectionError as e:
            print(f"S3 server error: {e}")
            # don;t acc need to implement roll back on the upload to server because the uploading is the last part and only starts if
            # everything else is valid
            raise APIException(detail = "Image server connection",code = "image_server")

class InventoryView(views.APIView):
    authentication_classes = [SessionAuthentication,TokenAuthentication] # Will automatically handle the authorisation token checking
    permission_classes = [permissions.IsAuthenticated]
    #renderer_classes = [JSONRenderer]
    
    '''
    must have in Header of request Authorization: Token <token value>
    '''
    def get_user_items(self,user):
        items = models.Item.objects.filter(owner=user).order_by('-date_added')
        result = []
        s3 = S3ItemImagesStorage()

        for item in items:
            
            #get thumbnail image from ItemImage table
            item_image = models.ItemImage.objects.filter(item = item, is_thumbnail = True).first()
            #create pre signed url
            pre_signed_url = s3.url(item_image.image.name, expire=3600)
            print(f'pre signed url: {pre_signed_url}')
            #formatting of url is shite, temp fix
            pre_signed_url = pre_signed_url.replace("https://","")
            inventory_item = InventoryItem(id =item.id, title = item.title, price_per_day = item.price_per_day, thumbnail_url = pre_signed_url)
            result.append(asdict(inventory_item))
        return result
    def get(self,request):
        user= request.user #if token is valid, we get the user
        items = self.get_user_items(user=user)
        serializer = InventoryItemSerializer(items,many=True)  # Serialize nearby items
        response = Response(serializer.data)
        return response

class InventoryItemDetailView(views.APIView):
    authentication_classes = [SessionAuthentication,TokenAuthentication] # Will automatically handle the authorisation token checking
    permission_classes = [permissions.IsAuthenticated]
    def get(self,request):
        user = request.user        
        item_id = request.GET.get("id") # uri encoded param for GET requests
        item = models.Item.objects.get(pk = item_id)
        if item.owner != user:
            raise PermissionDenied(detail= "Forbidden Access.", code = "forbidden")

        return Response({"date_added" : item.date_added,
            "description":item.description})
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
    
class PasswordResetView(views.APIView):
    def post(self, request):
        
        data = JSONParser().parse(request)
        email  = data.get("email")
        if not email:
            return Response(
                {'error': 'Email is required'}, 
                status=status.HTTP_400_BAD_REQUEST)
        try:
            user = models.CustomUser.objects.get(email = email)
    
        except models.CustomUser.DoesNotExist:
            print(f"User with email : {email} doesn't exist")
            return Response(
                {'message': 'If the email exists, you will receive a password reset email.'}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(f"PasswordResetView Exception: {e}")
            return Response(
                {'error': 'Failed to send email'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        new_password = generate_random_password(length = 4)
        old_password = user.password
        try:
            send_mail(
                subject='Password Reset',
                message=f'Your new password is: {new_password}\n\nPlease change this password after logging in.',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            user.set_password(new_password)
            user.save()
            return Response(
                {'message': 'If the email exists, you will receive a password reset email.'}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(f"PasswordResetView Exception: {e}")
            print("Resetting to old password")
            user.set_password(old_password)
            user.save()
            return Response(
                {'error': 'Failed to send email'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class PasswordChangeView(views.APIView):
    authentication_classes = [SessionAuthentication,TokenAuthentication] # Will automatically handle the authorisation token checking
    permission_classes = [permissions.IsAuthenticated]
    def put(self, request):
        user = request.user
        if not user:
            raise authentication_failed
        serializer = PasswordChangeSerializer(data=request.GET, context={'user': user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        print(f"Success changed password for user: {user}")
        return Response(status = status.HTTP_200_OK)
class ItemDeleteView(views.APIView):
    authentication_classes = [SessionAuthentication,TokenAuthentication] # Will automatically handle the authorisation token checking
    permission_classes = [permissions.IsAuthenticated]
    def delete(self, request, *args, **kwargs):
        user = request.user
        if not user:
            raise authentication_failed
        serializer = ItemDeleteSerializer(data=request.GET) #url encoded params
        serializer.is_valid(raise_exception=True)
        
        item_id = serializer.validated_data['id']
        try:
            item = models.Item.objects.get(pk=item_id)
            # Delete all associated ItemImage objects
            item_images = models.ItemImage.objects.filter(item=item)
            for item_image in item_images:
                item_image.delete()  # This will also delete the image from the storage backend
            # Finally, delete the Item object
            item.delete()
            return Response( status=status.HTTP_204_NO_CONTENT)
        except models.Item.DoesNotExist:
            raise NotFound(detail="Item not found")
        except botocore.exceptions.EndpointConnectionError as e:
            print(f"S3 server error: {e}")
            raise APIException(detail = "Image server connection",code = "image_server")
        except Exception as e:
            raise APIException(detail = e)


        
# class EmailChangeView(views.APIView):
#     authentication_classes = [SessionAuthentication,TokenAuthentication] # Will automatically handle the authorisation token checking
#     permission_classes = [permissions.IsAuthenticated]
#     def post(self,request):
#         data = JSONParser().parse(request)
#         user = request.user
#         old_email = data.get("old_email")
#         new_email = data.get("old_email")
#         password= data.get("password")

