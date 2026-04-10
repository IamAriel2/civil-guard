import json
import requests
import time

def get_coordinates(address, api_key):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    response = requests.get(url).json()
    if response.get('status') == 'OK':
        location = response['results'][0]['geometry']['location']
        return [location['lat'], location['lng']]
    return None

with open('data/shelters.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

api_key = "AIzaSyDC4F_n5UciqmSvjZSXQl6q4Ws4lDQIM0o"

for item in data:
    address = item.get("addr2")
    if address:
        coords = get_coordinates(address, api_key)
        if coords:
            item['coords'] = coords
    time.sleep(0.1)

with open('data/shelters.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)