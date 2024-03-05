from django.db import models
from django.contrib.auth.models import User
from .models import House  # Import the House model


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