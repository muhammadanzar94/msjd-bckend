from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from users.permissions import IsSystemAdmin
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


class UserListView(generics.ListAPIView):
    """System-admin-only: lists masjid admin accounts, e.g. for an
    approval queue. Filter with ?is_approved=true|false."""
    serializer_class = UserSerializer
    permission_classes = [IsSystemAdmin]

    def get_queryset(self):
        qs = User.objects.filter(role=User.Role.MASJID_ADMIN)
        is_approved = self.request.query_params.get('is_approved')
        if is_approved is not None:
            qs = qs.filter(is_approved=is_approved.lower() == 'true')
        return qs


class UserApprovalView(APIView):
    """System-admin-only endpoint to approve/reject a masjid admin account."""
    permission_classes = [IsSystemAdmin]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk, role=User.Role.MASJID_ADMIN)
        except User.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')  # 'approve' or 'reject'
        if action == 'approve':
            user.is_approved = True
            user.is_active = True
            user.save(update_fields=['is_approved', 'is_active'])
        elif action == 'reject':
            user.is_approved = False
            user.is_active = False
            user.save(update_fields=['is_approved', 'is_active'])
        else:
            return Response({'detail': "action must be 'approve' or 'reject'."}, status=400)

        return Response(UserSerializer(user).data)