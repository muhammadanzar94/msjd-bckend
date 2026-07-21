from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import MasjidAdminRegisterSerializer, UserSerializer, CustomTokenObtainPairSerializer


class MasjidAdminRegisterView(generics.CreateAPIView):
    """Public signup — creates an unapproved masjid admin account."""
    queryset = User.objects.all()
    serializer_class = MasjidAdminRegisterSerializer
    permission_classes = [permissions.AllowAny]


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user