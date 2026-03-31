from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import permissions, serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserHealthCondition, UserProfile
from .serializers import (
    AdminUserDetailSerializer,
    AdminUserListSerializer,
    AdminUserUpdateSerializer,
    FlexibleTokenObtainPairSerializer,
    RegisterSerializer,
    UserHealthConditionSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    UserSerializer,
)


User = get_user_model()


class EnvelopeUserSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = UserSerializer()


class EnvelopeProfileSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = UserProfileSerializer()


class EnvelopeHealthConditionSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = UserHealthConditionSerializer()


class FullProfileRequestSerializer(serializers.Serializer):
    account = UserUpdateSerializer(required=False)
    profile = UserProfileSerializer(required=False)
    health_condition = UserHealthConditionSerializer(required=False)


class FullProfileResponseDataSerializer(serializers.Serializer):
    account = UserSerializer()
    profile = UserProfileSerializer()
    health_condition = UserHealthConditionSerializer()


class EnvelopeFullProfileSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = FullProfileResponseDataSerializer()


class LoginResponseDataSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class EnvelopeLoginSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = LoginResponseDataSerializer()


class AdminUserListEnvelopeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = inline_serializer(
        name="AdminUserListData",
        fields={
            "count": serializers.IntegerField(),
            "next": serializers.CharField(allow_null=True),
            "previous": serializers.CharField(allow_null=True),
            "items": AdminUserListSerializer(many=True),
        },
    )


class AdminUserDetailEnvelopeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = AdminUserDetailSerializer()


class AdminUserRequestSerializer(serializers.Serializer):
    account = AdminUserUpdateSerializer(required=False)
    profile = UserProfileSerializer(required=False)
    health_condition = UserHealthConditionSerializer(required=False)


class IsAdminManager(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.is_staff or getattr(user, "role", "") == "admin"))


class AdminUserPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "count": self.page.paginator.count,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "items": data,
                },
            }
        )


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=RegisterSerializer, responses=EnvelopeUserSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"code": 0, "message": "success", "data": UserSerializer(user).data})


class MeView(APIView):
    @extend_schema(responses=EnvelopeUserSerializer)
    def get(self, request):
        return Response({"code": 0, "message": "success", "data": UserSerializer(request.user).data})

    @extend_schema(request=UserUpdateSerializer, responses=EnvelopeUserSerializer)
    def put(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"code": 0, "message": "success", "data": UserSerializer(user).data})


class ProfileView(APIView):
    @extend_schema(request=UserProfileSerializer, responses=EnvelopeProfileSerializer)
    def put(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"code": 0, "message": "success", "data": serializer.data})


class HealthConditionView(APIView):
    @extend_schema(request=UserHealthConditionSerializer, responses=EnvelopeHealthConditionSerializer)
    def put(self, request):
        health_condition, _ = UserHealthCondition.objects.get_or_create(user=request.user)
        serializer = UserHealthConditionSerializer(health_condition, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"code": 0, "message": "success", "data": serializer.data})


class FullProfileView(APIView):
    @transaction.atomic
    @extend_schema(request=FullProfileRequestSerializer, responses=EnvelopeFullProfileSerializer)
    def put(self, request):
        user_serializer = UserUpdateSerializer(request.user, data=request.data.get("account", {}), partial=True)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile_serializer = UserProfileSerializer(profile, data=request.data.get("profile", {}), partial=True)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()

        health_condition, _ = UserHealthCondition.objects.get_or_create(user=user)
        health_serializer = UserHealthConditionSerializer(health_condition, data=request.data.get("health_condition", {}), partial=True)
        health_serializer.is_valid(raise_exception=True)
        health_serializer.save()

        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "account": UserSerializer(user).data,
                    "profile": profile_serializer.data,
                    "health_condition": health_serializer.data,
                },
            }
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=FlexibleTokenObtainPairSerializer, responses=EnvelopeLoginSerializer)
    def post(self, request):
        serializer = FlexibleTokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": UserSerializer(user).data,
                },
            }
        )


class AdminUserListView(APIView):
    permission_classes = [IsAdminManager]
    pagination_class = AdminUserPagination

    @extend_schema(responses=AdminUserListEnvelopeSerializer)
    def get(self, request):
        queryset = User.objects.select_related("profile", "health_condition").order_by("-date_joined", "-id")

        keyword = request.query_params.get("keyword", "").strip()
        role = request.query_params.get("role", "").strip()
        status_value = request.query_params.get("status", "").strip()

        if keyword:
            queryset = queryset.filter(
                Q(username__icontains=keyword)
                | Q(nickname__icontains=keyword)
                | Q(email__icontains=keyword)
                | Q(phone__icontains=keyword)
            )
        if role:
            queryset = queryset.filter(role=role)
        if status_value:
            queryset = queryset.filter(status=status_value)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = AdminUserListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminUserDetailView(APIView):
    permission_classes = [IsAdminManager]

    def get_object(self, user_id):
        return get_object_or_404(User.objects.select_related("profile", "health_condition"), pk=user_id)

    @extend_schema(responses=AdminUserDetailEnvelopeSerializer)
    def get(self, request, user_id):
        user = self.get_object(user_id)
        serializer = AdminUserDetailSerializer(user)
        return Response({"code": 0, "message": "success", "data": serializer.data})

    @transaction.atomic
    @extend_schema(request=AdminUserRequestSerializer, responses=AdminUserDetailEnvelopeSerializer)
    def patch(self, request, user_id):
        user = self.get_object(user_id)

        account_serializer = AdminUserUpdateSerializer(user, data=request.data.get("account", {}), partial=True)
        account_serializer.is_valid(raise_exception=True)
        user = account_serializer.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile_serializer = UserProfileSerializer(profile, data=request.data.get("profile", {}), partial=True)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()

        health_condition, _ = UserHealthCondition.objects.get_or_create(user=user)
        health_serializer = UserHealthConditionSerializer(health_condition, data=request.data.get("health_condition", {}), partial=True)
        health_serializer.is_valid(raise_exception=True)
        health_serializer.save()

        detail_serializer = AdminUserDetailSerializer(user)
        return Response({"code": 0, "message": "success", "data": detail_serializer.data}, status=status.HTTP_200_OK)
