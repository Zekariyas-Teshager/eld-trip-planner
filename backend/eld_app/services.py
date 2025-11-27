import math
from typing import Dict, List
from .models import Trip, Stop
from .map_service import MapService

class TripPlannerService:
    def __init__(self):
        self.avg_speed_kmh = 80
        self.fuel_stop_interval = 1600
        self.driving_hours_per_day = 11
        self.daily_window_hours = 14
        self.cycle_hours = 70
        self.cycle_days = 8
        self.map_service = MapService()
    
    def calculate_distance(self, loc1: str, loc2: str) -> float:
        """Use real routing service for accurate distances"""
        coords1 = self.geocode_location(loc1)
        coords2 = self.geocode_location(loc2)
        
        route_data = self.map_service.get_route(coords1, coords2)
        return route_data['distance_km']
    
    # In your plan_trip method in services.py
    def plan_trip(self, current_location: str, pickup_location: str, 
                dropoff_location: str, current_cycle_used: float) -> Dict:
        
        print(f"🚛 Planning trip: {current_location} -> {pickup_location} -> {dropoff_location}")
        
        try:
            # Geocode all locations to get real coordinates
            current_coords = self.map_service.geocode_location(current_location)
            pickup_coords = self.map_service.geocode_location(pickup_location)
            dropoff_coords = self.map_service.geocode_location(dropoff_location)
            
            print(f"📍 Coordinates:")
            print(f"   Current: {current_coords}")
            print(f"   Pickup: {pickup_coords}") 
            print(f"   Dropoff: {dropoff_coords}")
            
            # Calculate distances using OSRM
            to_pickup_route = self.map_service.get_route(current_coords, pickup_coords)
            to_dropoff_route = self.map_service.get_route(pickup_coords, dropoff_coords)
            
            to_pickup_distance = to_pickup_route['distance_km']
            to_dropoff_distance = to_dropoff_route['distance_km']
            total_distance = to_pickup_distance + to_dropoff_distance
            
            to_pickup_duration = to_pickup_route['duration_hours']
            to_dropoff_duration = to_dropoff_route['duration_hours']
            total_duration = to_pickup_duration + to_dropoff_duration
            
            # Get full route coordinates for the map
            full_route = self.map_service.get_route(current_coords, dropoff_coords)
            
            # Generate stops and logs
            stops = self.generate_stops(total_distance, total_duration)
            daily_logs = self.generate_daily_logs(total_duration, current_cycle_used)
            
            # Generate map
            map_path = self.map_service.generate_map(full_route['coordinates'], stops)
            
            return {
                'total_distance_km': round(total_distance, 2),
                'total_duration_hours': round(total_duration, 2),
                'stops': stops,
                'daily_logs': daily_logs,
                'route_coordinates': full_route['coordinates'],
                'map_path': map_path,
                'route': {
                    'current_to_pickup': {
                        'distance': round(to_pickup_distance, 2),
                        'duration': round(to_pickup_duration, 2)
                    },
                    'pickup_to_dropoff': {
                        'distance': round(to_dropoff_distance, 2),
                        'duration': round(to_dropoff_duration, 2)
                    }
                }
            }
            
        except Exception as e:
            print(f"❌ Error in plan_trip: {e}")
            # Return fallback data
            return self._get_fallback_trip_data(current_location, pickup_location, dropoff_location, current_cycle_used)

    def calculate_duration(self, distance: float) -> float:
        return distance / self.avg_speed_kmh
    
    def generate_stops(self, total_distance: float, total_duration: float) -> List[Dict]:
        stops = []
        
        # Add pickup stop (1 hour)
        stops.append({
            'type': 'PICKUP',
            'location': 'Pickup Location',
            'distance': 0,
            'duration': 0,
            'stop_duration': 1.0
        })
        
        # Add fuel stops every 1600 km
        fuel_stop_count = int(total_distance // self.fuel_stop_interval)
        for i in range(1, fuel_stop_count + 1):
            fuel_distance = i * self.fuel_stop_interval
            if fuel_distance < total_distance:
                stops.append({
                    'type': 'FUEL',
                    'location': f'Fuel Stop {i}',
                    'distance': fuel_distance,
                    'duration': fuel_distance / self.avg_speed_kmh,
                    'stop_duration': 0.5
                })
        
        # Add mandatory 30-minute rest breaks every 8 hours of driving
        rest_break_count = int(total_duration // 8)
        for i in range(1, rest_break_count + 1):
            rest_duration = i * 8
            rest_distance = rest_duration * self.avg_speed_kmh
            if rest_distance < total_distance:
                stops.append({
                    'type': 'REST',
                    'location': f'30-min Break after {i*8} hours',
                    'distance': rest_distance,
                    'duration': rest_duration,
                    'stop_duration': 0.5
                })
        
        # Add overnight stops based on 11-hour daily driving limit
        daily_driving_distance = self.driving_hours_per_day * self.avg_speed_kmh
        overnight_count = int(total_distance // daily_driving_distance)
        
        for i in range(1, overnight_count + 1):
            overnight_distance = i * daily_driving_distance
            if overnight_distance < total_distance:
                stops.append({
                    'type': 'OVERNIGHT',
                    'location': f'Overnight Rest Day {i}',
                    'distance': overnight_distance,
                    'duration': i * self.driving_hours_per_day,
                    'stop_duration': 10.0
                })
        
        # Add dropoff stop (1 hour)
        stops.append({
            'type': 'DROPOFF',
            'location': 'Dropoff Location',
            'distance': total_distance,
            'duration': total_duration,
            'stop_duration': 1.0
        })
        
        # Sort stops by distance and remove any that are too close
        stops.sort(key=lambda x: x['distance'])
        
        # Filter stops to ensure reasonable spacing
        filtered_stops = []
        min_distance_gap = 50  # km
        
        for stop in stops:
            if not filtered_stops or stop['distance'] - filtered_stops[-1]['distance'] >= min_distance_gap:
                filtered_stops.append(stop)
        
        return filtered_stops
    

    def generate_daily_logs(self, total_duration_hours: float, current_cycle_used: float) -> List[Dict]:
        """
        Generate realistic daily logs with proper HOS scheduling and schedule[] for graph
        """
        if total_duration_hours <= 0:
            total_duration_hours = 0.1

        # Max driving ~10.5–11 hrs/day, but we plan conservatively
        max_driving_per_day = 10.5
        days_needed = max(1, math.ceil(total_duration_hours / max_driving_per_day))
        driving_per_day = total_duration_hours / days_needed

        daily_logs = []
        cycle_used = float(current_cycle_used)

        current_time = 0.0  # Start at midnight

        for day in range(1, days_needed + 1):
            is_first_day = day == 1
            is_last_day = day == days_needed

            # === Realistic Daily Duty Split ===
            driving_today = min(driving_per_day, 11.0)
            if is_last_day and driving_today < 5:
                driving_today = max(driving_today, 3.0)  # Don't end with tiny drive

            # 30-minute break required after 8 hours driving
            break_needed = driving_today >= 8.0
            break_duration = 0.5 if break_needed else 0.0

            # On-duty not driving: pre/post trip, fueling, breaks
            on_duty_nd = 1.5 + (0.5 if break_needed else 0.0) + (0.5 if is_first_day or is_last_day else 0.0)
            total_on_duty = driving_today + on_duty_nd

            # Sleep: minimum 10 hours off/sleeper if full duty day
            sleeper_hours = 10.0 if total_on_duty >= 13 else 11.0
            if is_last_day:
                sleeper_hours = max(8.0, 24 - total_on_duty - 1.0)

            off_duty_hours = 24 - total_on_duty - sleeper_hours

            # === Build Realistic 24-Hour Schedule ===
            schedule = []

            # Start with sleep (Sleeper Berth or Off Duty)
            sleep_start = 0.0
            sleep_end = 10.0 if not is_last_day else 8.0
            schedule.append({
                "status": "SB" if sleeper_hours >= 10 else "OFF",
                "start": sleep_start,
                "end": sleep_end,
                "remark": "10-hr reset completed" if not is_last_day else "End of trip",
            })

            current_time = sleep_end

            # Pre-trip inspection / on-duty
            schedule.append({
                "status": "ON",
                "start": current_time,
                "end": current_time + 0.5,
                "remark": "Pre-trip inspection",
            })
            current_time += 0.5

            # Morning drive block
            morning_drive = min(5.0, driving_today)
            schedule.append({
                "status": "D",
                "start": current_time,
                "end": current_time + morning_drive
            })
            current_time += morning_drive

            # 30-minute break if needed
            if break_needed:
                schedule.append({
                    "status": "ON",
                    "start": current_time,
                    "end": current_time + 0.5,
                    "remark": "30-min break",
                })
                current_time += 0.5

            # Afternoon drive block
            remaining_drive = driving_today - morning_drive
            if remaining_drive > 0:
                schedule.append({
                    "status": "D",
                    "start": current_time,
                    "end": current_time + remaining_drive
                })
                current_time += remaining_drive

            # Post-trip / paperwork
            schedule.append({
                "status": "ON",
                "start": current_time,
                "end": current_time + 0.5,
                "remark": "Post-trip duties",
            })
            current_time += 0.5

            # Final off-duty / sleeper
            final_status = "OFF" if is_last_day else "SB"
            schedule.append({
                "status": final_status,
                "start": current_time,
                "end": 24.0,
                "remark": "10-hr reset completed" if not is_last_day else "End of trip",
            })

            # Update cycle
            cycle_used += total_on_duty

            daily_logs.append({
                "day_number": day,
                "driving_hours": round(driving_today, 1),
                "on_duty_hours": round(total_on_duty, 1),
                "off_duty_hours": round(off_duty_hours, 1),
                "sleeper_hours": round(sleeper_hours, 1),
                "cycle_used": round(cycle_used, 1),
                "requires_34_hour_restart": cycle_used >= 68.0,  # Warn early
                "schedule": schedule,  # This powers the graph!
            })

        return daily_logs