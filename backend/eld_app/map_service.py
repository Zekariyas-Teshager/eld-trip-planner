# map_service.py
import requests
import math

class MapService:
    def __init__(self):
        # No API key needed for OSRM
        self.osrm_base_url = "http://router.project-osrm.org"
    
    def get_route(self, start_coords, end_coords):
        """Use free OSRM service for routing - no API key needed"""
        try:
            return self._get_osrm_route(start_coords, end_coords)
        except Exception as e:
            print(f"OSRM routing failed: {e}")
            # Fallback to straight line calculation
            return self._generate_straight_route(start_coords, end_coords)
    
    def _get_osrm_route(self, start_coords, end_coords):
        """Get route from OSRM (Open Source Routing Machine)"""
        start_lng, start_lat = start_coords
        end_lng, end_lat = end_coords
        
        # OSRM endpoint for route between two points
        url = f"{self.osrm_base_url}/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}"
        params = {
            'overview': 'full',
            'geometries': 'geojson',
            'steps': 'false'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data['code'] == 'Ok':
            route = data['routes'][0]
            return {
                'distance_km': route['distance'] / 1000,  # Convert meters to km
                'duration_hours': route['duration'] / 3600,  # Convert seconds to hours
                'coordinates': route['geometry']['coordinates']  # [lng, lat] format
            }
        else:
            raise Exception(f"OSRM routing error: {data.get('message', 'Unknown error')}")
    
    def _generate_straight_route(self, start_coords, end_coords):
        """Fallback: generate straight line route if OSRM fails"""
        start_lng, start_lat = start_coords
        end_lng, end_lat = end_coords
        
        # Calculate straight-line distance
        distance_km = self._calculate_great_circle_distance(start_coords, end_coords)
        
        # Generate intermediate points for the polyline
        coordinates = []
        num_points = max(10, int(distance_km / 50))  # Points every ~50km
        
        for i in range(num_points + 1):
            fraction = i / num_points
            lng = start_lng + (end_lng - start_lng) * fraction
            lat = start_lat + (end_lat - start_lat) * fraction
            coordinates.append([lng, lat])
        
        return {
            'distance_km': distance_km,
            'duration_hours': distance_km / 80,  # Assume 80 km/h average speed
            'coordinates': coordinates
        }
    
    def _calculate_great_circle_distance(self, coord1, coord2):
        """Calculate great circle distance between two coordinates in km"""
        lng1, lat1 = coord1
        lng2, lat2 = coord2
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        lng1_rad = math.radians(lng1)
        lng2_rad = math.radians(lng2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        radius_earth_km = 6371
        return radius_earth_km * c