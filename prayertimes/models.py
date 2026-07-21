from django.db import models
from core.models import TimeStampedModel
from masjids.models import Masjid


class PrayerTimetable(TimeStampedModel):
    masjid = models.ForeignKey(Masjid, on_delete=models.CASCADE, related_name='timetables')
    date = models.DateField()

    fajr_start = models.TimeField()
    fajr_jamaat = models.TimeField()
    duhr_start = models.TimeField()
    duhr_jamaat = models.TimeField()
    asr_start = models.TimeField()
    asr_jamaat = models.TimeField()
    maghrib_start = models.TimeField()
    maghrib_jamaat = models.TimeField()
    isha_start = models.TimeField()
    isha_jamaat = models.TimeField()

    sunrise = models.TimeField(null=True, blank=True)
    sunset = models.TimeField(null=True, blank=True)
    noon = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ('masjid', 'date')
        ordering = ['date']

    def __str__(self):
        return f'{self.masjid.name} — {self.date}'


class JummaTime(TimeStampedModel):
    masjid = models.ForeignKey(Masjid, on_delete=models.CASCADE, related_name='jumma_times')
    date = models.DateField()
    khutbah_start = models.TimeField()
    jamaat_time = models.TimeField()

    class Meta:
        ordering = ['date', 'jamaat_time']

    def __str__(self):
        return f'Jumma {self.masjid.name} — {self.date} ({self.jamaat_time})'