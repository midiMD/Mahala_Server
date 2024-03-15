import requests


GOOGLE_API_KEY = 'AIzaSyDse4apEDFgIFDnX-6qyVq_3u1A30tFNbk'
GOOGLE_MAPS_URL = "https://maps.googleapis.com/maps/api/geocode/json?" # Base URL for Google geocoding API
def fetch_house_info(postcode, street, house_number):
    address = f"{house_number}, {street}, {postcode}" 
    api_url = f"{GOOGLE_MAPS_URL}country=gb&address={address}&key={GOOGLE_API_KEY}"
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        place_id= data.get('results')[0].get('place_id')
        lat, lng = data.get('results')[0].get('geometry').get('location').get('lat'), data.get('results')[0].get('geometry').get('location').get('lng')
        return {"place_id":place_id, "lat":lat, "lng":lng}
    else:
        print(response.text)
        return None
    