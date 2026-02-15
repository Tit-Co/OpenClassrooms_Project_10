from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, BasePermission, IsAdminUser, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication

from contribution.models import Project, Contributor, Issue, Comment
from contribution.serializers import (ProjectCreateSerializer, ProjectDetailSerializer, ProjectListSerializer,
                                      IssueCreateSerializer, IssueDetailSerializer, IssueListSerializer,
                                      CommentCreateSerializer, CommentListSerializer, CommentDetailSerializer)


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

    def has_permission(self, request, view):
        AUTHENTICATED = bool(request.user and request.user.is_authenticated)

        if request.user.is_superuser:
            return True

        if request.method == "GET":
            if view.action == "list":
                return AUTHENTICATED

            if view.action == "retrieve":
                if "project_pk" in view.kwargs:
                    project = Project.objects.get(id=view.kwargs["project_pk"])
                else:
                    project = Issue.objects.get(id=view.kwargs['pk']).project

                return AUTHENTICATED  and request.user in project.contributors.all()

        if request.method == "POST":
            if view.action == "unsubscribe":
                project = Project.objects.get(id=view.kwargs['pk'])

                return AUTHENTICATED and request.user in project.contributors.all()

            elif view.action == "subscribe" or view.action == "create":
                return AUTHENTICATED

        if request.method not in self.edit_methods and view.action is not None:
            project = None
            if view.action == "issue":
                if 'project_pk' in view.kwargs:
                    project = Project.objects.get(id=view.kwargs['project_pk'])
                else:
                    project = Project.objects.get(id=view.kwargs['pk'])

            elif view.action == "comment":
                if 'project_pk' in view.kwargs:
                    return False

                issue = Issue.objects.get(id=view.kwargs['pk'])
                project = issue.project

            return AUTHENTICATED and request.user in project.contributors.all()

        if request.method in self.edit_methods:
            if "project_pk" in view.kwargs:
                if "issue_pk" in view.kwargs:
                    uuid = view.kwargs['pk']
                    comment = Comment.objects.get(uuid=uuid)

                    return AUTHENTICATED and request.user == comment.author

                issue_id = view.kwargs['pk']
                issue = Issue.objects.get(id=issue_id)
                return AUTHENTICATED and request.user == issue.author

            project = Project.objects.get(id=view.kwargs['pk'])
            return AUTHENTICATED and request.user == project.author

        return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if obj.author == request.user and request.method in self.edit_methods:
            return True

        if view.action == "subscribe":
            return True

        if hasattr(obj, "contributors"):
            return request.user in obj.contributors.all()

        if hasattr(obj, "project"):
            return request.user in obj.project.contributors.all()

        if hasattr(obj, "issue"):
            return request.user in obj.issue.project.contributors.all()

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

        queryset = Project.objects.filter(active=True)
        project_id = self.request.GET.get('project_id')
        if project_id is not None:
            queryset = queryset.filter(id=project_id)

        return queryset

    def get_serializer_class(self):
        if self.action == 'issue':
            if self.request.method == 'POST':
                return IssueCreateSerializer
            elif self.request.method == 'GET':
                return IssueDetailSerializer
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


    @action(detail=True, methods=['get', 'post'])
    def issue(self, request, pk=None):
        project = self.get_object()
        if request.method == 'GET':
            issues = Issue.objects.filter(project=project, active=True)
            serializer = self.get_serializer(issues, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            serializer = self.get_serializer(data=request.data, context={'request': request, 'project': project})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        queryset = Issue.objects.filter(active=True)
        issue_id = self.request.GET.get('issue_id')
        if issue_id is not None:
            queryset = queryset.filter(id=issue_id)

        return queryset

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

    @action(detail=True, methods=['get', 'post'])
    def comment(self, request, project_pk=None, pk=None):
        issue = self.get_object()
        self.check_object_permissions(request, issue)
        if request.method == 'GET':
            comments = Comment.objects.filter(issue=issue, active=True)
            serializer = self.get_serializer(comments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            serializer = self.get_serializer(data=request.data, context={'request': request, 'issue': issue})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentViewSet(MultipleSerializerMixin, ModelViewSet):
    serializer_class = CommentCreateSerializer
    create_serializer_class = CommentCreateSerializer
    detail_serializer_class = CommentDetailSerializer
    list_serializer_class = CommentListSerializer

    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomPermissionOrAdmin]

    def get_queryset(self):
        queryset = Comment.objects.filter(active=True)
        comment_uuid = self.request.GET.get('comment_uuid')
        if comment_uuid is not None:
            queryset = queryset.filter(id=comment_uuid)

        return queryset
