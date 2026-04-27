import math
from typing import Tuple

class GisService:
    @staticmethod
    def gps_to_web_mercator(lat: float, lng: float) -> Tuple[float, float]:
        """
        Converts GPS coordinates (EPSG:4326) to Web Mercator (EPSG:3857).
        Based on the mathematical formula provided by the user for IMPLAN GeoServer compatibility.
        """
        x = lng * 20037508.34 / 180
        y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180) * 20037508.34 / 180
        return x, y

    @staticmethod
    def get_bbox_from_point(lat: float, lng: float, buffer_meters: float = 10.0) -> str:
        """
        Creates a BBOX string (xmin, ymin, xmax, ymax) centered on a GPS point.
        """
        x, y = GisService.gps_to_web_mercator(lat, lng)
        return f"{x - buffer_meters},{y - buffer_meters},{x + buffer_meters},{y + buffer_meters}"
