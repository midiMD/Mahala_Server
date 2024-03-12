from django.db import models
from django.contrib.auth.models import User,AbstractBaseUser, BaseUserManager


from django.db import models
import requests  # Assuming you'll use 'requests' for API calls

class House(models.Model):
    postcode = models.CharField(max_length=10)
    house_number = models.CharField(max_length=10)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.latitude or not self.longitude:
            self.fetch_coordinates()  # Call the coordinate fetching function
        super().save(*args, **kwargs)

    def fetch_coordinates(self):
        # You'll need to replace "YOUR_API_KEY" with a valid API key
        api_url = f"https://api.example.com/geocode?address={self.postcode},{self.house_number}&key=YOUR_API_KEY"
        response = requests.get(api_url)

        if response.status_code == 200:
            data = response.json()
            # Assuming your response provides 'lat' and 'lng' in the data...
            self.latitude = data.get('lat')
            self.longitude = data.get('lng')
        else:
            # Handle API errors here
            pass

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    house = models.ForeignKey(House, on_delete=models.PROTECT)  # foreign key in House table. on_delete: if there is some other user using that House record, then keep it, otherwise, delete the House record

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Item(models.Model):
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE)
    price_per_day = models.DecimalField(max_digits=6, decimal_places=2)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    image = models.ImageField(upload_to='item_images')


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have a username")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
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

    USERNAME_FIELD = "email"  # Email is the login identifier
    REQUIRED_FIELDS = ["username"]  

    objects = UserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True