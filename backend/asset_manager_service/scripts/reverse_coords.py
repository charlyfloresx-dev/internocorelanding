import math

def web_mercator_to_gps(x: float, y: float):
    lng = x * 180 / 20037508.34
    lat = (math.atan(math.exp(y / (20037508.34 / 180) * (math.pi / 180))) * 360 / math.pi) - 90
    return lat, lng

# Functional BBOX Center
x_center = -13014275
y_center = 3827960

lat, lng = web_mercator_to_gps(x_center, y_center)
print(f"Center Web Mercator: {x_center}, {y_center}")
print(f"Center GPS: {lat}, {lng}")
