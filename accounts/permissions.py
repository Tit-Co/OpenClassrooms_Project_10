from typing import TYPE_CHECKING

from django.http import HttpRequest
from rest_framework.permissions import BasePermission

from accounts.models import User

if TYPE_CHECKING:
    from accounts.views import UserViewSet


class CustomUserPermissionOrAdmin(BasePermission):
    edit_methods = ("PUT", "PATCH", "DELETE")

    @staticmethod
    def _is_authenticated(user: User) -> bool:
        return bool(user and user.is_authenticated)

    def has_permission(self, request: HttpRequest, view: UserViewSet) -> bool:
        if request.user.is_superuser:
            return True

        if request.method == "GET":
            if view.action == "list":
                return True

            if view.action == "retrieve":
                return self._is_authenticated(request.user)

        if request.method == "POST":
            if view.action == "create":
                return True

        if request.method in self.edit_methods:
            user_id = view.kwargs['pk']
            user = User.objects.get(id=user_id)
            return (self._is_authenticated(user=user)
                    and (request.user == user or request.user.is_superuser))

        return False

    def has_object_permission(self, request: HttpRequest, view: UserViewSet, obj: User) -> bool:
        if request.user.is_authenticated and (request.user == obj or request.user.is_superuser):
            return True

        return False
