from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    MasjidAdminRegisterView, CustomTokenObtainPairView, MeView,
    UserListView, UserApprovalView,
)

urlpatterns = [
    path('register/', MasjidAdminRegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/approval/', UserApprovalView.as_view(), name='user-approval'),
]