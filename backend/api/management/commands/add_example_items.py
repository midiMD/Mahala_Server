# yourapp/management/commands/load_categories.py

from django.core.management.base import BaseCommand
import json
from api.models import Category, CustomUser, Item, ItemImage, item_image_upload_path
from api.storage import S3ItemImagesStorage  
#categories.json file location
data_path = "fixtures/items.json"
DEBUG = True
class Command(BaseCommand):
    help = 'Loads example items and their images (Minio S3). Make sure there exist Users'
    def _create_item_images(self,image_path, item_object, is_thumbnail = False):
        
        # Initialize storage
        storage = S3ItemImagesStorage()
        #print(storage.connection.meta.client.head_object(Bucket= "mahala-item-images",Key = image_path))
        # Open the image file
        item_image = ItemImage.objects.create(
            item=item_object,
            is_thumbnail=is_thumbnail,
            image="temp.jpg"
        )
        upload_path = item_image_upload_path(item_image, image_path)
        item_image.image = upload_path

        item_image.image.save(upload_path, open(image_path, 'rb'))

        return item_image

    def handle(self, *args, **options):

        
        with open(data_path, 'r') as file:
            items = json.load(file)
        users= list(CustomUser.objects.all())
        which_user = 0
        for item in items:
            owner = users[which_user]
            print(f'item: {item}')
            item_record = Item.objects.create(
                owner=owner,
                price_per_day=item['price_per_day'],
                title=item['title'],
                description=item['description']
            )
            for category_id in item['categories']:
                category = Category.objects.get(category_id=category_id)
                item_record.categories.add(category)
            self.stdout.write(self.style.SUCCESS(f'Created Item: {item["title"]} of owner: {owner}'))
            which_user = (which_user+1)%len(users)
            print(f'Creating ItemImage record for the item {item["title"]} and uploading')
            self._create_item_images(item['thumbnail_path'], item_record, is_thumbnail = True)
            self.stdout.write(self.style.SUCCESS(f'Uploaded thumbnail image : {item["thumbnail_path"]} for item : {item_record.title}'))
            
        self.stdout.write(self.style.SUCCESS('Successfully loaded items'))
