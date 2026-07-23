from django.urls import path
from .views import (
    PrayerTimetableListCreateView, PrayerTimetableDetailView,
    JummaTimeListCreateView, JummaTimeDetailView,
    PrayerTimetableBulkUploadView,
)

urlpatterns = [
    path('<int:masjid_id>/', PrayerTimetableListCreateView.as_view(), name='timetable-list-create'),
    path('entry/<int:pk>/', PrayerTimetableDetailView.as_view(), name='timetable-detail'),
    path('<int:masjid_id>/jumma/', JummaTimeListCreateView.as_view(), name='jumma-list-create'),
    path('jumma/<int:pk>/', JummaTimeDetailView.as_view(), name='jumma-detail'),
    path('<int:masjid_id>/bulk-upload/', PrayerTimetableBulkUploadView.as_view(), name='timetable-bulk-upload'),
]