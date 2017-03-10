from django.contrib import admin

from .models import DataSource, EventType, Location, Vehicle


class LocationAdmin(admin.ModelAdmin):
    list_display = ('coords', 'vehicle')


admin.site.register(DataSource)
admin.site.register(EventType)
admin.site.register(Location, LocationAdmin)
admin.site.register(Vehicle)
