from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from core.fields import AbsoluteFileField, AbsoluteImageField
from users.models import User
from .models import Masjid, MasjidTheme, DonationDetail, MasjidImage


class MasjidThemeSerializer(serializers.ModelSerializer):
    background_image = AbsoluteImageField(required=False, allow_null=True)

    class Meta:
        model = MasjidTheme
        fields = ('id', 'primary_color', 'secondary_color', 'font_family', 'background_image')


class DonationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonationDetail
        fields = ('id', 'bank_name', 'account_name', 'account_number', 'sort_code', 'iban', 'notes')


class MasjidImageSerializer(serializers.ModelSerializer):
    image = AbsoluteImageField()

    class Meta:
        model = MasjidImage
        fields = ('id', 'image', 'order')

    def validate(self, attrs):
        masjid = self.context['masjid']
        if not self.instance and masjid.images.count() >= 4:
            raise serializers.ValidationError('A masjid can have a maximum of 4 images.')
        return attrs


class MasjidSerializer(serializers.ModelSerializer):
    theme = MasjidThemeSerializer(read_only=True)
    donation_details = DonationDetailSerializer(many=True, read_only=True)
    images = MasjidImageSerializer(many=True, read_only=True)
    logo = AbsoluteImageField(required=False, allow_null=True)
    intro_video = AbsoluteFileField(required=False, allow_null=True)

    class Meta:
        model = Masjid
        fields = (
            'id', 'name', 'slug', 'address', 'city', 'country', 'postcode',
            'phone', 'email', 'firqa', 'google_maps_link', 'latitude', 'longitude',
            'timezone', 'logo', 'intro_video', 'status',
            'theme', 'donation_details', 'images',
            'created_at', 'updated_at',
        )
        read_only_fields = ('status',)  # only system admin approves, via separate endpoint


class MasjidCreateSerializer(serializers.ModelSerializer):
    """Used on creation. A masjid admin submits this for their own masjid
    (status starts pending, awaiting system-admin approval, and it's linked
    to the submitting user). A system admin can also use this to create a
    masjid directly — it's approved immediately since a system admin is
    vouching for it, and they can optionally create + link a masjid_admin
    account for it in the same request via the admin_* fields."""

    logo = AbsoluteImageField(required=False, allow_null=True)
    intro_video = AbsoluteFileField(required=False, allow_null=True)

    admin_username = serializers.CharField(write_only=True, required=False, allow_blank=True)
    admin_email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    admin_phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    admin_password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Masjid
        fields = (
            'id', 'name', 'slug', 'address', 'city', 'country', 'postcode',
            'phone', 'email', 'firqa', 'google_maps_link', 'latitude', 'longitude',
            'timezone', 'logo', 'intro_video',
            'admin_username', 'admin_email', 'admin_phone', 'admin_password',
        )

    def validate(self, attrs):
        request = self.context['request']
        if request.user.role == 'system_admin':
            admin_username = attrs.get('admin_username')
            admin_password = attrs.get('admin_password')
            if bool(admin_username) != bool(admin_password):
                raise serializers.ValidationError(
                    'Provide both admin_username and admin_password to create a masjid admin '
                    'account, or leave both blank.'
                )
            if admin_username:
                if User.objects.filter(username=admin_username).exists():
                    raise serializers.ValidationError({'admin_username': 'This username is already taken.'})
                validate_password(admin_password)
        return attrs

    def create(self, validated_data):
        admin_username = validated_data.pop('admin_username', '') or ''
        admin_email = validated_data.pop('admin_email', '') or ''
        admin_phone = validated_data.pop('admin_phone', '') or ''
        admin_password = validated_data.pop('admin_password', '') or ''

        request = self.context['request']
        is_system_admin = request.user.role == 'system_admin'

        masjid = Masjid.objects.create(
            **validated_data,
            status=Masjid.Status.APPROVED if is_system_admin else Masjid.Status.PENDING,
        )
        MasjidTheme.objects.create(masjid=masjid)  # default theme

        if is_system_admin:
            if admin_username and admin_password:
                User.objects.create_user(
                    username=admin_username,
                    email=admin_email,
                    phone=admin_phone,
                    password=admin_password,
                    role=User.Role.MASJID_ADMIN,
                    is_approved=True,
                    masjid=masjid,
                )
        else:
            # Link this masjid to the submitting masjid admin
            request.user.masjid = masjid
            request.user.save(update_fields=['masjid'])

        return masjid