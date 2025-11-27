import requests
import math
import time
from typing import Dict, List, Optional

class MapService:
    def __init__(self):
        # No API key needed for OSRM
        self.osrm_base_url = "http://router.project-osrm.org"
    
    def geocode_location(self, location_name: str) -> Optional[List[float]]:
        """Convert location name to coordinates using OpenStreetMap Nominatim"""
        # First, try the real geocoding API
        real_coords = self._geocode_with_nominatim(location_name)
        if real_coords:
            return real_coords
        
        # Fallback to mock data if API fails
        return self._get_mock_coordinates(location_name)
    
    def _geocode_with_nominatim(self, location_name: str) -> Optional[List[float]]:
        """Real geocoding using OpenStreetMap Nominatim - FREE, no API key"""
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': location_name,
            'format': 'json',
            'limit': 1
        }
        
        # Important: Add user agent header as required by Nominatim
        headers = {
            'User-Agent': 'ELD-Trip-Planner/1.0 (educational-trucking-app)'
        }
        
        try:
            print(f"🌍 Geocoding: {location_name}")
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    # OSRM uses [longitude, latitude] format
                    lon = float(data[0]['lon'])
                    lat = float(data[0]['lat'])
                    display_name = data[0]['display_name']
                    
                    print(f"📍 Found: {location_name} -> [{lon}, {lat}]")
                    print(f"   Display: {display_name}")
                    return [lon, lat]  # Return in [lon, lat] format for OSRM
                else:
                    print(f"❌ No geocoding results for: {location_name}")
            else:
                print(f"❌ Geocoding API error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Geocoding failed: {e}")
        
        return None
    
    def _get_mock_coordinates(self, location_name: str) -> List[float]:
        """Fallback coordinates for when API fails"""
        geocodes = {
            'new york, ny': [-74.006, 40.7128],
            'new york': [-74.006, 40.7128],
            'ny': [-74.006, 40.7128],
            'chicago, il': [-87.6298, 41.8781],
            'chicago': [-87.6298, 41.8781],
            'los angeles, ca': [-118.2437, 34.0522],
            'los angeles': [-118.2437, 34.0522],
            'la': [-118.2437, 34.0522],
            'philadelphia, pa': [-75.1652, 39.9526],
            'philadelphia': [-75.1652, 39.9526],
            'houston, tx': [-95.3698, 29.7604],
            'houston': [-95.3698, 29.7604],
            'phoenix, az': [-112.0740, 33.4484],
            'phoenix': [-112.0740, 33.4484],
            'miami, fl': [-80.1918, 25.7617],
            'miami': [-80.1918, 25.7617],
            'seattle, wa': [-122.3321, 47.6062],
            'seattle': [-122.3321, 47.6062],
        }
        
        clean_name = location_name.lower().strip()
        return geocodes.get(clean_name, [-98.5795, 39.8283])  # Default to US center

    def get_route(self, start_coords, end_coords):
        """Use free OSRM service for routing - no API key needed"""
        try:
            # Validate coordinates
            if not start_coords or not end_coords:
                raise ValueError("Invalid coordinates provided")
                
            print(f"🗺️ Getting OSRM route from {start_coords} to {end_coords}")
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
            distance_km = route['distance'] / 1000  # Convert meters to km
            duration_hours = route['duration'] / 3600  # Convert seconds to hours
            
            print(f"✅ OSRM Route: {distance_km:.1f} km, {duration_hours:.1f} hours")
            return {
                'distance_km': distance_km,
                'duration_hours': duration_hours,
                'coordinates': route['geometry']['coordinates']  # [lng, lat] format
            }
        else:
            raise Exception(f"OSRM routing error: {data.get('message', 'Unknown error')}")
    
    def _generate_straight_route(self, start_coords, end_coords):
        """Fallback: generate straight line route if OSRM fails"""
        # Handle None coordinates
        if not start_coords or not end_coords:
            start_coords = [-98.5795, 39.8283]  # US center
            end_coords = [-98.5795, 39.8283]
            
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
        
        duration_hours = distance_km / 80  # Assume 80 km/h average speed
        
        print(f"📏 Straight-line route: {distance_km:.1f} km, {duration_hours:.1f} hours")
        
        return {
            'distance_km': distance_km,
            'duration_hours': duration_hours,
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

    def generate_map(self, coordinates: List[List[float]], stops: List[Dict], output_path: str = 'route_map.html') -> Optional[str]:
        """Generate an HTML map with route and stops"""
        try:
            import folium
            
            if not coordinates or len(coordinates) < 2:
                print("❌ Not enough coordinates for map generation")
                return None
            
            # Convert coordinates to [lat, lng] format for folium
            route_coords = [[coord[1], coord[0]] for coord in coordinates]
            
            # Calculate map center
            lats = [coord[1] for coord in coordinates]
            lngs = [coord[0] for coord in coordinates]
            center_lat = (min(lats) + max(lats)) / 2
            center_lng = (min(lngs) + max(lngs)) / 2
            
            # Create map
            m = folium.Map(location=[center_lat, center_lng], zoom_start=5)
            
            # Add route line
            folium.PolyLine(
                route_coords,
                color='blue',
                weight=5,
                opacity=0.7,
                popup='Truck Route'
            ).add_to(m)
            
            # Add stops with different markers
            stop_icons = {
                'PICKUP': 'green',
                'DROPOFF': 'red', 
                'FUEL': 'orange',
                'REST': 'purple',
                'OVERNIGHT': 'darkblue'
            }
            
            for i, stop in enumerate(stops):
                if i < len(route_coords):
                    # Distribute stops along the route
                    stop_index = min(int((i / len(stops)) * len(route_coords)), len(route_coords) - 1)
                    stop_coords = route_coords[stop_index]
                    
                    folium.Marker(
                        stop_coords,
                        popup=f"{stop['type']}: {stop['location']}",
                        tooltip=stop['type'],
                        icon=folium.Icon(color=stop_icons.get(stop['type'], 'gray'))
                    ).add_to(m)
            
            # Save map
            m.save(output_path)
            print(f"✅ Map generated: {output_path}")
            return output_path
            
        except ImportError:
            print("❌ Folium not installed, skipping map generation")
            return None
        except Exception as e:
            print(f"❌ Map generation failed: {e}")
            return None