from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

geolocator = Nominatim(user_agent="dating_bot_app", timeout=10)

@lru_cache(maxsize=1000)
def normalize_city(city_input: str) -> tuple:
    """
    Возвращает (city_name, country, latitude, longitude)
    """
    if not city_input or len(city_input) < 2:
        return (city_input, None, None, None)
    
    try:
        location = geolocator.geocode(city_input, language='ru', exactly_one=True, addressdetails=True)
        
        if location:
            address = location.raw.get('address', {})
            
            city_name = (
                address.get('city') or 
                address.get('town') or 
                address.get('village') or
                address.get('municipality') or
                address.get('county') or
                address.get('state')
            )
            
            if not city_name:
                display = location.raw.get('display_name', '')
                city_name = display.split(',')[0].strip() if display else city_input.strip().title()
            
            country = address.get('country')
            
            return (city_name, country, location.latitude, location.longitude)
        else:
            return (city_input.strip().title(), None, None, None)
            
    except Exception as e:
        logger.error(f"Ошибка геокодинга '{city_input}': {e}")
        return (city_input.strip().title(), None, None, None)

def get_city_from_coords(latitude: float, longitude: float) -> tuple:
    """
    Возвращает (city_name, country, full_address)
    """
    if not latitude or not longitude:
        return (None, None, None)
    
    try:
        location = geolocator.reverse(f"{latitude}, {longitude}", language='ru', exactly_one=True)
        
        if location:
            address = location.raw.get('address', {})
            
            city_name = (
                address.get('city') or 
                address.get('town') or 
                address.get('village') or
                address.get('municipality') or
                address.get('county') or
                address.get('state') or
                address.get('country')
            )
            
            country = address.get('country')
            
            return (city_name, country, location.address)
        else:
            return (None, None, None)
            
    except Exception as e:
        logger.error(f"Ошибка reverse geocoding: {e}")
        return (None, None, None)

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    if not all([lat1, lon1, lat2, lon2]):
        return float('inf')
    try:
        return geodesic((lat1, lon1), (lat2, lon2)).kilometers
    except:
        return float('inf')

def format_distance(km: float) -> str:
    if km == float('inf') or km > 9000:
        return ""
    elif km < 1:
        return f"{int(km * 1000)} м"
    elif km < 10:
        return f"{km:.1f} км"
    else:
        return f"{int(km)} км"