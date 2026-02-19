from rest_framework.permissions import BasePermission, SAFE_METHODS

from contribution.models import Project, Issue


class CustomPermissionOrAdmin(BasePermission):
    edit_methods = ("PUT", "PATCH", "DELETE")

    @staticmethod
    def _is_authenticated(user):
        return bool(user and user.is_authenticated)

    @staticmethod
    def _is_contributor(user, project):
        return user in project.contributors.all()

    @staticmethod
    def _is_project_author(user, project):
        return user == project.author

    @staticmethod
    def _is_issue_author(user, issue):
        return user == issue.author

    @staticmethod
    def _is_comment_author(user, comment):
        return user == comment.author

    @staticmethod
    def _is_assigned(user, issue):
        return user == issue.attribution

    @staticmethod
    def _get_project(obj):
        if hasattr(obj, "project"):
            return obj.project

        if hasattr(obj, "issue"):
            return obj.issue.project

        return obj


    def has_permission(self, request, view):
        if not request.user or not self._is_authenticated(request.user):
            return False

        if view.action == "create" and "project_pk" in view.kwargs:
            project = Project.objects.get(id=view.kwargs["project_pk"])
            return self._is_contributor(request.user, project)

        if view.action == "create" and "issue_pk" in view.kwargs:
            project = Issue.objects.get(id=view.kwargs["issue_pk"]).project
            return self._is_contributor(request.user, project)

        if view.action == "unsubscribe" and "pk" in view.kwargs:
            project = Project.objects.get(id=view.kwargs["pk"])
            return self._is_contributor(request.user, project)

        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if view.action in ["subscribe"]:
            return True

        if request.method in SAFE_METHODS or view.action == "unsubscribe":
            return self._is_contributor(request.user, self._get_project(obj))

        if (self._is_project_author(request.user, self._get_project(obj))
                or self._is_issue_author(request.user, obj)
                or self._is_comment_author(request.user, obj)):
            return True

        if request.method in ["PUT", "PATCH"]:
            if type(obj) == Issue:
                if self._is_assigned(request.user, obj):
                    return True

        return False


class CustomContributorPermissionOrAdmin(BasePermission):

    @staticmethod
    def is_authenticated(request):
        return bool(request.user and request.user.is_authenticated)

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        if request.method == "GET":
            if view.action in ["list", "retrieve"]:
                return self.is_authenticated(request)

        return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if request.method == "GET":
            return True

        return False
