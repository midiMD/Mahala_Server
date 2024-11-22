# yourapp/management/commands/load_categories.py

from django.core.management.base import BaseCommand
import json
from api.models import Category, CustomUser, Item, ItemImage, item_image_upload_path
from api.storage import S3ItemImagesStorage  
class Command(BaseCommand):
    help = 'delete all images from s3 bucket'
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
        #item_image.save()

        item_image.image.save(upload_path, open(image_path, 'rb'))
        #item_image.save()

        return item_image

    def handle(self, *args, **options):
        
        item = Item.objects.get(id = item_id)
        print(f'Creating ItemImage record for the item {item.title}')
        self._create_item_images(image_path, item, is_thumbnail = True)
        self.stdout.write(self.style.SUCCESS(f'Uploaded thumbnail image : {image_path} for item : {item.title}'))
                
            
        # except FileNotFoundError:
        #     self.stdout.write(self.style.ERROR(data_path+' file not found'))
        # except json.JSONDecodeError:
        #     self.stdout.write(self.style.ERROR('Invalid JSON format in ' + data_path))
        # except Exception as e:
        #     self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))

