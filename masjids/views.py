from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from users.permissions import IsSystemAdmin, IsSystemAdminOrOwnMasjidAdmin
from .models import Masjid, MasjidTheme, DonationDetail, MasjidImage
from .serializers import (
    MasjidSerializer, MasjidCreateSerializer,
    MasjidThemeSerializer, DonationDetailSerializer, MasjidImageSerializer,
)


class MasjidListCreateView(generics.ListCreateAPIView):
    """
    GET  -> system admin sees all masjids; masjid admin sees only their own
    POST -> masjid admin creates their masjid (must be approved user, and must not already have one)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'system_admin':
            return Masjid.objects.all()
        return Masjid.objects.filter(id=user.masjid_id) if user.masjid_id else Masjid.objects.none()

    def get_serializer_class(self):
        return MasjidCreateSerializer if self.request.method == 'POST' else MasjidSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != 'masjid_admin' or not user.is_approved:
            raise PermissionDenied('Only approved masjid admins can create a masjid.')
        if user.masjid_id:
            raise PermissionDenied('You already manage a masjid.')
        serializer.save()


class MasjidDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Masjid.objects.all()
    serializer_class = MasjidSerializer
    permission_classes = [IsSystemAdminOrOwnMasjidAdmin]


class MasjidApprovalView(APIView):
    """System-admin-only endpoint to approve/reject a masjid."""
    permission_classes = [IsSystemAdmin]

    def post(self, request, pk):
        try:
            masjid = Masjid.objects.get(pk=pk)
        except Masjid.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')  # 'approve' or 'reject'
        if action == 'approve':
            masjid.status = Masjid.Status.APPROVED
        elif action == 'reject':
            masjid.status = Masjid.Status.REJECTED
        else:
            return Response({'detail': "action must be 'approve' or 'reject'."}, status=400)

        masjid.save(update_fields=['status'])
        return Response(MasjidSerializer(masjid, context={'request': request}).data)


class MasjidThemeUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = MasjidThemeSerializer
    permission_classes = [IsSystemAdminOrOwnMasjidAdmin]

    def get_object(self):
        masjid = Masjid.objects.get(pk=self.kwargs['masjid_id'])
        self.check_object_permissions(self.request, masjid)
        theme, _ = MasjidTheme.objects.get_or_create(masjid=masjid)
        return theme


class DonationDetailListCreateView(generics.ListCreateAPIView):
    serializer_class = DonationDetailSerializer
    permission_classes = [IsSystemAdminOrOwnMasjidAdmin]

    def get_queryset(self):
        return DonationDetail.objects.filter(masjid_id=self.kwargs['masjid_id'])

    def perform_create(self, serializer):
        masjid = Masjid.objects.get(pk=self.kwargs['masjid_id'])
        self.check_object_permissions(self.request, masjid)
        serializer.save(masjid=masjid)


class DonationDetailDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DonationDetailSerializer
    permission_classes = [IsSystemAdminOrOwnMasjidAdmin]
    queryset = DonationDetail.objects.all()


class MasjidImageListCreateView(generics.ListCreateAPIView):
    serializer_class = MasjidImageSerializer
    permission_classes = [IsSystemAdminOrOwnMasjidAdmin]

    def get_queryset(self):
        return MasjidImage.objects.filter(masjid_id=self.kwargs['masjid_id'])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['masjid'] = Masjid.objects.get(pk=self.kwargs['masjid_id'])
        return context

    def perform_create(self, serializer):
        masjid = Masjid.objects.get(pk=self.kwargs['masjid_id'])
        self.check_object_permissions(self.request, masjid)
        serializer.save(masjid=masjid)


class MasjidImageDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = MasjidImageSerializer
    permission_classes = [IsSystemAdminOrOwnMasjidAdmin]
    queryset = MasjidImage.objects.all()


@method_decorator(ratelimit(key='ip', rate='20/m', method='GET', block=True), name='get')
class PublicMasjidDetailView(APIView):
    """Guest-facing endpoint — masjid is resolved from the request's
    subdomain by TenantMiddleware. Only serves approved masjids."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        masjid = request.masjid
        if masjid is None or masjid.status != Masjid.Status.APPROVED:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(MasjidSerializer(masjid, context={'request': request}).data)


@method_decorator(ratelimit(key='ip', rate='20/m', method='GET', block=True), name='get')
class PublicDemoMasjidView(APIView):
    """Guest-facing endpoint returning the slug of the first masjid ever
    approved on the platform — used for the marketing site's 'live demo' link
    so it doesn't need to be hardcoded to one mosque."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        masjid = Masjid.objects.filter(status=Masjid.Status.APPROVED).order_by('created_at').first()
        if masjid is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'slug': masjid.slug})