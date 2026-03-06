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
        """
        Method to check if the user is authenticated.
        Args:
            user (User): User instance.

        Returns:
            True if the user is authenticated otherwise False.
        """
        return bool(user and user.is_authenticated)

    def has_permission(self, request: HttpRequest, view: UserViewSet) -> bool:
        """
        Method to return the access permission to data according to the request method
        or the view action.
        Args:
            request (HttpRequest): HTTP request.
            view (UserViewSet): User view.

        Returns:
            True if the user is authorized otherwise False.
        """
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
        """
        Method to return the modification permission on the User object.
        Args:
            request (HttpRequest): HTTP request.
            view (UserViewSet): User view.
            obj (User): User instance.

        Returns:
            True if the user is authorized otherwise False.
        """
        if request.user.is_authenticated and (request.user == obj or request.user.is_superuser):
            return True

        return False
