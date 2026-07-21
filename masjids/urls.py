from django.urls import path
from .views import (
    MasjidListCreateView, MasjidDetailView, MasjidApprovalView,
    MasjidThemeUpdateView, DonationDetailListCreateView, DonationDetailDetailView,
    MasjidImageListCreateView, MasjidImageDetailView,
)

urlpatterns = [
    path('', MasjidListCreateView.as_view(), name='masjid-list-create'),
    path('<int:pk>/', MasjidDetailView.as_view(), name='masjid-detail'),
    path('<int:pk>/approval/', MasjidApprovalView.as_view(), name='masjid-approval'),
    path('<int:masjid_id>/theme/', MasjidThemeUpdateView.as_view(), name='masjid-theme'),
    path('<int:masjid_id>/donations/', DonationDetailListCreateView.as_view(), name='donation-list-create'),
    path('donations/<int:pk>/', DonationDetailDetailView.as_view(), name='donation-detail'),
    path('<int:masjid_id>/images/', MasjidImageListCreateView.as_view(), name='image-list-create'),
    path('images/<int:pk>/', MasjidImageDetailView.as_view(), name='image-detail'),
]