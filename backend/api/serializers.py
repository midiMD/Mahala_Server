import botocore
from django.forms import ValidationError
from rest_framework import serializers
from .models import Category, House, Item, CustomUser, ItemImage
from rest_framework.fields import EmailField,CharField
from .utils import *
from django.db.models import Max
from .models import item_image_upload_path

'''
Serializer : Python Object -> JSON

'''
class HouseSerializer(serializers.ModelSerializer):
    postcode = CharField(max_length=10)
    house_number = CharField(max_length=10)
    street = CharField(max_length=200)
    apartment_number = CharField(max_length=10,allow_blank=True)
    class Meta:
        model = House
        fields = ('postcode', 'house_number', "street","apartment_number")
    def validate(self, attrs):
        attrs = super().validate(attrs)
        '''
        TODO :
        More complex House validation logic
        '''
        google_fetched_data = fetch_house_info(street=attrs["street"],postcode=attrs["postcode"],house_number=attrs["house_number"],apartment_number=attrs["apartment_number"])
        try:
            existing_house = House.objects.get(place_id = google_fetched_data["place_id"]) 
            attrs["existing_house"] = existing_house
        except Exception:
            pass
        
        return attrs
    def create(self,validated_data):
        google_fetched_data= fetch_house_info(street = validated_data["street"],postcode = validated_data["postcode"],house_number = validated_data["house_number"],apartment_number = validated_data["apartment_number"])
        house = House.objects.create(**validated_data,**google_fetched_data)
        house.save()
        return house


class UserSerializer(serializers.ModelSerializer):

    house = HouseSerializer(required=True,many = False)
    class Meta:
        model = CustomUser
        fields = ("id","full_name", "email", "password","house")
        extra_kwargs = {'password': {'write_only': True}}
    

    def create(self, validated_data):
        print("Creating user : " , validated_data)
        house_data = validated_data.pop('house')
        print("House data: ", house_data)
        if "existing_house" in house_data:
            house = house_data.pop("existing_house")
        else:
            house = House.objects.create(**house_data)
            house.save()
    
        user = CustomUser.objects.create_user(**validated_data, house=house)
        user.save()
        return user


from django.contrib.auth import authenticate


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['category_id']

class ItemSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    categories= serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    class Meta:
        model = Item
        fields = ['id', 'owner', 'price_per_day', 'title',"description",'categories',"date_added"]
        read_only_fields = ["owner"]
    def validate_categories(self,value):

        # get the upper bound of category_id in the Category table to see which of the integers in the request are not in bounds and thus
        # don't correspond to any category            
        max_category_id = Category.objects.aggregate(Max('category_id'))['category_id__max']
        invalid_category_ids = [x for x in value if (x<1 or x>max_category_id)]
        if len(invalid_category_ids)>0:
            print(ValidationError(f"category integers provided don't all match up with available categories: {invalid_category_ids}"))
    def create(self, validated_data):
        # owner_data = validated_data.pop('owner')
        # owner, _ = CustomUser.objects.get(owner_data)
        categories = validated_data.pop('categories', [])

        item = Item.objects.create(**validated_data)
        categories = Category.objects.filter(category_id__in=categories)
        item.categories.set(categories)
        return item

class UploadItemSerializer(serializers.ModelSerializer):
    # Field definitions. tell django what field types to expect
    price_per_day = serializers.DecimalField(max_digits=10, decimal_places=2)
    owner = serializers.ReadOnlyField(source='owner.username')
    image = serializers.ImageField(required = True)
    categories = serializers.CharField()
    class Meta:
        model = Item
        fields = ['title', 'categories', 'description', 'price_per_day',"owner","image"]
        read_only_fields = ["owner"]

    def validate_categories(self, value):
        categories = value.split(',')
        try:
            # Convert each category to an integer after stripping whitespace
            categories = [int(category.strip()) for category in categories]
        except Exception as e:
            print(e)
            raise serializers.ValidationError(
                "Categories must be a comma-separated string of integers."
            )
        return categories
    def validate_price_per_day(self,value):
        try:
            return float(value)
        except Exception as e:
            raise serializers.ValidationError("Price must be a number")
    def validate(self,data):
        item_serializer = ItemSerializer(data = data) # can pass everything, it will select what it needs out of it
        item_serializer.is_valid(raise_exception=True)
        return data
    def create(self,validated_data):
        # print(validated_data)
        image = validated_data.pop("image")
        categories = validated_data.pop('categories', [])

        item = Item.objects.create(**validated_data)
        categories = Category.objects.filter(category_id__in=categories)
        item.categories.set(categories)
        item.save()
        print(f"Created Item: {item.title}")
        item_image = ItemImage.objects.create(
                item=item,
                is_thumbnail=True,  
                image="temp.jpg"
            )
        upload_path = item_image_upload_path(item_image, image.name)
        item_image.image = upload_path
        item_image.image.save(upload_path,image)
        print(f"Succesfully uploaded to S3: {item_image.image.name}")
        return {"item":item,"item_image":item_image}

class MarketItemSerializer(serializers.Serializer):
    # Django Rest Framework can automatically deal with single object inputed and a list of them, we don't need to modify the serializer
    owner_name = serializers.CharField(read_only=True)
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    price_per_day = serializers.FloatField(read_only=True)
    image_url = serializers.CharField(read_only=True)   
    distance = serializers.FloatField(read_only=True)

class InventoryItemSerializer(serializers.Serializer):
    # Django Rest Framework can automatically deal with single object inputed and a list of them, we don't need to modify the serializer
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    price_per_day = serializers.FloatField(read_only=True)
    thumbnail_url = serializers.CharField(read_only=True)   
    
    



