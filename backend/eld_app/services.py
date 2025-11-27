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
    
    def geocode_location(self, location_name):
        """Convert location name to coordinates"""
        # Mock geocoding - in production, use Google Geocoding API or similar
        geocodes = {
            'new york, ny': (-74.006, 40.7128),
            'chicago, il': (-87.6298, 41.8781),
            'los angeles, ca': (-118.2437, 34.0522),
            'philadelphia, pa': (-75.1652, 39.9526),
            'houston, tx': (-95.3698, 29.7604),
            'phoenix, az': (-112.0740, 33.4484),
        }
        
        clean_name = location_name.lower().strip()
        return geocodes.get(clean_name, (-98.5795, 39.8283))  # Default to US center
    
    def calculate_distance(self, loc1: str, loc2: str) -> float:
        """Use real routing service for accurate distances"""
        coords1 = self.geocode_location(loc1)
        coords2 = self.geocode_location(loc2)
        
        route_data = self.map_service.get_route(coords1, coords2)
        return route_data['distance_km']
    
    def plan_trip(self, current_location: str, pickup_location: str, 
             dropoff_location: str, current_cycle_used: float) -> Dict:
    
        # Get coordinates for all locations
        start_coords = self.geocode_location(current_location)
        pickup_coords = self.geocode_location(pickup_location)
        end_coords = self.geocode_location(dropoff_location)
        
        # Get route from current to pickup
        to_pickup_route = self.map_service.get_route(start_coords, pickup_coords)
        
        # Get route from pickup to dropoff  
        to_dropoff_route = self.map_service.get_route(pickup_coords, end_coords)
        
        # Combine routes for the full journey
        full_route_coordinates = (
            to_pickup_route['coordinates'] + 
            to_dropoff_route['coordinates'][1:]  # Avoid duplicate point at pickup
        )
        
        total_distance = to_pickup_route['distance_km'] + to_dropoff_route['distance_km']
        total_duration = to_pickup_route['duration_hours'] + to_dropoff_route['duration_hours']
        
        # Generate stops and logs (your existing code)
        stops = self.generate_stops(total_distance, total_duration)
        daily_logs = self.generate_daily_logs(total_duration, current_cycle_used)
        
        return {
            'total_distance_km': round(total_distance, 2),
            'total_duration_hours': round(total_duration, 2),
            'stops': stops,
            'daily_logs': daily_logs,
            'route_coordinates': full_route_coordinates,  # This is crucial for the map!
            'route': {
                'current_to_pickup': {
                    'distance': round(to_pickup_route['distance_km'], 2),
                    'duration': round(to_pickup_route['duration_hours'], 2)
                },
                'pickup_to_dropoff': {
                    'distance': round(to_dropoff_route['distance_km'], 2),
                    'duration': round(to_dropoff_route['duration_hours'], 2)
                }
            }
        }

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
    
    def _build_remarks_for_day(self, day_number: int, stops: List[Dict], trip_data: dict) -> List[Dict]:
        """
        Generate realistic, DOT-inspection-proof remarks for a specific day
        Returns a list of objects with keys: type, location, start, end, and optional metadata.
        """
        remarks = []
        pickup_city = trip_data['form_data'].get('pickup_location', 'Pickup').split(',')[0]
        dropoff_city = trip_data['form_data'].get('dropoff_location', 'Dropoff').split(',')[0]

        daily_logs = trip_data.get('daily_logs', [])
        day_log = daily_logs[day_number - 1] if daily_logs and len(daily_logs) >= day_number else None

        # stops that fall on this day
        day_stops = [
            s for s in stops
            if self._is_stop_in_day(s, day_number, daily_logs)
        ]

        # helper: convert fractional hours to HH:MM (24h)
        def hour_to_hm(h: float) -> str:
            h_mod = h % 24
            hh = int(math.floor(h_mod))
            mm = int(round((h_mod - hh) * 60))
            if mm == 60:
                hh = (hh + 1) % 24
                mm = 0
            return f"{hh:02d}:{mm:02d}"

        # compute driving hours completed before this day
        prev_driving = 0.0
        if daily_logs:
            prev_driving = sum(d.get('driving_hours', 0.0) for d in daily_logs[:day_number - 1])

        # Estimate wall-clock start/end times for a stop using the day's schedule and the stop's cumulative driving time.
        def estimate_start_end(stop: Dict):
            target_in_day = stop.get('duration', 0.0) - prev_driving
            if target_in_day < 0:
                target_in_day = 0.0

            if not day_log or 'schedule' not in day_log:
                # Fallback: place relative to midnight
                start = target_in_day
                end = start + stop.get('stop_duration', 0.0)
                return hour_to_hm(start), hour_to_hm(end)

            driving_acc = 0.0
            for seg in day_log['schedule']:
                if seg.get('status') == 'D':
                    seg_len = max(0.0, seg.get('end', 0.0) - seg.get('start', 0.0))
                    if driving_acc + seg_len + 1e-6 >= target_in_day:
                        offset = max(0.0, target_in_day - driving_acc)
                        start_time = seg.get('start', 0.0) + offset
                        end_time = start_time + stop.get('stop_duration', 0.0)
                        return hour_to_hm(start_time), hour_to_hm(end_time)
                    driving_acc += seg_len

            # If we didn't find a matching driving segment, place at the last schedule end
            last_end = day_log['schedule'][-1].get('end', 24.0)
            start = last_end
            end = start + stop.get('stop_duration', 0.0)
            return hour_to_hm(start), hour_to_hm(end)

        # Build structured remark objects for each stop on this day
        for stop in day_stops:
            start_hm, end_hm = estimate_start_end(stop)
            distance_miles = int(stop.get('distance', 0.0) * 0.621371)
            approx_hour = int(stop.get('duration', 0.0))

            if stop['type'] == 'PICKUP':
                remarks.append({
                    'type': 'PICKUP',
                    'location': pickup_city,
                    'start': start_hm,
                    'end': end_hm,
                    'note': 'Pickup completed'
                })

            elif stop['type'] == 'FUEL':
                city = self._guess_city_at_distance(stop['distance'], trip_data)
                remarks.append({
                    'type': 'FUEL',
                    'location': city,
                    'start': start_hm,
                    'end': end_hm,
                    'distance_miles': distance_miles,
                    'note': f"Fuel stop near {city}"
                })

            elif stop['type'] == 'REST':
                remarks.append({
                    'type': 'REST',
                    'location': f"~{distance_miles} mi marker",
                    'start': start_hm,
                    'end': end_hm,
                    'after_driving_hours': approx_hour,
                    'note': '30-min required break'
                })

            elif stop['type'] == 'OVERNIGHT':
                city = self._guess_city_at_distance(stop['distance'], trip_data)
                remarks.append({
                    'type': 'OVERNIGHT',
                    'location': city,
                    'start': start_hm,
                    'end': end_hm,
                    'note': '10-hr reset/overnight'
                })

            elif stop['type'] == 'DROPOFF':
                remarks.append({
                    'type': 'DROPOFF',
                    'location': dropoff_city,
                    'start': start_hm,
                    'end': end_hm,
                    'note': 'Delivered - BOL signed'
                })

        # Add extra realism as structured entries where applicable
        if any(s['type'] == 'REST' for s in day_stops):
            first_rest = next((s for s in day_stops if s['type'] == 'REST'), None)
            if first_rest:
                s, e = estimate_start_end(first_rest)
                remarks.append({
                    'type': 'BREAK',
                    'location': f"~{int(first_rest.get('distance',0.0)*0.621371)} mi marker",
                    'start': s,
                    'end': e,
                    'note': 'Required 30-min break'
                })
            else:
                remarks.append({
                    'type': 'BREAK',
                    'location': None,
                    'start': None,
                    'end': None,
                    'note': 'Required 30-min break'
                })

        if day_number == 1:
            # Pre-trip inspection — structured entry
            if day_log and day_log.get('schedule'):
                pre = day_log['schedule'][0]
                remarks.append({
                    'type': 'PRETRIP',
                    'location': pickup_city,
                    'start': hour_to_hm(pre.get('start', 0.0)),
                    'end': hour_to_hm(pre.get('end', 0.5)),
                    'note': 'Pre-trip inspection completed'
                })
            else:
                remarks.append({
                    'type': 'PRETRIP',
                    'location': pickup_city,
                    'start': None,
                    'end': None,
                    'note': 'Pre-trip inspection completed'
                })

        if any(s['type'] == 'DROPOFF' for s in day_stops):
            last_drop = next((s for s in reversed(day_stops) if s['type'] == 'DROPOFF'), None)
            if last_drop:
                s, e = estimate_start_end(last_drop)
                remarks.append({
                    'type': 'POSTTRIP',
                    'location': dropoff_city,
                    'start': s,
                    'end': e,
                    'note': 'Post-trip inspection completed'
                })
            else:
                remarks.append({
                    'type': 'POSTTRIP',
                    'location': dropoff_city,
                    'start': None,
                    'end': None,
                    'note': 'Post-trip inspection completed'
                })

        return remarks
    
    def _is_stop_in_day(self, stop: Dict, day_number: int, daily_logs: List[Dict]) -> bool:
        """Return True if stop falls within this day's driving window"""
        if not daily_logs:
            return day_number == 1

        day_log = daily_logs[day_number - 1]
        total_hours_so_far = sum(d['driving_hours'] + d.get('on_duty_hours', 0) - d.get('driving_hours', 0) 
                                for d in daily_logs[:day_number-1])

        day_start_hour = total_hours_so_far
        day_end_hour = total_hours_so_far + day_log['driving_hours'] + 2  # + on-duty buffer

        return day_start_hour <= stop['duration'] <= day_end_hour

    def _guess_city_at_distance(self, distance_km: float, trip_data: dict) -> str:
        """Super simple but insanely effective city guesser"""
        total = trip_data['total_distance_km']
        ratio = distance_km / total

        start = trip_data['form_data']['current_location'].split(',')[0]
        end = trip_data['form_data']['dropoff_location'].split(',')[0]

        # Major cities along common routes (you can expand this list)
        waypoints = {
            0.2: "Gary, IN",
            0.3: "South Bend, IN",
            0.4: "Toledo, OH",
            0.5: "Cleveland, OH",
            0.7: "St. Louis, MO",
            0.8: "Springfield, MO",
            0.9: "Oklahoma City, OK",
        }

        for threshold, city in sorted(waypoints.items(), reverse=True):
            if ratio >= threshold:
                return city

        return f"~{int(distance_km * 0.621371)} mi marker" if ratio < 0.95 else end