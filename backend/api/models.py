import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from .utils import *
from django.core.validators import EmailValidator

from django.db import models
import requests  # Assuming you'll use 'requests' for API calls

class House(models.Model):  
    postcode = models.CharField(max_length=10)
    house_number = models.CharField(max_length=10)
    street = models.CharField(max_length=200)
    apartment_number = models.CharField(max_length=10, null=True, blank=True)

    place_id = models.CharField(primary_key=True, max_length=100,unique=True) # Google maps place ID
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.lat or not self.lng:
            self._fetch_coordinates()  # Call the coordinate fetching function
        super().save(*args, **kwargs)

    def _fetch_coordinates(self):
        google_maps_result = fetch_house_info(street=self.street, house_number = self.house_number, postcode = self.postcode, apartment_number=self.apartment_number)
        if "error" not in google_maps_result:
            self.lat , self.lng,self.place_id= google_maps_result["lat"],google_maps_result["lng"],google_maps_result["place_id"] 
        else:
            print(google_maps_result)
    

    def __str__(self):
        address_parts = [self.house_number, self.street, self.postcode]
        # Add apartment number if it exists
        if self.apartment_number:
            address_parts.insert(0, f"Apt. {self.apartment_number}") 
        return ", ".join(address_parts)




class UserManager(BaseUserManager):
    def create_user(self, email, full_name, password,house):

        if not email:
            raise ValueError("Users must have an email address")
        if not full_name:
            raise ValueError("Users must have a full name")
        if not password:
            raise ValueError("Users must have a password")

        user = self.model(
            email=self.normalize_email(email),
            full_name=full_name,
            house= house,
        )
    
        user.set_password(password)  # Hashes the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password):
        
        user = self.model(
            email=self.normalize_email(email),
            full_name=full_name,
            house = House.objects.first()  # get(pk="ChIJ12cums4adkgRjkncD43eWNQ"), #example house, first house
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser):
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    full_name = models.CharField(max_length=60)
    date_joined = models.DateTimeField(verbose_name="date joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="last login", auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False) # whether they have verified their address
    password = models.CharField(max_length=128)
    house = models.ForeignKey(House, on_delete=models.PROTECT)
    USERNAME_FIELD = "email"  # Email is the login identifier
    REQUIRED_FIELDS = ["full_name"]  

    objects = UserManager()

    def __str__(self):
        return f'{self.full_name} || {self.email}'

    def has_perm(self, perm, obj=None):
        return self.is_admin
    
    def has_module_perms(self, app_label):
        return True

    def is_verified(self):
        return self.is_verified

class Category(models.Model):
    category_id = models.IntegerField(unique=True)  # The distinct integer representing the category
    name = models.CharField(max_length=100)  # The name of the category
class Item(models.Model):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    price_per_day = models.DecimalField(max_digits=6, decimal_places=2)
    date_added = models.DateTimeField(verbose_name="date added", auto_now_add=True)
    title = models.CharField(max_length=100,null = False)    
    description = models.TextField(null = True)
    categories = models.ManyToManyField(Category,blank =True)
    def __str__(self) -> str:
        return f'Item {self.title}'
    
def item_image_upload_path(instance, filename):
    # Extract the original file extension
    extension = filename.split('.')[-1]
    # Create a unique filename using UUID   
    new_filename = f"{instance.id}.{extension}"
    # Organize images by item ID
    return f"items/{instance.item.id}/images/{new_filename}"
class ItemImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(Item, related_name='images', on_delete=models.CASCADE, db_index=True)
    is_thumbnail = models.BooleanField(default=False)
    image = models.ImageField(upload_to=item_image_upload_path  )
    display_order = models.IntegerField(default=0)
    #delete from s3 as well when deleting image record from db
    def delete(self, *args, **kwargs):
        # Method 1: Override delete method
        # Delete the file from S3 before deleting the record
        print(f"deleting {self.image.name} from s3")
        if self.image:
            # Get the storage backend
            storage = self.image.storage
            file_name = self.image.name
            try:
                # storage.Object("mahala-item-images", file_name).load()
                storage.delete(file_name)
                print(f'Image {file_name} has been deleted from s3')
            except Exception as e:
                print(e)
        
        # Call the parent class's delete method
        super().delete(*args, **kwargs)
