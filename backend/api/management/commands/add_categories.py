# yourapp/management/commands/load_categories.py

from django.core.management.base import BaseCommand
import json
from api.models import Category  
#categories.json file location
categories_path = 'fixtures/categories.json'
class Command(BaseCommand):
    help = 'Loads categories from fixtures/categories.json file'

    def handle(self, *args, **options):
        try:
            # Open and read the JSON file
            with open(categories_path, 'r') as file:
                categories = json.load(file)
                
            # Create categories
            for category in categories:
                id,name = category["id"],category["name"]
                Category.objects.get_or_create(
                    category_id=id,
                    defaults={'name': name}
                )
                self.stdout.write(self.style.SUCCESS(f'Created category: {id} - {name}'))
                
            self.stdout.write(self.style.SUCCESS('Successfully loaded categories'))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(categories_path+' file not found'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('Invalid JSON format in ' + categories_path))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))