from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Trip, Stop, DailyLog, LogEntry
from .serializers import TripSerializer, TripInputSerializer
from .services import TripPlannerService

class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer

@api_view(['POST'])
def plan_trip(request):
    serializer = TripInputSerializer(data=request.data)
    if serializer.is_valid():
        trip_data = serializer.validated_data
        
        # Use the trip planner service to calculate route and HOS compliance
        trip_planner = TripPlannerService()
        result = trip_planner.plan_trip(
            current_location=trip_data['current_location'],
            pickup_location=trip_data['pickup_location'],
            dropoff_location=trip_data['dropoff_location'],
            current_cycle_used=float(trip_data['current_cycle_used'])
        )
        
        return Response(result, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)