import math
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from .map_service import MapService

class TripPlannerService:
    def __init__(self):
        # HOS Limits (FMCSA regulations)
        self.max_driving_hours = 11          # 11-hour driving limit
        self.max_duty_hours = 14             # 14-hour duty window  
        self.min_rest_hours = 10             # 10-hour minimum rest
        self.break_after_hours = 8           # 30-min break after 8 hours driving
        self.cycle_limit_hours = 70          # 70-hour/8-day limit
        
        # Trucking assumptions
        self.avg_speed_kmh = 80              # Average truck speed km/h
        self.avg_speed_mph = 50              # Average truck speed mph
        self.fuel_interval_miles = 1000      # Fuel every 1000 miles per assessment
        self.fuel_interval_km = 1600         # Fuel every 1600 km
        self.pickup_duration = 1.0           # 1 hour loading
        self.dropoff_duration = 1.0          # 1 hour unloading
        self.fuel_stop_duration = 0.5        # 30 minutes fueling
        self.rest_stop_duration = 0.5        # 30 minutes break
        
        self.map_service = MapService()
    
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
            current_to_pickup_data = self.map_service.get_route(current_coords, pickup_coords)
            pickup_to_dropoff_data = self.map_service.get_route(pickup_coords, dropoff_coords)
            
            to_pickup_distance_km = current_to_pickup_data['distance_km']
            to_dropoff_distance_km = pickup_to_dropoff_data['distance_km']
            total_distance_km = to_pickup_distance_km + to_dropoff_distance_km
            
            to_pickup_duration = current_to_pickup_data['duration_hours']
            to_dropoff_duration = pickup_to_dropoff_data['duration_hours']
            total_duration = to_pickup_duration + to_dropoff_duration
            
            # Get full route coordinates for the map
            full_route = self.map_service.get_route(current_coords, dropoff_coords)
            
            # Convert distances to miles
            KM_TO_MILES = 0.621371
            current_to_pickup_miles = to_pickup_distance_km * KM_TO_MILES
            pickup_to_dropoff_miles = to_dropoff_distance_km * KM_TO_MILES
            
            # Generate stops based on realistic durations and HOS rules
            stops = self._generate_hos_compliant_stops(
                current_location=current_location,
                pickup_location=pickup_location,
                dropoff_location=dropoff_location,
                current_to_pickup_miles=current_to_pickup_miles,
                current_to_pickup_hours=to_pickup_duration,
                pickup_to_dropoff_miles=pickup_to_dropoff_miles,
                pickup_to_dropoff_hours=to_dropoff_duration,
                current_cycle_used=current_cycle_used
            )
            
            # Get real location names for stops using reverse geocoding
            stops_with_locations = self._add_real_location_names(stops, full_route['coordinates'])

            # Assign day numbers to stops
            stops_with_locations_and_day = self._assign_days_to_stops(stops_with_locations)
            
            # Generate daily logs from the stops
            daily_logs = self._generate_daily_logs_from_stops(stops_with_locations_and_day, current_cycle_used)
            
            # Generate map with all stops
            map_path = self.map_service.generate_map(full_route['coordinates'], stops_with_locations)

            # Get Last stop to calculate total duration
            last_stop = stops_with_locations[-1] if stops_with_locations else None
            if last_stop:
                total_duration = last_stop['cumulative_hours'] 
            # add dropoff duration
            total_duration += self.dropoff_duration
            
            return {
                'trip_info': {
                    'current_location': current_location,
                    'pickup_location': pickup_location,
                    'dropoff_location': dropoff_location,
                    'total_distance_km': round(total_distance_km, 2),
                    'total_distance_miles': round(total_distance_km * KM_TO_MILES, 2),
                    'total_duration_hours': round(total_duration, 2),
                    'estimated_days': len(daily_logs),
                    'current_cycle_start': current_cycle_used,
                    'final_cycle_used': daily_logs[-1]['cycle_used'] if daily_logs else current_cycle_used
                },
                'route': {
                    'current_to_pickup': {
                        'distance_km': round(to_pickup_distance_km, 2),
                        'distance_miles': round(current_to_pickup_miles, 2),
                        'duration_hours': round(to_pickup_duration, 2)
                    },
                    'pickup_to_dropoff': {
                        'distance_km': round(to_dropoff_distance_km, 2),
                        'distance_miles': round(pickup_to_dropoff_miles, 2),
                        'duration_hours': round(to_dropoff_duration, 2)
                    }
                },
                'stops': stops_with_locations_and_day,
                'daily_logs': daily_logs,
                'route_coordinates': full_route['coordinates'],
                'map_path': map_path
            }
            
        except Exception as e:
            print(f"❌ Error in plan_trip: {e}")
            raise e
    
    def _generate_hos_compliant_stops(
        self,
        current_location: str,
        pickup_location: str,
        dropoff_location: str,
        current_to_pickup_miles: float,
        current_to_pickup_hours: float,
        pickup_to_dropoff_miles: float,
        pickup_to_dropoff_hours: float,
        current_cycle_used: float
    ) -> List[Dict]:
        """
        Generate HOS-compliant stops based on realistic route durations
        """
        stops = []
        
        # Convert everything to miles for calculations
        total_distance_miles = current_to_pickup_miles + pickup_to_dropoff_miles
        total_duration_hours = current_to_pickup_hours + pickup_to_dropoff_hours
        
        # 1. START: Current Location
        stops.append({
            'type': 'START',
            'location': current_location.title(),
            'cumulative_distance_miles': 0.0,
            'cumulative_distance_km': 0.0,
            'cumulative_hours': 0.0,
            'stop_duration': 0.0,
            'day': 1,
            'notes': 'Trip starting point',
            'current_cycle_used': current_cycle_used
        })
        
        # Track HOS compliance
        cumulative_driving_today = 0.0
        cumulative_on_duty_today = 0.0
        cumulative_driving_since_break = 0.0
        cumulative_distance = 0.0
        cumulative_hours = 0.0
        next_fuel_check = self.fuel_interval_miles
        
        # 2. Simulate CURRENT → PICKUP segment
        segment_stops = self._simulate_driving_segment(
            segment_name="CURRENT_TO_PICKUP",
            segment_distance_miles=current_to_pickup_miles,
            segment_duration_hours=current_to_pickup_hours,
            start_distance=cumulative_distance,
            start_hours=cumulative_hours,
            cumulative_driving_today=cumulative_driving_today,
            cumulative_on_duty_today=cumulative_on_duty_today,
            cumulative_driving_since_break=cumulative_driving_since_break,
            next_fuel_check=next_fuel_check
        )
        
        stops.extend(segment_stops)
        
        # Update totals after segment
        if segment_stops:
            last_segment_stop = segment_stops[-1]
            cumulative_distance = current_to_pickup_miles
            cumulative_hours = last_segment_stop.get('cumulative_hours', current_to_pickup_hours)
            cumulative_driving_today = last_segment_stop.get('cumulative_driving_today', 0)
            cumulative_on_duty_today = last_segment_stop.get('cumulative_on_duty_today', 0)
            cumulative_driving_since_break = last_segment_stop.get('cumulative_driving_since_break', 0)
            next_fuel_check = last_segment_stop.get('next_fuel_check', self.fuel_interval_miles)
            current_hours = last_segment_stop.get('current_hours', cumulative_hours)    
            
        
        # 3. PICKUP Location (1 hour loading)
        stops.append({
            'type': 'PICKUP',
            'location': pickup_location.title(),
            'cumulative_distance_miles': round(cumulative_distance, 2),
            'cumulative_distance_km': round(cumulative_distance / 0.621371, 2),
            'cumulative_hours': round(current_hours, 2),
            'stop_duration': self.pickup_duration,
            'notes': '1 hour loading time'
        })
        
        cumulative_hours += self.pickup_duration
        cumulative_on_duty_today += self.pickup_duration
        
        # 4. Simulate PICKUP → DROPOFF segment
        segment_stops = self._simulate_driving_segment(
            segment_name="PICKUP_TO_DROPOFF",
            segment_distance_miles=pickup_to_dropoff_miles,
            segment_duration_hours=pickup_to_dropoff_hours,
            start_distance=cumulative_distance,
            start_hours=cumulative_hours,
            cumulative_driving_today=cumulative_driving_today,
            cumulative_on_duty_today=cumulative_on_duty_today,
            cumulative_driving_since_break=cumulative_driving_since_break,
            next_fuel_check=next_fuel_check,
            is_after_pickup=True
        )
        
        stops.extend(segment_stops)
        
        # Update totals after second segment
        if segment_stops:
            last_segment_stop = segment_stops[-1]
            cumulative_distance = total_distance_miles
            cumulative_hours = last_segment_stop.get('cumulative_hours', total_duration_hours)
            cumulative_driving_today = last_segment_stop.get('cumulative_driving_today', 0)
            cumulative_on_duty_today = last_segment_stop.get('cumulative_on_duty_today', 0)
            cumulative_driving_since_break = last_segment_stop.get('cumulative_driving_since_break', 0)
            current_hours = last_segment_stop.get('current_hours', cumulative_hours)
            
        
        # 5. DROPOFF Location (1 hour unloading)
        stops.append({
            'type': 'DROPOFF',
            'location': dropoff_location.title(),
            'cumulative_distance_miles': round(total_distance_miles, 2),
            'cumulative_distance_km': round(total_distance_miles / 0.621371, 2),
            'cumulative_hours': round(current_hours, 2),
            'stop_duration': self.dropoff_duration,
            'notes': '1 hour unloading time'
        })
        
        return stops
    
    def _simulate_driving_segment(
        self,
        segment_name: str,
        segment_distance_miles: float,
        segment_duration_hours: float,
        start_distance: float,
        start_hours: float,
        cumulative_driving_today: float,
        cumulative_on_duty_today: float,
        cumulative_driving_since_break: float,
        next_fuel_check: float,
        is_after_pickup: bool = False
    ) -> List[Dict]:
        """Simulate driving through a segment and add stops when HOS limits are reached"""
        segment_stops = []
        
        # Break segment into chunks for simulation
        CHUNK_SIZE_HOURS = 0.5  # Check every 30 minutes
        num_chunks = max(1, int(math.ceil(segment_duration_hours / CHUNK_SIZE_HOURS)))
        chunk_hours = segment_duration_hours / num_chunks
        chunk_distance = segment_distance_miles / num_chunks
        
        current_cumulative_driving = cumulative_driving_today
        current_cumulative_on_duty = cumulative_on_duty_today
        current_cumulative_break = cumulative_driving_since_break
        current_fuel_check = next_fuel_check
        
        fuel_stop_counter = int(start_distance // self.fuel_interval_miles) + 1
        
        for chunk in range(num_chunks):
            # Update cumulative values
            current_cumulative_driving += chunk_hours
            current_cumulative_on_duty += chunk_hours
            current_cumulative_break += chunk_hours
            
            # Calculate current position
            chunk_progress = (chunk + 1) / num_chunks
            current_distance = start_distance + (chunk_progress * segment_distance_miles)
            current_hours = start_hours + (chunk_progress * segment_duration_hours)
            
            # CHECK 1: 30-minute break needed? (after 8 hours cumulative driving)
            if current_cumulative_break >= self.break_after_hours:
                print(f"  ⏱️  Adding 30-min break at {current_distance:.0f} miles")

                difference = self.break_after_hours - current_cumulative_break

                segment_stops.append({
                    'type': 'REST',
                    'location': f'Rest Area near mile {int(current_distance)}',
                    'cumulative_distance_miles': round(current_distance, 1),
                    'cumulative_distance_km': round(current_distance / 0.621371, 1),
                    'cumulative_hours': round(current_hours + difference, 2),
                    'stop_duration': self.rest_stop_duration,
                    'notes': f'30-min break after {current_cumulative_break:.1f}h driving',
                    'cumulative_driving_today': current_cumulative_driving,
                    'cumulative_on_duty_today': current_cumulative_on_duty,
                    'cumulative_driving_since_break': current_cumulative_break
                })
                
                current_cumulative_on_duty += self.rest_stop_duration
                current_cumulative_break = 0
                current_hours += self.rest_stop_duration
            
            # CHECK 2: Fuel stop needed? (every 1000 miles)
            if is_after_pickup and current_distance >= current_fuel_check:
                print(f"  ⛽ Adding fuel stop at {current_distance:.0f} miles")
                
                segment_stops.append({
                    'type': 'FUEL',
                    'location': f'Fuel Station {fuel_stop_counter}',
                    'cumulative_distance_miles': round(current_distance, 1),
                    'cumulative_distance_km': round(current_distance / 0.621371, 1),
                    'cumulative_hours': round(current_hours, 2),
                    'stop_duration': self.fuel_stop_duration,
                    'notes': f'Fuel stop at {current_distance:.0f} miles',
                    'cumulative_driving_today': current_cumulative_driving,
                    'cumulative_on_duty_today': current_cumulative_on_duty,
                    'cumulative_driving_since_break': current_cumulative_break
                })
                
                current_cumulative_on_duty += self.fuel_stop_duration
                fuel_stop_counter += 1
                current_fuel_check += self.fuel_interval_miles
                current_hours += self.fuel_stop_duration
            
            # CHECK 3: Daily driving limit reached? (11 hours)
            if current_cumulative_driving >= self.max_driving_hours:
                print(f"  🛑 Daily driving limit reached at {current_distance:.0f} miles")

                difference = self.max_driving_hours - current_cumulative_driving
                
                segment_stops.append({
                    'type': 'OVERNIGHT',
                    'location': f'Overnight Stop Day at mile {int(current_distance)}',
                    'cumulative_distance_miles': round(current_distance, 1),
                    'cumulative_distance_km': round(current_distance / 0.621371, 1),
                    'cumulative_hours': round(current_hours + difference, 2),
                    'stop_duration': self.min_rest_hours,
                    'notes': f'10-hour rest after {current_cumulative_driving:.1f}h driving',
                    'cumulative_driving_today': current_cumulative_driving,
                    'cumulative_on_duty_today': current_cumulative_on_duty,
                    'cumulative_driving_since_break': current_cumulative_break,
                    'day_ended': True
                })

                current_cumulative_driving = 0
                current_cumulative_on_duty = 0
                current_cumulative_break = 0
                current_hours += self.min_rest_hours
            
            # CHECK 4: Daily duty limit reached? (14 hours on-duty)
            elif current_cumulative_on_duty >= self.max_duty_hours:
                print(f"  🛑 Daily duty limit reached at {current_distance:.0f} miles")

                difference = self.max_duty_hours - current_cumulative_on_duty
                
                segment_stops.append({
                    'type': 'OVERNIGHT',
                    'location': f'Overnight Stop Day at mile {int(current_distance)}',
                    'cumulative_distance_miles': round(current_distance, 1),
                    'cumulative_distance_km': round(current_distance / 0.621371, 1),
                    'cumulative_hours': round(current_hours + difference, 2),
                    'stop_duration': self.min_rest_hours,
                    'notes': f'10-hour rest after {current_cumulative_on_duty:.1f}h on-duty',
                    'cumulative_driving_today': current_cumulative_driving,
                    'cumulative_on_duty_today': current_cumulative_on_duty,
                    'cumulative_driving_since_break': current_cumulative_break,
                })

                current_cumulative_driving = 0
                current_cumulative_on_duty = 0
                current_cumulative_break = 0
                current_hours += self.min_rest_hours
        
        # Add metadata to the last stop
        if segment_stops:
            last_stop = segment_stops[-1]
            last_stop['cumulative_driving_today'] = current_cumulative_driving
            last_stop['cumulative_on_duty_today'] = current_cumulative_on_duty
            last_stop['cumulative_driving_since_break'] = current_cumulative_break
            last_stop['next_fuel_check'] = current_fuel_check
            last_stop['current_hours'] = current_hours


        return segment_stops
    
    def _add_real_location_names(self, stops: List[Dict], route_coordinates: List[List[float]]) -> List[Dict]:
        """Add real location names to stops by reverse geocoding approximate coordinates"""
        if not route_coordinates or len(route_coordinates) < 2:
            return stops
        
        enhanced_stops = []
        
        for stop in stops:
            # For START, PICKUP, DROPOFF - we already have real location names
            if stop['type'] in ['START', 'PICKUP', 'DROPOFF']:
                enhanced_stops.append(stop)
                continue
            
            # For other stops, estimate their coordinates along the route
            stop_progress = stop['cumulative_distance_miles'] / max(stop['cumulative_distance_miles'], 1)
            stop_index = min(int(stop_progress * len(route_coordinates)), len(route_coordinates) - 1)
            
            if stop_index < len(route_coordinates):
                # Get approximate coordinates
                approx_coords = route_coordinates[stop_index]
                
                # Try to get real location name (you might want to implement reverse geocoding)
                # For now, we'll use a descriptive name based on distance
                location_name = self._get_descriptive_location_name(
                    stop['type'], 
                    int(stop['cumulative_distance_miles'])
                )
                
                enhanced_stop = stop.copy()
                enhanced_stop['location'] = location_name
                enhanced_stop['approx_coordinates'] = approx_coords
                
                enhanced_stops.append(enhanced_stop)
            else:
                enhanced_stops.append(stop)
        
        return enhanced_stops
    
    def _assign_days_to_stops(self, stops: List[Dict]) -> List[Dict]:
        """
        Assign day numbers to stops based on cumulative hours.
        Day = floor(cumulative_hours / 24) + 1
        """
        if not stops:
            return []
        
        # Create a copy to avoid modifying original
        stops_with_days = []
        
        for stop in stops:
            # Calculate day number: floor(cumulative_hours / 24) + 1
            cumulative_hours = stop.get('cumulative_hours', 0)
            
            # Calculate day number (starting from 1)
            # Example: 
            # - 0-23.99 hours = Day 1
            # - 24-47.99 hours = Day 2
            # - 48-71.99 hours = Day 3, etc.
            day_number = int(cumulative_hours // 24) + 1
            
            # Calculate time within the day (0-24 hours)
            time_in_day = cumulative_hours % 24
            
            # Create stop with day information
            stop_with_day = stop.copy()
            stop_with_day['day'] = day_number
            stop_with_day['time_in_day'] = round(time_in_day, 2)  # Hours within the day (0-24)
            
            # Calculate approximate time of day
            hour_of_day = int(time_in_day)
            minute_of_day = int((time_in_day - hour_of_day) * 60)
            am_pm = "AM" if hour_of_day < 12 else "PM"
            display_hour = hour_of_day if hour_of_day <= 12 else hour_of_day - 12
            if display_hour == 0:
                display_hour = 12
                
            stop_with_day['time_of_day'] = f"{display_hour}:{minute_of_day:02d} {am_pm}"
            
            stops_with_days.append(stop_with_day)
        
        return stops_with_days
    
    def _get_descriptive_location_name(self, stop_type: str, distance_miles: int) -> str:
        """Generate descriptive location names for stops"""
        if stop_type == 'FUEL':
            return f"Fuel Station near mile {distance_miles}"
        elif stop_type == 'REST':
            return f"Rest Area at mile {distance_miles}"
        elif stop_type == 'OVERNIGHT':
            return f"Truck Stop at mile {distance_miles}"
        else:
            return f"Stop at mile {distance_miles}"
    
    def _generate_daily_logs_from_stops(self, stops: List[Dict], current_cycle_used: float) -> List[Dict]:
        """Generate daily logs based on actual stops, handling stops that span across days"""
        
        # Step 1: Split stops that span across day boundaries
        processed_stops = self._split_stops_across_days(stops)
        
        # Step 2: Group stops by day
        stops_by_day = {}
        for stop in processed_stops:
            day = stop['day']
            if day not in stops_by_day:
                stops_by_day[day] = []
            stops_by_day[day].append(stop)
        
        # Step 3: Generate daily logs
        daily_logs = []
        cycle_used = current_cycle_used
        
        for day_num in sorted(stops_by_day.keys()):
            day_stops = stops_by_day[day_num]
            day_stops.sort(key=lambda x: x.get('start_time_in_day', x.get('cumulative_hours', 0)))
            
            # Calculate statistics for the day
            day_stats = self._calculate_day_stats(day_stops, day_num, len(stops_by_day))
            
            # Generate schedule
            schedule = self._generate_daily_schedule(day_stops, day_num, len(stops_by_day))
            
            # Update cycle
            cycle_used += day_stats['total_on_duty']
            
            daily_log = {
                "day_number": day_num,
                "date": (datetime.now() + timedelta(days=day_num-1)),
                "driving_hours": round(day_stats['driving_hours'], 0),
                "on_duty_hours": round(day_stats['on_duty_not_driving'], 0),
                "off_duty_hours": round(day_stats['off_duty_hours'], 0),
                "sleeper_berth": round(day_stats['sleeper_berth'], 0),
                "cycle_used": round(cycle_used, 1),
                "requires_34_hour_restart": cycle_used >= 70.0,
                "stops_today": [f"{s['type']} ({s.get('duration_in_day', s['stop_duration']):.1f}h)" for s in day_stops],
                "schedule": schedule,
            }
            
            daily_logs.append(daily_log)
        
        return daily_logs

    def _split_stops_across_days(self, stops: List[Dict]) -> List[Dict]:
        """
        Split stops that span across day boundaries.
        A stop that starts on Day 1 at 23:00 and lasts 2 hours 
        should be split into:
        - Stop A: Day 1, 23:00-24:00 (1 hour)
        - Stop B: Day 2, 00:00-01:00 (1 hour)
        """
        processed_stops = []
        
        for stop in stops:
            cumulative_hours = stop.get('cumulative_hours', 0)
            stop_duration = stop.get('stop_duration', 0)
            
            # Calculate which day the stop starts on
            start_day = int(cumulative_hours // 24) + 1
            start_time_in_day = cumulative_hours % 24
            
            # Calculate end time
            end_hours = cumulative_hours + stop_duration
            end_day = int(end_hours // 24) + 1
            end_time_in_day = end_hours % 24
            
            # If stop doesn't span days, keep as is
            if start_day == end_day:
                processed_stop = stop.copy()
                processed_stop['day'] = start_day
                processed_stop['start_time_in_day'] = start_time_in_day
                processed_stop['end_time_in_day'] = end_time_in_day
                processed_stop['duration_in_day'] = stop_duration
                processed_stops.append(processed_stop)
            else:
                # Stop spans across days - split it
                # Part 1: On start day
                hours_on_start_day = 24 - start_time_in_day
                processed_stop_1 = stop.copy()
                processed_stop_1['day'] = start_day
                processed_stop_1['start_time_in_day'] = start_time_in_day
                processed_stop_1['end_time_in_day'] = 24.0  # End of day
                processed_stop_1['duration_in_day'] = hours_on_start_day
                processed_stop_1['is_split_part'] = True
                processed_stop_1['split_part'] = 1
                processed_stop_1['original_stop_duration'] = stop_duration
                processed_stops.append(processed_stop_1)
                
                # Part 2: On next day(s) - handle multi-day spans
                remaining_duration = stop_duration - hours_on_start_day
                current_day = start_day + 1
                current_start_time = 0.0
                
                while remaining_duration > 0:
                    # How many hours fit in this day
                    hours_this_day = min(24.0, remaining_duration)
                    
                    processed_stop_n = stop.copy()
                    processed_stop_n['day'] = current_day
                    processed_stop_n['start_time_in_day'] = current_start_time
                    processed_stop_n['end_time_in_day'] = current_start_time + hours_this_day
                    processed_stop_n['duration_in_day'] = hours_this_day
                    processed_stop_n['is_split_part'] = True
                    processed_stop_n['split_part'] = current_day - start_day + 1
                    processed_stop_n['original_stop_duration'] = stop_duration
                    
                    processed_stops.append(processed_stop_n)
                    
                    remaining_duration -= hours_this_day
                    current_day += 1
                    current_start_time = 0.0
        
        return processed_stops

    def _calculate_day_stats(self, day_stops: List[Dict], day_num: int, total_days: int) -> Dict:
        """Calculate HOS statistics for a day from stops, handling split stops"""
        if not day_stops:
            return {
                'driving_hours': 0,
                'on_duty_not_driving': 0,
                'total_on_duty': 0,
                'off_duty_hours': 24,
                'sleeper_berth': 0
            }
        
        # Sort stops by start time
        day_stops.sort(key=lambda x: x.get('start_time_in_day', 0))
        
        # Find driving time between stops
        driving_hours = 0
        on_duty_not_driving = 0
        sleeper_berth = 0
        
        # Calculate driving time between stops
        for i in range(len(day_stops) - 1):
            current = day_stops[i]
            next_stop = day_stops[i + 1]
            
            # Calculate time between end of current stop and start of next stop
            current_end = current.get('end_time_in_day', 
                                    current.get('start_time_in_day', 0) + current.get('duration_in_day', current.get('stop_duration', 0)))
            next_start = next_stop.get('start_time_in_day', 0)
            
            # If there's a gap between stops, it's driving time
            if next_start > current_end:
                driving_hours += (next_start - current_end)
        
        # Calculate on-duty not driving and sleeper berth from stop durations
        for stop in day_stops:
            stop_type = stop['type']
            duration_in_day = stop.get('duration_in_day', stop.get('stop_duration', 0))
            
            # For split stops, use the portion in this day
            if stop_type in ['PICKUP', 'DROPOFF', 'FUEL', 'REST']:
                on_duty_not_driving += duration_in_day
            elif stop_type == 'OVERNIGHT':
                # Overnight stops count toward sleeper berth time
                sleeper_berth += duration_in_day
        
        # # Add pre/post trip inspections (30 min total)
        # on_duty_not_driving += 0.5
        
        total_on_duty = driving_hours + on_duty_not_driving

        
        # Calculate total accounted time
        total_accounted = total_on_duty + sleeper_berth
        
        # Remaining time is off-duty
        off_duty_hours = max(0, 24 - total_accounted)
        
        # For last day, adjust sleeper time
        is_last_day = (day_num == total_days)
        if is_last_day and sleeper_berth > 0:
            # Ensure minimum 8 hours rest on last day if there's an overnight stop
            if sleeper_berth < 8:
                sleeper_berth = min(8, 24 - total_on_duty)
                off_duty_hours = max(0, 24 - total_on_duty - sleeper_berth)
        
        return {
            'driving_hours': driving_hours,
            'on_duty_not_driving': on_duty_not_driving,
            'total_on_duty': total_on_duty,
            'off_duty_hours': off_duty_hours,
            'sleeper_berth': sleeper_berth
        }

    def _generate_daily_schedule(self, day_stops: List[Dict], day_num: int, total_days: int) -> List[Dict]:
        """Generate a realistic 24-hour schedule for ELD display, handling split stops"""
        schedule = []
        current_time = 0.0
        is_last_day = (day_num == total_days)
        
        # Sort stops by start time
        day_stops.sort(key=lambda x: x.get('start_time_in_day', 0))
        
        # Handle start of day
        if day_num == 1:
            # First day starts at 6 AM
            if day_stops and day_stops[0].get('start_time_in_day', 6.0) < 6.0:
                current_time = day_stops[0].get('start_time_in_day', 0.0)
            else:
                current_time = 6.0
                
            if current_time > 0:
                schedule.append({
                    "status": "OFF",
                    "start": 0.0,
                    "end": current_time,
                    "remark": "Before trip start"
                })
        else:
            # Subsequent days start with sleeper berth from overnight
            current_time = 0.0
            # Check if we have an ongoing overnight stop from previous day
            ongoing_overnight = next((s for s in day_stops if s.get('is_split_part', False) and s['type'] in ['OVERNIGHT', 'OFF']), None)
            
            if ongoing_overnight:
                schedule.append({
                    "status": "SB" if ongoing_overnight['type'] == 'OVERNIGHT' else "OFF",
                    "start": 0.0,
                    "end": ongoing_overnight.get('end_time_in_day', 10.0),
                    "remark": ongoing_overnight.get('location',"Continuation of overnight rest" if ongoing_overnight.get('is_split_part') else "10-hour off-duty rest")
                })
                current_time = ongoing_overnight.get('end_time_in_day', 10.0)
            else:
                schedule.append({
                    "status": "SB",
                    "start": 0.0,
                    "end": 10.0,
                    "remark": day_stops[0].get('location',"10-hour sleeper berth rest")
                })
                current_time = 10.0
        
        # # Pre-trip inspection if we're starting driving activities
        # if current_time < 24.0 and not any(s['type'] == 'OVERNIGHT' for s in day_stops if s.get('start_time_in_day', 0) <= current_time):
        #     schedule.append({
        #         "status": "ON",
        #         "start": current_time,
        #         "end": current_time + 0.25,
        #         "remark": "Pre-trip inspection"
        #     })
        #     current_time += 0.25
        
        # Process stops for this day
        for stop in day_stops:
            stop_type = stop['type']
            start_time = stop.get('start_time_in_day', 0)
            duration = stop.get('duration_in_day', stop.get('stop_duration', 0))
            
            # Skip if this stop has already been accounted for (starts before current_time)
            if start_time < current_time:
                continue
                
            # If there's a gap before this stop, it's driving time
            if start_time > current_time:
                schedule.append({
                    "status": "D",
                    "start": current_time,
                    "end": start_time,
                    "remark": "Driving between stops"
                })
                current_time = start_time
            
            # Add the stop activity
            status = self._get_status_for_stop_type(stop_type)
            remark = self._get_remark_for_stop(stop, duration)
            
            schedule.append({
                "status": status,
                "start": current_time,
                "end": current_time + duration,
                "remark": remark
            })
            
            current_time += duration
            
            # # If this is an overnight stop that ends the day
            # if stop_type == 'OVERNIGHT' and not stop.get('is_split_part', False):
            #     break
        
        # If day doesn't end with overnight, fill remaining time
        if current_time < 24.0:
            if is_last_day:
                # # Post-trip on last day
                # schedule.append({
                #     "status": "ON",
                #     "start": current_time,
                #     "end": current_time + 0.25,
                #     "remark": "Post-trip inspection and paperwork"
                # })
                # current_time += 0.25
                
                if current_time < 24.0:
                    schedule.append({
                        "status": "OFF",
                        "start": current_time,
                        "end": 24.0,
                        "remark": "Trip complete - off duty"
                    })
            else:
                # Regular day - off-duty until next day
                schedule.append({
                    "status": "D",
                    "start": current_time,
                    "end": 24.0,
                    "remark": "Driving until end of day"
                })
        
        return schedule

    def _get_status_for_stop_type(self, stop_type: str) -> str:
        """Map stop type to ELD status"""
        status_map = {
            'START': 'D',
            'PICKUP': 'ON',
            'DROPOFF': 'ON',
            'FUEL': 'ON',
            'REST': 'ON',
            'OVERNIGHT': 'SB',
            'OFF': 'OFF'
        }
        return status_map.get(stop_type, 'ON')

    def _get_remark_for_stop(self, stop: Dict, duration: float) -> str:
        """Generate remark for stop in schedule"""
        stop_type = stop['type']
        location = stop.get('location', 'Unknown')
        
        if stop.get('is_split_part', False):
            part_num = stop.get('split_part', 1)
            if stop_type == 'OVERNIGHT':
                return f"Overnight rest continuation at {location} (Part {part_num}): {duration:.1f}h"
            elif stop_type == 'OFF':
                return f"Overnight rest continuation at {location} (Part {part_num}): {duration:.1f}h"
            else:
                return f"{stop_type} at {location} (Part {part_num}): {duration:.1f}h"
        
        remarks = {
            'START': f"Departing from {location}",
            'PICKUP': f"Loading at {location}: {duration:.1f}h",
            'DROPOFF': f"Unloading at {location}: {duration:.1f}h",
            'FUEL': f"Fueling at {location}: {duration:.1f}h",
            'REST': f"30-min break at {location}",
            'OVERNIGHT': f"Overnight rest at {location}: {duration:.1f}h"
        }
        
        return remarks.get(stop_type, f"{stop_type} at {location}: {duration:.1f}h")