from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from accounts.serializers import UserCreateSerializer, UserDetailSerializer, UserListSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly, BasePermission, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication


class MultipleSerializerMixin:
    serializer_class = None
    create_serializer_class = None
    detail_serializer_class = None
    list_serializer_class = None

    def get_serializer_class(self):
            if self.action == "create":
                return self.create_serializer_class
            elif self.action == "retrieve" and self.detail_serializer_class is not None:
                return self.detail_serializer_class
            elif self.action == "list":
                return self.list_serializer_class
            elif self.action == "update":
                return self.create_serializer_class

            return super().get_serializer_class()


class CustomUserPermissionOrAdmin(BasePermission):
    edit_methods = ("PUT", "PATCH", "DELETE")

    def has_permission(self, request, view):
        AUTHENTICATED = bool(request.user and request.user.is_authenticated)

        if request.user.is_superuser:
            return True

        if request.method == "GET":
            if view.action == "list":
                return True

            if view.action == "retrieve":
                return AUTHENTICATED

        if request.method == "POST":
            if view.action == "create":
                return True

        if request.method in self.edit_methods:
            user_id = view.kwargs['pk']
            user = User.objects.get(id=user_id)
            return AUTHENTICATED and (request.user == user or request.user.is_superuser)

        return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and (request.user == obj or request.user.is_superuser):
            return True
        return False


class UserViewSet(MultipleSerializerMixin, ModelViewSet):
    serializer_class = UserCreateSerializer
    create_serializer_class = UserCreateSerializer
    detail_serializer_class = UserDetailSerializer
    list_serializer_class = UserListSerializer

    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomUserPermissionOrAdmin]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all()

        queryset = User.objects.filter(is_active=True)
        user_id = self.request.GET.get('user_id')
        if user_id is not None:
            queryset = queryset.filter(id=user_id)

        return queryset

    @action(detail=True, methods=['POST'], permission_classes=[IsAdminUser])
    def disable(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user.disable()
        return Response()

    @action(detail=True, methods=['POST'], permission_classes=[IsAdminUser])
    def enable(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user.enable()
        return Response()
