from django.test import TestCase

from api import models

# Create your tests here.
class S3StorageTestCase(TestCase):
    def setUp(self):
        super().setUp()
                  
    def test_db_congruency(self): #test that the db is consistent with the s3
        item_image = models.ItemImage.objects.first()
        s3 = item_image.image.storage
        file_name = item_image.image.name
        if s3.exists(file_name):
            print(f'Image {file_name} exists in s3')
            return True
        else:
            print("image doesn't exist")
            return False
        
        # try:
        #     s3.connection.meta.client.head_object(Bucket= "mahala-item-images",Key = file_name)
        #     print(f'Image {file_name} exists in s3')
        # except Exception as e:
        #     print(e)
        #     print("Doesn't exist")
