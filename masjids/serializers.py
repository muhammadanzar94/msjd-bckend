from rest_framework import serializers
from core.fields import AbsoluteFileField, AbsoluteImageField
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
    """Used on creation — masjid admin submits this, status always starts pending."""

    logo = AbsoluteImageField(required=False, allow_null=True)
    intro_video = AbsoluteFileField(required=False, allow_null=True)

    class Meta:
        model = Masjid
        fields = (
            'id', 'name', 'slug', 'address', 'city', 'country', 'postcode',
            'phone', 'email', 'firqa', 'google_maps_link', 'latitude', 'longitude',
            'timezone', 'logo', 'intro_video',
        )

    def create(self, validated_data):
        masjid = Masjid.objects.create(**validated_data, status=Masjid.Status.PENDING)
        MasjidTheme.objects.create(masjid=masjid)  # default theme
        # Link this masjid to the creating admin
        request = self.context['request']
        request.user.masjid = masjid
        request.user.save(update_fields=['masjid'])
        return masjid