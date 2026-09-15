from app.geo.haversine import haversine_km
from app.geo.hex_grid import HexGridGenerator

def test_haversine_known_points():
    # New Delhi (28.6139, 77.2090) to Mumbai (19.0760, 72.8777)
    # Distance is approx 1148 km
    dist = haversine_km(28.6139, 77.2090, 19.0760, 72.8777)
    assert 1140 < dist < 1160

    # Distance to self should be 0
    dist = haversine_km(28.6139, 77.2090, 28.6139, 77.2090)
    assert dist == 0.0

def test_hex_grid_center_point():
    points = HexGridGenerator.generate(12.9716, 77.5946, 0.0, 1.5)
    assert len(points) == 1
    assert points[0] == (12.9716, 77.5946)

def test_hex_grid_coverage():
    center_lat, center_lng = 12.9716, 77.5946
    radius = 3.0
    spacing = 1.5
    points = HexGridGenerator.generate(center_lat, center_lng, radius, spacing)
    
    # Ensure there are multiple points
    assert len(points) > 1
    
    # Ensure all points fall within the radius
    for lat, lng in points:
        dist = haversine_km(center_lat, center_lng, lat, lng)
        assert dist <= radius
        
    # Ensure first point is the closest (center)
    assert points[0] == (center_lat, center_lng)
    
    # Ensure no duplicates
    assert len(set(points)) == len(points)
