# backend/eld_app/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse
import os
from datetime import datetime, timedelta
from django.conf import settings

from .pdf_service import PDFLogService
from .models import Trip, Stop, DailyLog, LogEntry
from .serializers import TripSerializer, TripInputSerializer
from .services import TripPlannerService
from .log_service import LogService  # For HTML preview


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer


def _generate_fmcsa_daily_logs(trip_data, request):
    """Generate FMCSA-compliant daily logs (PDF + HTML) and return URLs"""
    pdf_service = PDFLogService()
    log_service = LogService()
    planner = TripPlannerService()          # ← ADD THIS LINE
    daily_logs_data = []

    total_distance_km = trip_data['total_distance_km']
    total_duration_hours = trip_data['total_duration_hours']  # ← You already have this!
    total_distance_miles = total_distance_km * 0.621371
    num_days = len(trip_data['daily_logs']) if trip_data['daily_logs'] else 1
    daily_miles = total_distance_miles / num_days if num_days > 0 else 0

    # Ensure media folders exist
    pdf_dir = os.path.join(settings.MEDIA_ROOT, 'pdf_logs')
    html_dir = os.path.join(settings.MEDIA_ROOT, 'html_logs')
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)

    # Generate stops ONCE (outside the loop)
    stops = planner.generate_stops(total_distance_km, total_duration_hours)

    for i, day_log in enumerate(trip_data['daily_logs']):
        log_date = datetime.now() + timedelta(days=i)

        # Smart location names
        if i == 0:
            start_location = trip_data['form_data']['current_location']
            end_location = f"Enroute → {trip_data['form_data']['dropoff_location']}"
        elif i == len(trip_data['daily_logs']) - 1:
            start_location = f"Enroute → {trip_data['form_data']['dropoff_location']}"
            end_location = trip_data['form_data']['dropoff_location']
        else:
            start_location = f"Day {i+1} Rest Stop"
            end_location = f"Day {i+2} Rest Stop"

        # ←←← THIS IS THE MAGIC PART →→→
        remarks = planner._build_remarks_for_day(
            day_number=day_log['day_number'],
            stops=stops,
            trip_data=trip_data
        )

        day_specific_data = {
            'day_number': day_log['day_number'],
            'date': log_date,
            'miles_today': f"{daily_miles:.0f}",
            'total_mileage': f"{(i + 1) * daily_miles:.0f}",
            'driving_hours': float(day_log['driving_hours']),
            'on_duty_hours': float(day_log['on_duty_hours']),
            'off_duty_hours': float(day_log.get('off_duty_hours', 24 - day_log['on_duty_hours'])),
            'sleeper_hours': float(day_log.get('sleeper_hours', 10.0)),
            'cycle_used': float(day_log.get('cycle_used', 0)),
            'start_location': start_location,
            'end_location': end_location,
            'schedule': day_log.get('schedule', []),
            'remarks': remarks,                     # ← THIS GOES TO PDF!
        }

        # Generate filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f"fmcsa_log_day_{day_log['day_number']}_{timestamp}.pdf"
        html_filename = f"daily_log_day_{day_log['day_number']}_{timestamp}.html"
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        html_path = os.path.join(html_dir, html_filename)

        try:
            pdf_service.generate_fmcsa_daily_log(day_specific_data, trip_data, pdf_path)
            html_content = log_service.generate_html_daily_log(day_specific_data, trip_data)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            pdf_url = request.build_absolute_uri(f'/media/pdf_logs/{pdf_filename}')
            html_url = request.build_absolute_uri(f'/media/html_logs/{html_filename}')

            daily_logs_data.append({
                'day_number': day_log['day_number'],
                'date': log_date.strftime('%m/%d/%Y'),
                'pdf_url': pdf_url,
                'html_url': html_url,
                'remarks': remarks,  # ← Show in response too!
                'miles_today': f"{daily_miles:.0f}",
            })
        except Exception as e:
            print(f"Error generating log for day {day_log['day_number']}: {e}")
            daily_logs_data.append({'day_number': day_log['day_number'], 'error': str(e)})

    return daily_logs_data

@api_view(['POST'])
def plan_trip(request):
    serializer = TripInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    input_data = serializer.validated_data

    planner = TripPlannerService()
    result = planner.plan_trip(
        current_location=input_data['current_location'],
        pickup_location=input_data['pickup_location'],
        dropoff_location=input_data['dropoff_location'],
        current_cycle_used=float(input_data['current_cycle_used'])
    )

    # Inject form data for headers/remarks
    result['form_data'] = {
        'current_location': input_data['current_location'],
        'pickup_location': input_data['pickup_location'],
        'dropoff_location': input_data['dropoff_location'],
        'main_office_address': f"123 Main Terminal Rd, {input_data['current_location']}",
        'home_terminal_address': f"456 Home Base Ave, {input_data['current_location']}",
        'vehicle_numbers': "Truck: 8899 | Trailer: 1122",
        'commodity': "General Freight",
    }

    # Generate real FMCSA logs
    result['fmcsa_daily_logs'] = _generate_fmcsa_daily_logs(result, request)

    return Response(result, status=status.HTTP_200_OK)


# Download PDF
@api_view(['GET'])
def download_pdf(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, 'pdf_logs', filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    return Response({"error": "PDF not found"}, status=404)


# View HTML log in browser
@api_view(['GET'])
def view_html_log(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, 'html_logs', filename)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    return Response({"error": "HTML log not found"}, status=404)

# ADD THIS FUNCTION TO YOUR views.py (anywhere after the other @api_view functions)
@api_view(['GET'])
def get_day_logs(request, day_number, trip_id=None):
    """
    Return the latest generated PDF + HTML log URLs for a specific day_number
    (useful when you only want to fetch logs without re-planning the whole trip)
    """
    pdf_dir = os.path.join(settings.MEDIA_ROOT, 'pdf_logs')
    html_dir = os.path.join(settings.MEDIA_ROOT, 'html_logs')

    # Find the most recent files that match the day number
    try:
        pdf_files = sorted(
            [f for f in os.listdir(pdf_dir) if f.startswith(f'fmcsa_log_day_{day_number}_')],
            reverse=True
        )
        html_files = sorted(
            [f for f in os.listdir(html_dir) if f.startswith(f'daily_log_day_{day_number}_')],
            reverse=True
        )

        if not pdf_files:
            return Response({"error": f"No log found for day {day_number}"}, status=404)

        pdf_filename = pdf_files[0]
        html_filename = html_files[0] if html_files else None

        return Response({
            "day_number": day_number,
            "pdf_url": request.build_absolute_uri(f'/media/pdf_logs/{pdf_filename}'),
            "html_url": request.build_absolute_uri(f'/media/html_logs/{html_filename}') if html_filename else None,
            "pdf_filename": pdf_filename,
            "html_filename": html_filename,
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)