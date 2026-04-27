import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.modules.investments.infrastructure.gis_service import GisService

lat = 32.49110422428155
lng = -116.90942970348044

bbox = GisService.get_bbox_from_point(lat, lng, buffer_meters=5)
x, y = GisService.gps_to_web_mercator(lat, lng)

print(f"GPS: {lat}, {lng}")
print(f"Web Mercator X: {x}, Y: {y}")
print(f"BBOX (5m): {bbox}")
