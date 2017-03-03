from django.contrib import admin

from .models import DataSource, EventType, Location, Vehicle

admin.site.register(DataSource)
admin.site.register(EventType)
admin.site.register(Location)
admin.site.register(Vehicle)
