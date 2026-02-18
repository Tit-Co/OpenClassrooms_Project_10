from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, BasePermission, IsAdminUser, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication

from contribution.models import Project, Contributor, Issue, Comment
from contribution.serializers import (ProjectCreateSerializer, ProjectDetailSerializer, ProjectListSerializer,
                                      IssueCreateSerializer, IssueDetailSerializer, IssueListSerializer,
                                      CommentCreateSerializer, CommentListSerializer, CommentDetailSerializer,
                                      ContributorDetailSerializer, ContributorListSerializer)


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

        if request.method in SAFE_METHODS or view.action in ["unsubscribe"]:
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

class ProjectViewSet(MultipleSerializerMixin, ModelViewSet):
    serializer_class = ProjectCreateSerializer
    create_serializer_class = ProjectCreateSerializer
    detail_serializer_class = ProjectDetailSerializer
    list_serializer_class = ProjectListSerializer

    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomPermissionOrAdmin]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Project.objects.all()

        pk = self.kwargs.get('pk')
        if not pk or self.action == "subscribe":
            queryset = Project.objects.filter(active=True)
        else:
            queryset = Project.objects.filter(contributors=self.request.user, active=True)
            queryset = queryset.filter(id=pk)

        return queryset

    def get_serializer_class(self):
        if self.action == 'contributor':
            if self.request.method == 'GET':
                return ContributorListSerializer

        return super().get_serializer_class()

    @action(detail=True, methods=['POST'], permission_classes=[IsAdminUser])
    def disable(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        project.disable()
        return Response({'status': 'Succés'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'], permission_classes=[IsAdminUser])
    def enable(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        project.enable()
        return Response({'status': 'Succés'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk):
        project = self.get_object()
        user = request.user

        try:
            Contributor.objects.create(user=user, project=project, role='CONTRIBUTOR')
        except IntegrityError:
            return Response({'status': 'Vous êtes déjà contributeur.'}, status=status.HTTP_409_CONFLICT)

        return Response({'status': 'Succés'}, status=status.HTTP_200_OK)


    @action(detail=True, methods=['post'])
    def unsubscribe(self, request, pk):
        project = self.get_object()
        user = request.user

        try:
            Contributor.objects.filter(user=user, project=project).delete()
        except Contributor.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not user.can_data_be_shared:
            issues = Issue.objects.filter(project=project)
            for issue in issues:
                Comment.objects.filter(author=user, issue=issue).delete()
            Issue.objects.filter(project=project, author=user).delete()

        return Response({'status': 'Succés'}, status=status.HTTP_200_OK)


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


class ContributorViewSet(MultipleSerializerMixin, ModelViewSet):
    serializer_class = ProjectListSerializer
    detail_serializer_class = ProjectDetailSerializer
    list_serializer_class = ProjectListSerializer

    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomContributorPermissionOrAdmin]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Contributor.objects.all().order_by('id')

        queryset = Contributor.objects.filter().order_by('id')
        contributor_id = self.request.GET.get('contributor_id')
        if contributor_id is not None:
            queryset = queryset.filter(id=contributor_id)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ContributorListSerializer

        elif self.action == 'retrieve':
            return ContributorDetailSerializer

        return super().get_serializer_class()


class IssueViewSet(MultipleSerializerMixin, ModelViewSet):
    serializer_class = IssueCreateSerializer
    create_serializer_class = IssueCreateSerializer
    detail_serializer_class = IssueDetailSerializer
    list_serializer_class = IssueListSerializer

    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomPermissionOrAdmin]

    def get_serializer_class(self):
        if self.action == 'comment':
            if self.request.method == 'POST':
                return CommentCreateSerializer
            elif self.request.method == 'GET':
                return CommentDetailSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Issue.objects.all()
        project_pk = self.kwargs.get('project_pk')
        if project_pk:
            queryset = Issue.objects.filter(project__pk=project_pk, active=True)
        else:
            queryset = Issue.objects.filter(active=True)

        return queryset

    def perform_create(self, serializer):
        try:
            project = Project.objects.get(pk=self.kwargs["project_pk"])
            serializer.save(
                project=project,
                author=self.request.user
            )
        except KeyError:
            raise ValidationError("Aucun projet spécifié.")

    @action(detail=True, methods=['POST'], permission_classes=[IsAdminUser])
    def disable(self, request, pk):
        try:
            issue = Issue.objects.get(pk=pk)
        except Issue.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        issue.disable()
        return Response()

    @action(detail=True, methods=['POST'], permission_classes=[IsAdminUser])
    def enable(self, request, pk):
        try:
            issue = Issue.objects.get(pk=pk)
        except Issue.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        issue.enable()
        return Response()


class CommentViewSet(MultipleSerializerMixin, ModelViewSet):
    serializer_class = CommentCreateSerializer
    create_serializer_class = CommentCreateSerializer
    detail_serializer_class = CommentDetailSerializer
    list_serializer_class = CommentListSerializer

    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomPermissionOrAdmin]

    def get_queryset(self):
        issue_pk = self.kwargs.get('issue_pk')
        queryset = Comment.objects.filter(issue__id=issue_pk, active=True)
        comment_uuid = self.request.GET.get('comment_uuid')
        if comment_uuid is not None:
            queryset = queryset.filter(id=comment_uuid)

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentCreateSerializer
        elif self.request.method == 'GET':
            if self.action == 'list':
                return CommentListSerializer
            elif self.action == 'retrieve':
                return CommentDetailSerializer

        return super().get_serializer_class()

    def perform_create(self, serializer):
        issue = Issue.objects.get(pk=self.kwargs["issue_pk"])
        serializer.save(
            issue=issue,
            author=self.request.user
        )
