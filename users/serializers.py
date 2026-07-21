from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User


class MasjidAdminRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': "Passwords don't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            phone=validated_data.get('phone', ''),
            password=validated_data['password'],
            role=User.Role.MASJID_ADMIN,
            is_approved=False,  # must be approved by a system admin before use
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'role', 'is_approved', 'masjid')
        read_only_fields = ('role', 'is_approved', 'masjid')


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Blocks login for masjid admins who haven't been approved yet,
    and embeds role/masjid/approval info directly in the JWT payload."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['is_approved'] = user.is_approved
        token['masjid_id'] = user.masjid_id
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        if self.user.role == User.Role.MASJID_ADMIN and not self.user.is_approved:
            raise serializers.ValidationError(
                'Your account is pending approval by a system admin.'
            )
        data['user'] = UserSerializer(self.user).data
        return data