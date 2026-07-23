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

    def validate(self, attrs):
        # `masjid` is read-only (assigned by the view), so DRF's automatic
        # UniqueTogetherValidator on (masjid, date) never fires — check it
        # here instead, otherwise a duplicate date hits the DB constraint
        # directly and surfaces as a 500.
        masjid_id = self.context.get('masjid_id') or (self.instance.masjid_id if self.instance else None)
        date = attrs.get('date', self.instance.date if self.instance else None)
        if masjid_id and date:
            qs = PrayerTimetable.objects.filter(masjid_id=masjid_id, date=date)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {'date': 'A timetable entry for this masjid and date already exists.'}
                )
        return attrs


class JummaTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = JummaTime
        fields = ('id', 'masjid', 'date', 'khutbah_start', 'jamaat_time')
        read_only_fields = ('masjid',)