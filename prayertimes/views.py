from rest_framework import generics
from masjids.models import Masjid
from users.permissions import IsSystemAdminOrOwnMasjidAdmin
from .models import PrayerTimetable, JummaTime
from .serializers import PrayerTimetableSerializer, JummaTimeSerializer


class PrayerTimetableListCreateView(generics.ListCreateAPIView):
    serializer_class = PrayerTimetableSerializer
    permission_classes = [IsSystemAdminOrOwnMasjidAdmin]

    def get_queryset(self):
        qs = PrayerTimetable.objects.filter(masjid_id=self.kwargs['masjid_id'])
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')
        if start:
            qs = qs.filter(date__gte=start)
        if end:
            qs = qs.filter(date__lte=end)
        return qs

    def perform_create(self, serializer):
        masjid = Masjid.objects.get(pk=self.kwargs['masjid_id'])
        self.check_object_permissions(self.request, masjid)
        serializer.save(masjid=masjid)


class PrayerTimetableDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PrayerTimetableSerializer
    permission_classes = [IsSystemAdminOrOwnMasjidAdmin]
    queryset = PrayerTimetable.objects.all()


class JummaTimeListCreateView(generics.ListCreateAPIView):
    serializer_class = JummaTimeSerializer
    permission_classes = [IsSystemAdminOrOwnMasjidAdmin]

    def get_queryset(self):
        return JummaTime.objects.filter(masjid_id=self.kwargs['masjid_id'])

    def perform_create(self, serializer):
        masjid = Masjid.objects.get(pk=self.kwargs['masjid_id'])
        self.check_object_permissions(self.request, masjid)
        serializer.save(masjid=masjid)


class JummaTimeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JummaTimeSerializer
    permission_classes = [IsSystemAdminOrOwnMasjidAdmin]
    queryset = JummaTime.objects.all()