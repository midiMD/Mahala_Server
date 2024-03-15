from django.db import models
from django.contrib.auth.models import User,AbstractBaseUser, BaseUserManager
from .utils import *

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
        address = f"{self.house_number}, {self.street}, {self.postcode}" 
        api_url = f"{GOOGLE_MAPS_URL}country=gb&address={address}&key={GOOGLE_API_KEY}"
        response = requests.get(api_url)

        if response.status_code == 200:
            data = response.json()
            self.place_id= data.get('results')[0].get('place_id')
            self.lat, self.lng = data.get('results')[0].get('geometry').get('location').get('lat'), data.get('results')[0].get('geometry').get('location').get('lng')
        else:
            print(response.text)
            pass
    

    def __str__(self):
        address_parts = [self.house_number, self.street, self.postcode]
        # Add apartment number if it exists
        if self.apartment_number:
            address_parts.insert(0, f"Apt. {self.apartment_number}") 
        return ", ".join(address_parts)

class Item(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    price_per_day = models.DecimalField(max_digits=6, decimal_places=2)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    image = models.ImageField(upload_to='item_images')
    def __str__(self) -> str:
        return f'Item {self.name}'


class UserManager(BaseUserManager):
    def create_user(self, email, username, password,house):
        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have a username")
        if not password:
            raise ValueError("Users must have a password")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            house= house,
        )
    
        user.set_password(password)  # Hashes the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    username = models.CharField(max_length=30, unique=True)
    date_joined = models.DateTimeField(verbose_name="date joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="last login", auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    house = models.ForeignKey(House, on_delete=models.PROTECT) 
    USERNAME_FIELD = "email"  # Email is the login identifier
    REQUIRED_FIELDS = ["username","email"]  

    objects = UserManager()

    def __str__(self):
        return f'{self.username} || {self.email}'

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True