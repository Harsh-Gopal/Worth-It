import math
from typing import List, Tuple
from app.geo.haversine import haversine_km, KM_PER_DEG_LAT

class HexGridGenerator:
    """
    Generates a deterministic, hexagonally packed grid of coordinates
    covering a given circular search area.
    """
    
    @staticmethod
    def generate(center_lat: float, center_lng: float, radius_km: float, spacing_km: float) -> List[Tuple[float, float]]:
        """
        Returns a list of (latitude, longitude) tuples.
        The points are sorted by distance from the center (nearest first).
        The center point itself is always included.
        """
        if radius_km <= 0:
            return [(center_lat, center_lng)]
            
        km_per_deg_lng = KM_PER_DEG_LAT * math.cos(math.radians(center_lat))
        # Distance between rows in a hex grid
        row_step_km = spacing_km * math.sqrt(3) / 2
        
        points: List[Tuple[float, float]] = []
        n_rows = int(radius_km / row_step_km) + 1
        
        for row in range(-n_rows, n_rows + 1):
            y_km = row * row_step_km
            x_offset = (spacing_km / 2) if row % 2 else 0.0
            n_cols = int(radius_km / spacing_km) + 1
            
            for col in range(-n_cols, n_cols + 1):
                x_km = col * spacing_km + x_offset
                lat = center_lat + y_km / KM_PER_DEG_LAT
                lng = center_lng + x_km / km_per_deg_lng
                
                # Use strict haversine check to drop points that fall outside due to flat-earth distortion
                if haversine_km(center_lat, center_lng, lat, lng) <= radius_km:
                    points.append((lat, lng))
                
        # Sort by exact geographic distance to center
        points.sort(key=lambda p: haversine_km(center_lat, center_lng, p[0], p[1]))
        return points
