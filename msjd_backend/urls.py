from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from masjids.views import PublicMasjidDetailView, PublicDemoMasjidView
from prayertimes.views import PublicMasjidTimetableView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/masjids/', include('masjids.urls')),
    path('api/prayertimes/', include('prayertimes.urls')),
    path('api/public/masjid/', PublicMasjidDetailView.as_view(), name='public-masjid-detail'),
    path('api/public/masjid/timetable/', PublicMasjidTimetableView.as_view(), name='public-masjid-timetable'),
    path('api/public/masjids/demo/', PublicDemoMasjidView.as_view(), name='public-demo-masjid'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)