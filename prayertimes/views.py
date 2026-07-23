import datetime

from django.utils import timezone
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from masjids.models import Masjid
from users.permissions import IsSystemAdminOrOwnMasjidAdmin
from .bulk_upload import parse_bulk_upload
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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['masjid_id'] = self.kwargs['masjid_id']
        return context

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


class PrayerTimetableBulkUploadView(APIView):
    """POST a CSV/XLSX file to bulk create/update a masjid's timetable."""
    parser_classes = [MultiPartParser]
    permission_classes = [IsSystemAdminOrOwnMasjidAdmin]

    def post(self, request, masjid_id):
        try:
            masjid = Masjid.objects.get(pk=masjid_id)
        except Masjid.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, masjid)

        upload = request.FILES.get('file')
        if not upload:
            return Response({'detail': "No file provided (expected form field 'file')."}, status=400)

        try:
            summary = parse_bulk_upload(upload, masjid)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)

        return Response(summary)


@method_decorator(ratelimit(key='ip', rate='20/m', method='GET', block=True), name='get')
class PublicMasjidTimetableView(APIView):
    """Guest-facing endpoint — masjid is resolved from the request's
    subdomain by TenantMiddleware. Defaults to today -> +30 days."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        masjid = request.masjid
        if masjid is None or masjid.status != Masjid.Status.APPROVED:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        today = timezone.localdate()
        start = request.query_params.get('start') or today
        end = request.query_params.get('end') or (today + datetime.timedelta(days=30))

        timetable = PrayerTimetable.objects.filter(masjid=masjid, date__gte=start, date__lte=end)
        jumma_times = JummaTime.objects.filter(masjid=masjid, date__gte=start, date__lte=end)

        return Response({
            'timetable': PrayerTimetableSerializer(timetable, many=True).data,
            'jumma_times': JummaTimeSerializer(jumma_times, many=True).data,
        })