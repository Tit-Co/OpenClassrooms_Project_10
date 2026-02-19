from typing import TYPE_CHECKING

from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest

from rest_framework.permissions import BasePermission, SAFE_METHODS

from contribution.models import Project, Issue, Comment, Contributor

if TYPE_CHECKING:
    from contribution.views import IssueViewSet, ProjectViewSet, CommentViewSet, ContributorViewSet


class CustomPermissionOrAdmin(BasePermission):
    edit_methods = ("PUT", "PATCH", "DELETE")

    @staticmethod
    def _is_authenticated(user: AbstractBaseUser):
        return bool(user and user.is_authenticated)

    @staticmethod
    def _is_contributor(user: AbstractBaseUser, project: Project) -> bool:
        return user in project.contributors.all()

    @staticmethod
    def _is_project_author(user: AbstractBaseUser, project: Project) -> bool:
        return user == project.author

    @staticmethod
    def _is_issue_author(user: AbstractBaseUser, issue: Issue) -> bool:
        return user == issue.author

    @staticmethod
    def _is_comment_author(user: AbstractBaseUser, comment: Comment) -> bool:
        return user == comment.author

    @staticmethod
    def _is_assigned(user: AbstractBaseUser, issue: Issue) -> bool:
        return user == issue.attribution

    @staticmethod
    def _get_project(obj: Project|Issue|Comment|Contributor) -> Project:
        if hasattr(obj, "project"):
            return obj.project

        if hasattr(obj, "issue"):
            return obj.issue.project

        return obj


    def has_permission(self, request: HttpRequest, view: ProjectViewSet|IssueViewSet|CommentViewSet) -> bool:
        if not request.user or not self._is_authenticated(request.user):
            return False

        if view.action == "create" and "project_pk" in view.kwargs:
            project = Project.objects.get(id=view.kwargs["project_pk"])
            return self._is_contributor(user=request.user, project=project)

        if view.action == "create" and "issue_pk" in view.kwargs:
            project = Issue.objects.get(id=view.kwargs["issue_pk"]).project
            return self._is_contributor(user=request.user, project=project)

        if view.action == "unsubscribe" and "pk" in view.kwargs:
            project = Project.objects.get(id=view.kwargs["pk"])
            return self._is_contributor(user=request.user, project=project)

        return True

    def has_object_permission(self, request: HttpRequest, view: ProjectViewSet|IssueViewSet|CommentViewSet,
                              obj: Project|Issue|Comment) -> bool:
        if request.user.is_superuser:
            return True

        if view.action in ["subscribe"]:
            return True

        if request.method in SAFE_METHODS or view.action == "unsubscribe":
            return self._is_contributor(user=request.user, project=self._get_project(obj))

        if (self._is_project_author(user=request.user, project=self._get_project(obj))
                or self._is_issue_author(user=request.user, issue=obj)
                or self._is_comment_author(user=request.user, comment=obj)):
            return True

        if request.method in ["PUT", "PATCH"]:
            if type(obj) == Issue:
                if self._is_assigned(user=request.user, issue=obj):
                    return True

        return False


class CustomContributorPermissionOrAdmin(BasePermission):

    @staticmethod
    def is_authenticated(user: AbstractBaseUser) -> bool:
        return bool(user and user.is_authenticated)

    def has_permission(self, request: HttpRequest, view: ContributorViewSet):
        if request.user.is_superuser:
            return True

        if request.method == "GET":
            if view.action in ["list", "retrieve"]:
                return self.is_authenticated(user=request.user)

        return False

    def has_object_permission(self, request: HttpRequest, view: ContributorViewSet, obj: Contributor) -> bool:
        if request.user.is_superuser:
            return True

        if request.method == "GET":
            return True

        return False
