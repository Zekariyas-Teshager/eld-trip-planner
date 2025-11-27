import os
import sys
import django
from dotenv import load_dotenv

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eld_backend.settings')
django.setup()

from eld_app.map_service import MapService

def test_mapping():
    print("🧪 Testing OpenRouteService API...")
    
    map_service = MapService()
    
    # Test coordinates: New York to Chicago
    start_coords = [-74.006, 40.7128]  # NY
    end_coords = [-87.6298, 41.8781]   # Chicago
    
    print("📍 Testing route from New York to Chicago...")
    
    try:
        route_data = map_service.get_route(start_coords, end_coords)
        
        print("✅ API Connection Successful!")
        print(f"📏 Distance: {route_data['distance_km']} km")
        print(f"⏱️  Duration: {route_data['duration_hours']} hours")
        print(f"📍 Coordinates points: {len(route_data['coordinates'])}")
        
        # Test map generation
        print("\n🗺️ Testing map generation...")
        map_path = map_service.generate_map(
            route_data['coordinates'], 
            [{'type': 'PICKUP', 'location': 'NY', 'distance': 0, 'duration': 0, 'stop_duration': 1},
             {'type': 'DROPOFF', 'location': 'Chicago', 'distance': route_data['distance_km'], 'duration': route_data['duration_hours'], 'stop_duration': 1}]
        )
        
        if map_path:
            print(f"✅ Map generated: {map_path}")
        else:
            print("❌ Map generation failed")
            
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        print("💡 Check your API key and internet connection")

if __name__ == "__main__":
    test_mapping()