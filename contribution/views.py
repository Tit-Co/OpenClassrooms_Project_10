from django.db import IntegrityError
from django.http import HttpRequest
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication

from contribution.models import Project, Contributor, Issue, Comment
from contribution.serializers import (ProjectCreateSerializer, ProjectDetailSerializer,
                                      ProjectListSerializer, IssueCreateSerializer,
                                      IssueDetailSerializer, IssueListSerializer,
                                      CommentCreateSerializer, CommentListSerializer,
                                      CommentDetailSerializer, ContributorDetailSerializer,
                                      ContributorListSerializer)

from contribution.permissions import CustomPermissionOrAdmin, CustomContributorPermissionOrAdmin


class MultipleSerializerMixin:
    serializer_class = None
    create_serializer_class = None
    detail_serializer_class = None
    list_serializer_class = None

    def get_serializer_class(self):
        """
        Method that gets the serializer according to the action.
        Returns:
            The serializer class.
        """
        if self.action == "create":
            return self.create_serializer_class
        elif self.action == "retrieve" and self.detail_serializer_class is not None:
            return self.detail_serializer_class
        elif self.action == "list":
            return self.list_serializer_class
        elif self.action == "update":
            return self.create_serializer_class

        return super().get_serializer_class()


class ProjectViewSet(MultipleSerializerMixin, ModelViewSet):
    serializer_class = ProjectCreateSerializer
    create_serializer_class = ProjectCreateSerializer
    detail_serializer_class = ProjectDetailSerializer
    list_serializer_class = ProjectListSerializer

    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomPermissionOrAdmin]

    def get_queryset(self):
        """
        Method that gets the queryset of projects.
        Returns:
            The queryset of projects.
        """
        if self.request.user.is_superuser:
            return Project.objects.all()

        return Project.objects.filter(active=True).order_by('-id')

    def get_serializer_class(self):
        """
        Method that gets the project serializer according to the action or the contributor list
        serializer
        Returns:
            The project serializer class or the contributor list serializer.
        """
        if self.action == 'contributor':
            if self.request.method == 'GET':
                return ContributorListSerializer

        return super().get_serializer_class()

    @action(detail=True, methods=['POST'], permission_classes=[IsAdminUser])
    def disable(self, request: HttpRequest, pk: int) -> Response:
        """
        Method that disables a project by admin user.
        Args:
            request (HttpRequest): The request object.
            pk (int): The id of the project to disable.

        Returns:
            The response object.
        """
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        project.disable()
        return Response({'status': 'Succés'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'], permission_classes=[IsAdminUser])
    def enable(self, request: HttpRequest, pk: int) -> Response:
        """
        Method that enables a project by admin user.
        Args:
            request (HttpRequest): The request object.
            pk (int): The id of the project to enable.

        Returns:
            The response object.
        """
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        project.enable()
        return Response({'status': 'Succés'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def subscribe(self, request: HttpRequest, pk: int) -> Response:
        """
        Method to subscribe a project
        Args:
            request (HttpRequest): The request object.
            pk (int): The id of the project to subscribe.

        Returns:
            The response object : success or conflict if the user is already contributor.
        """
        project = self.get_object()
        user = request.user

        try:
            Contributor.objects.create(user=user, project=project, role='CONTRIBUTOR')
        except IntegrityError:
            return Response({'status': 'Vous êtes déjà contributeur.'},
                            status=status.HTTP_409_CONFLICT)

        return Response({'status': 'Succés'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def unsubscribe(self, request: HttpRequest, pk: int) -> Response:
        """
        Method to unsubscribe a project
        Args:
            request (HttpRequest): The request object.
            pk (int): The id of the project to unsubscribe.

        Returns:
            The response object : success or not found error if the user is not contributor of the
            project.
        """
        project = self.get_object()
        user = request.user

        try:
            Contributor.objects.filter(user=user, project=project).delete()
        except Contributor.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not user.can_data_be_shared:
            issues = Issue.objects.filter(project=project)
            Comment.objects.filter(author=user, issue__in=issues).delete()
            issues.filter(author=user).delete()
            Project.objects.filter(id=project.pk, author=user).delete()

        return Response({'status': 'Succés'}, status=status.HTTP_200_OK)


class ContributorViewSet(MultipleSerializerMixin, ModelViewSet):
    serializer_class = ProjectListSerializer
    detail_serializer_class = ProjectDetailSerializer
    list_serializer_class = ProjectListSerializer

    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomContributorPermissionOrAdmin]

    def get_queryset(self):
        """
        Method that gets the queryset of contributors.
        Returns:
            The queryset of contributors.
        """
        if self.request.user.is_superuser:
            return Contributor.objects.all().order_by('-id')

        project = Project.objects.get(id=self.kwargs.get('project_pk'))
        queryset = Contributor.objects.filter(project=project).order_by('id')
        contributor_id = self.request.GET.get('contributor_id')
        if contributor_id is not None:
            queryset = queryset.filter(id=contributor_id)

        return queryset

    def get_serializer_class(self):
        """
        Method that gets the contributor serializer according to the action.
        Returns:
            The contributor serializer class.
        """
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
        """
        Method that gets the issue serializer according to the action and request method.
        Returns:
            The issue serializer class.
        """
        if self.action == 'comment' and self.request.method == 'POST':
            return CommentCreateSerializer

        if self.action == 'comment' and self.request.method == 'GET':
            return CommentDetailSerializer

        return super().get_serializer_class()

    def get_serializer_context(self):
        """
        Method that sets the request context for an issue.
        Returns:
            The request context.
        """
        context = super().get_serializer_context()
        if 'project_pk' in self.kwargs:
            context["project"] = Project.objects.get(pk=self.kwargs['project_pk'])
        else:
            context["project"] = None
        return context

    def get_queryset(self):
        """
        Method that gets the queryset of issues.
        Returns:
            The queryset of issues.
        """
        if self.request.user.is_superuser:
            return Issue.objects.all()

        project_pk = self.kwargs.get('project_pk')
        issue_pk = self.kwargs.get('pk')

        if project_pk:
            return Issue.objects.filter(project__pk=project_pk, active=True)

        elif issue_pk:
            return Issue.objects.filter(pk=issue_pk, active=True)

        return Issue.objects.filter(project__contributor__user=self.request.user,
                                    active=True).distinct().order_by('-id')

    def perform_create(self, serializer):
        """
        Method that creates a new issue with serializer data for the given project id in kwargs.
        Args:
            serializer (Serializer): The serializer object.
        """
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
        """
        Method that disables an issue by admin user.
        Args:
            request (HttpRequest): The request object.
            pk (int): The id of the issue to disable.

        Returns:
            The response object : success or not found error.
        """
        try:
            issue = Issue.objects.get(pk=pk)
        except Issue.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        issue.disable()
        return Response({'status': 'Succés'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'], permission_classes=[IsAdminUser])
    def enable(self, request, pk):
        """
        Method that enables an issue by admin user.
        Args:
            request (HttpRequest): The request object.
            pk (int): The id of the issue to enable.

        Returns:
            The response object : success or not found error.
        """
        try:
            issue = Issue.objects.get(pk=pk)
        except Issue.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        issue.enable()
        return Response({'status': 'Succés'}, status=status.HTTP_200_OK)


class CommentViewSet(MultipleSerializerMixin, ModelViewSet):
    serializer_class = CommentCreateSerializer
    create_serializer_class = CommentCreateSerializer
    detail_serializer_class = CommentDetailSerializer
    list_serializer_class = CommentListSerializer

    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomPermissionOrAdmin]

    def get_queryset(self):
        """
        Method that gets the queryset of comments.
        Returns:
            The queryset of comments.
        """
        issue_pk = self.kwargs.get('issue_pk')
        queryset = Comment.objects.filter(issue__id=issue_pk,
                                          active=True).order_by('-created_time')
        comment_uuid = self.request.GET.get('comment_uuid')
        if comment_uuid is not None:
            queryset = queryset.filter(id=comment_uuid)

        return queryset

    def get_serializer_class(self):
        """
        Method that gets the comment serializer according to the request method or action.
        Returns:
            The serializer class.
        """
        if self.request.method == 'POST':
            return CommentCreateSerializer
        elif self.request.method == 'GET':
            if self.action == 'list':
                return CommentListSerializer
            elif self.action == 'retrieve':
                return CommentDetailSerializer

        return super().get_serializer_class()

    def perform_create(self, serializer):
        """
        Method that creates a new comment with serializer data from the issue id in kwargs.
        Args:
            serializer ():
        """
        issue = Issue.objects.get(pk=self.kwargs["issue_pk"])
        serializer.save(
            issue=issue,
            author=self.request.user
        )
