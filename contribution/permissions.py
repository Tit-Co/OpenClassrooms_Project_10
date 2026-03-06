from typing import TYPE_CHECKING

from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest
from rest_framework.exceptions import PermissionDenied

from rest_framework.permissions import BasePermission, SAFE_METHODS

from accounts.models import User
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
    def _get_project_from_obj(obj: Project | Issue | Comment | Contributor) -> Project:
        """
        Method that gets a project from an object.
        Args:
            obj (Project | Issue | Comment | Contributor): The object.

        Returns:
            The project.
        """
        if hasattr(obj, "project"):
            return obj.project

        if hasattr(obj, "issue"):
            return obj.issue.project

        return obj

    @staticmethod
    def _get_project_from_view(view: ProjectViewSet | IssueViewSet | CommentViewSet) -> (Project
                                                                                         | None):
        """
        Method that gets a project from a view.
        Args:
            view (ProjectViewSet | IssueViewSet | CommentViewSet): The view.

        Returns:
            The project.
        """
        kwargs = view.kwargs
        basename = view.basename

        if basename == "project":
            if "pk" in kwargs:
                return Project.objects.get(pk=kwargs["pk"])

        if basename == "issue":
            if "project_pk" in kwargs:
                return Project.objects.get(pk=kwargs["project_pk"])
            if "pk" in kwargs:
                issue = Issue.objects.select_related("project").get(pk=kwargs["pk"])
                return issue.project

        if basename == "comment":
            if "issue_pk" in kwargs:
                issue = Issue.objects.select_related("project").get(pk=kwargs["issue_pk"])
                return issue.project
            if "pk" in kwargs:
                comment = Comment.objects.select_related("issue__project").get(pk=kwargs["pk"])
                return comment.issue.project

        return None

    @staticmethod
    def _get_assigned_user_from_request(request: HttpRequest) -> User | None:
        """
        Method that gets the issue assigned user from the request.
        Args:
            request (HttpRequest): The request.

        Returns:
            The user if exists, None otherwise.
        """
        data = request.data

        attribution = data.get('attribution')
        if attribution:
            return User.objects.get(pk=attribution)

        return None

    def has_permission(self, request: HttpRequest,
                       view: ProjectViewSet | IssueViewSet | CommentViewSet) -> bool:
        """
        Method that checks if a user has permission to access the data
        Args:
            request (HttpRequest): The request.
            view (ProjectViewSet | IssueViewSet | CommentViewSet): The view.

        Returns:
            True if the user has permission to access the data, False otherwise.
        """
        if not request.user or not self._is_authenticated(request.user):
            return False

        if view.action in ["list", "retrieve", "unsubscribe"]:
            project = self._get_project_from_view(view=view)
            if project:
                return self._is_contributor(user=request.user, project=project)

        if view.action != "create" or view.basename != "issue":
            return True

        project = self._get_project_from_view(view)
        if not project:
            return False

        if not self._is_contributor(request.user, project):
            return False

        assigned_user = self._get_assigned_user_from_request(request)

        if not self._is_contributor(assigned_user, project):
            raise PermissionDenied({
                "attribution": f"{assigned_user} n'est pas contributeur(rice) du projet {project}."
            })

        return True

    def has_object_permission(self, request: HttpRequest,
                              view: ProjectViewSet | IssueViewSet | CommentViewSet,
                              obj: Project | Issue | Comment) -> bool:
        """
        Methods for verifying whether a user is authorized to act on the data according to
         the view action or the request method.
        Args:
            request (HttpRequest): The request.
            view (ProjectViewSet | IssueViewSet | CommentViewSet): The view.
            obj (Project | Issue | Comment) : The object.

        Returns:
            True if the user is authorized to act on the data, False otherwise.
        """
        if request.user.is_superuser:
            return True

        if view.action in ["subscribe"]:
            return True

        project = self._get_project_from_obj(obj=obj)

        if request.method in SAFE_METHODS or view.action == "unsubscribe":
            return self._is_contributor(user=request.user, project=project)

        if (self._is_project_author(user=request.user, project=project)
                or self._is_issue_author(user=request.user, issue=obj)
                or self._is_comment_author(user=request.user, comment=obj)):
            return True

        if request.method in ["PATCH"]:
            if (
                isinstance(obj, Issue)
                and self._is_assigned(user=request.user, issue=obj)
                and set(request.data.keys()) == {"status"}
            ):
                return True
            raise PermissionDenied("Action non autorisée : vous ne pouvez modifier que le statut.")

        return False


class CustomContributorPermissionOrAdmin(BasePermission):

    @staticmethod
    def is_authenticated(user: AbstractBaseUser) -> bool:
        return bool(user and user.is_authenticated)

    @staticmethod
    def _is_contributor(user: AbstractBaseUser, project: Project) -> bool:
        return user in project.contributors.all()

    @staticmethod
    def _get_project_from_view(view: ContributorViewSet) -> Project | None:
        """
        Method that gets a project from the view set.
        Args:
            view (ContributorViewSet): The view.

        Returns:
            The project, None otherwise.
        """
        kwargs = view.kwargs
        basename = view.basename

        if basename == "project":
            if "pk" in kwargs:
                return Project.objects.get(pk=kwargs["pk"])

        if basename == "contributor":
            if "project_pk" in kwargs:
                return Project.objects.get(pk=kwargs["project_pk"])
            if "pk" in kwargs:
                contributor = Contributor.objects.select_related("project").get(pk=kwargs["pk"])
                return contributor.project

        return None

    def has_permission(self, request: HttpRequest, view: ContributorViewSet):
        """
        Method that checks if a user is authorized to access the contributor data.
        Args:
            request (HttpRequest): The request.
            view (ContributorViewSet): The view set.

        Returns:
            True if the user is authorized to access the data, False otherwise.
        """
        if request.user.is_superuser:
            return True

        if request.method == "GET":
            if view.action in ["list", "retrieve"]:
                project = self._get_project_from_view(view=view)
                if project:
                    return self._is_contributor(user=request.user, project=project)

        return False

    def has_object_permission(self, request: HttpRequest,
                              view: ContributorViewSet, obj: Contributor) -> bool:
        """
        Method that checks if a user is authorized to act on the contributor data according to the
        request method or the user role.
        Args:
            request (HttpRequest): The request.
            view (ContributorViewSet): The view.
            obj (Contributor) : The object.

        Returns:
            True if the user is authorized to act on the data, False otherwise.
        """
        if request.user.is_superuser:
            return True

        if request.method == "GET":
            return True

        return False
