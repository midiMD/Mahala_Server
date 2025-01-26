from django.test import TestCase

from models import CustomUser, House, Category

from django.db.models import Max
print(Category.objects.aggregate(Max('category_id'))['id__max'])