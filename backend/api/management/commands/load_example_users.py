# yourapp/management/commands/load_categories.py

from django.core.management.base import BaseCommand
import json

from django.db import IntegrityError
from api.models import Category,House,CustomUser
users_to_create = [
       {"email": "lady_day@gmail.com", "password": "pass1", "full_name": "lady day"},
       {"email": "john_coltrane@gmail.com", "password": "pass2", "full_name": "john coltrane"},
       {"email": "john.smith@gmail.com", "password": "pass3", "full_name": "john smith"},
       {"email": "flea@gmail.com", "password": "pass4", "full_name": "flea"},
       {"email": "chad@gmail.com", "password": "pass5", "full_name": "chad"}
   ]
class Command(BaseCommand):
    help = 'Loads categories from fixtures/categories.json file'
    def create_example_user(self,email, password, house:House, full_name):
        # CustomUser.objects.create would bypass the model creation function create_user thus the password would be stored in plain text 
        user = CustomUser.objects.create_user(email = email, house = house, full_name = full_name,password = password)
    def handle(self, *args, **options):

        houses = list(House.objects.all())

        which_house = 0
        for user in users_to_create:
            try:
                self.create_example_user(email=user["email"],password=user["password"],house =houses[which_house],full_name=user["full_name"])
                print(f'Created user: {user}')
                which_house = (which_house+1)%len(houses)
            except IntegrityError as e:
                print(e)
        



