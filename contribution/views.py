from django.db import transaction
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from contribution.models import Project, Contributor
from contribution.serializers import (ProjectCreateSerializer, ProjectDetailSerializer, ProjectAdminDetailSerializer,
                                      ProjectListSerializer)


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


class AdminProjectViewSet(MultipleSerializerMixin, ModelViewSet):
    pass


class IsProjectContributor(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.user in obj.contributors.all():
            return True
        return False


class IsProjectAuthor(BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.author == request.user:
            return True
        return False

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        return False


class ProjectViewSet(MultipleSerializerMixin, ModelViewSet):
    serializer_class = ProjectCreateSerializer
    create_serializer_class = ProjectCreateSerializer
    detail_serializer_class = ProjectDetailSerializer
    list_serializer_class = ProjectListSerializer

    def get_permissions(self):
        if self.action in ['create', 'list', 'subscribe']:
            return [AllowAny()]

        elif self.action in ['retrieve', 'unsubscribe']:
            return [IsProjectContributor()]

        return [IsProjectAuthor()]

    def get_queryset(self):
        queryset = Project.objects.filter()
        project_id = self.request.GET.get('project_id')
        if project_id is not None:
            queryset = queryset.filter(id=project_id)

        return queryset

    @transaction.atomic
    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk):
        project = self.get_object()
        user = request.user
        if user.is_authenticated:
            Contributor.objects.create(user=user, project=project, role='CONTRIBUTOR')

            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        return Response({'status': 'failed'}, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    @action(detail=True, methods=['post'])
    def unsubscribe(self, request, pk):
        project = self.get_object()
        user = request.user
        if user.is_authenticated:
            Contributor.objects.filter(user=user, project=project).delete()

            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        return Response({'status': 'failed'}, status=status.HTTP_400_BAD_REQUEST)