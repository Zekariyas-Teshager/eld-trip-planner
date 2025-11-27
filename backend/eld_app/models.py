from django.db import models

class Trip(models.Model):
    current_location = models.CharField(max_length=255)
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    current_cycle_used = models.DecimalField(max_digits=5, decimal_places=2)  # hours
    total_distance = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    total_duration = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Trip: {self.current_location} to {self.dropoff_location}"

class Stop(models.Model):
    STOP_TYPES = [
        ('FUEL', 'Fuel Stop'),
        ('REST', 'Rest Break'),
        ('PICKUP', 'Pickup'),
        ('DROPOFF', 'Dropoff'),
        ('OVERNIGHT', 'Overnight Rest'),
    ]
    
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='stops')
    stop_type = models.CharField(max_length=20, choices=STOP_TYPES)
    location = models.CharField(max_length=255)
    distance_from_start = models.DecimalField(max_digits=8, decimal_places=2)
    duration_from_start = models.DecimalField(max_digits=6, decimal_places=2)
    stop_duration = models.DecimalField(max_digits=4, decimal_places=2)  # hours
    
    def __str__(self):
        return f"{self.get_stop_type_display()} at {self.location}"

class DailyLog(models.Model):
    STATUS_CHOICES = [
        ('OFF', 'Off Duty'),
        ('SB', 'Sleeper Berth'),
        ('D', 'Driving'),
        ('ON', 'On Duty Not Driving'),
    ]
    
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='logs')
    day_number = models.IntegerField()
    date = models.DateField()
    total_miles = models.DecimalField(max_digits=6, decimal_places=2)
    
    def __str__(self):
        return f"Day {self.day_number} - {self.date}"

class LogEntry(models.Model):
    daily_log = models.ForeignKey(DailyLog, on_delete=models.CASCADE, related_name='entries')
    status = models.CharField(max_length=3, choices=DailyLog.STATUS_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=255)
    remarks = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.get_status_display()} - {self.start_time} to {self.end_time}"