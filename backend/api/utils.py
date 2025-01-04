from dataclasses import dataclass
import requests
import os
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
print("Google API key : ", GOOGLE_API_KEY)
GOOGLE_MAPS_URL = "https://maps.googleapis.com/maps/api/geocode/json?" # Base URL for Google geocoding API
def fetch_house_info(postcode, street, house_number,apartment_number):
    if apartment_number != "":
        address = f"{apartment_number}, {house_number}, {street}, {postcode}" 
    else:
        address = f"{house_number}, {street}, {postcode}" 

    api_url = f"{GOOGLE_MAPS_URL}country=gb&address={address}&key={GOOGLE_API_KEY}"
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        #print(data)
        place_id= data.get('results')[0].get('place_id')
        lat, lng = data.get('results')[0].get('geometry').get('location').get('lat'), data.get('results')[0].get('geometry').get('location').get('lng')
        return {"place_id":place_id, "lat":lat, "lng":lng}
    else:
        print(response.text)
        return {"status_code":response.status_code,"error" : response.text}
@dataclass
class MarketViewItem():
    id: int
    distance: float
    title: str
    owner_name: str
    price_per_day: float
    image_url: str

@dataclass
class InventoryItem():
    id:int
    title:str
    price_per_day:float
    thumbnail_url:str
    

# print(fetch_house_info("TW34JG", "Civic Street", "18","24"))
# print(fetch_house_info("TW34JG", "civic street", "18","24"))