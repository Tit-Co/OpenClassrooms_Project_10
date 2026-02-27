from typing import Any

from rest_framework.serializers import ModelSerializer, SerializerMethodField

from contribution.models import Project, Contributor, Issue, Comment


class ProjectCreateSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = ('name', 'description', 'type')

    def to_internal_value(self, data: Any) -> Any:
        data = data.copy()

        if 'type' in data:
            data['type'] = data['type'].strip().upper()

        return super().to_internal_value(data)

    def create(self, validated_data: Any) -> Project:
        user = self.context['request'].user
        project = Project.objects.create(
            name=validated_data['name'],
            description=validated_data['description'],
            type=validated_data['type'],
            author=user)

        Contributor.objects.create(user=user, project=project, role='AUTHOR')

        return project


class ProjectListSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name']


class ProjectDetailSerializer(ModelSerializer):
    issues = SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'type', 'author', 'created_time', 'issues']

    @staticmethod
    def get_issues(instance: Issue) -> list:
        queryset = Issue.objects.filter(project=instance, active=True)
        serializer = IssueDetailSerializer(queryset, many=True)
        return serializer.data


class ContributorListSerializer(ModelSerializer):
    class Meta:
        model = Contributor
        fields = ['id', 'project', 'user']


class ContributorDetailSerializer(ModelSerializer):

    class Meta:
        model = Contributor
        fields = ['id', 'project', 'user', 'role']


class IssueCreateSerializer(ModelSerializer):
    class Meta:
        model = Issue
        fields = ['name', 'priority', 'status', 'attribution', 'tag']

    def to_internal_value(self, data: Any) -> Any:
        data = data.copy()

        if 'priority' in data:
            data['priority'] = data['priority'].strip().upper()

        if 'status' in data:
            data['status'] = data['status'].strip().upper()

        if 'tag' in data:
            data['tag'] = data['tag'].strip().upper()

        return super().to_internal_value(data)


class IssueListSerializer(ModelSerializer):
    class Meta:
        model = Issue
        fields = ['id', 'name']


class IssueDetailSerializer(ModelSerializer):
    comments = SerializerMethodField()

    class Meta:
        model = Issue
        fields = ['id',
                  'name',
                  'priority',
                  'status',
                  'author',
                  'attribution',
                  'tag',
                  'created_time',
                  'comments']

    @staticmethod
    def get_comments(instance: Issue) -> list:
        queryset = Comment.objects.filter(issue=instance, active=True)
        serializer = CommentDetailSerializer(queryset, many=True)
        return serializer.data

    def get_fields(self):
        fields = super().get_fields()

        if self.context.get("project") is not None:
            fields.pop("comments", None)

        return fields


class CommentCreateSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = ['uuid', 'description', 'link', 'created_time']


class CommentListSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = ['uuid', 'description']


class CommentDetailSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = ['uuid', 'description', 'author', 'issue', 'link', 'created_time']
