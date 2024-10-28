from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class S3ItemImagesStorage(S3Boto3Storage):
    def __init__(self, *args, **kwargs):
        if settings.AWS_ACCESS_URL:
            self.secure_urls = False
            self.custom_domain = settings.AWS_ACCESS_URL
            self.use_ssl = False
            self.verify = False
            self.file_overwrite = False

        super(S3ItemImagesStorage, self).__init__(*args, **kwargs)