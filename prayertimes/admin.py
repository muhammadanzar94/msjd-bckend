from django.contrib import admin
from .models import PrayerTimetable, JummaTime


@admin.register(PrayerTimetable)
class PrayerTimetableAdmin(admin.ModelAdmin):
    list_display = ('masjid', 'date', 'fajr_jamaat', 'duhr_jamaat', 'asr_jamaat', 'maghrib_jamaat', 'isha_jamaat')
    list_filter = ('masjid',)
    date_hierarchy = 'date'


@admin.register(JummaTime)
class JummaTimeAdmin(admin.ModelAdmin):
    list_display = ('masjid', 'date', 'khutbah_start', 'jamaat_time')
    list_filter = ('masjid',)