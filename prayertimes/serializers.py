from rest_framework import serializers
from .models import PrayerTimetable, JummaTime


class PrayerTimetableSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrayerTimetable
        fields = (
            'id', 'masjid', 'date',
            'fajr_start', 'fajr_jamaat',
            'duhr_start', 'duhr_jamaat',
            'asr_start', 'asr_jamaat',
            'maghrib_start', 'maghrib_jamaat',
            'isha_start', 'isha_jamaat',
            'sunrise', 'sunset', 'noon',
            'created_at', 'updated_at',
        )
        read_only_fields = ('masjid',)


class JummaTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = JummaTime
        fields = ('id', 'masjid', 'date', 'khutbah_start', 'jamaat_time')
        read_only_fields = ('masjid',)