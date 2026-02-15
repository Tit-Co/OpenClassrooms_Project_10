from rest_framework.serializers import ModelSerializer, SerializerMethodField, ValidationError

from contribution.models import Project, Contributor, Issue, Comment


class ProjectCreateSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = ('name', 'description', 'type')

    def to_internal_value(self, data):
        data = data.copy()

        if 'type' in data:
            data['type'] = data['type'].strip().upper()

        return super().to_internal_value(data)

    def create(self, validated_data):
        user = self.context['request'].user
        project = Project.objects.create(
            name = validated_data['name'],
            description = validated_data['description'],
            type = validated_data['type'],
            author = user)

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
    def get_issues(instance):
        queryset = Issue.objects.filter(project=instance, active=True)
        serializer = IssueDetailSerializer(queryset, many=True)
        return serializer.data


class IssueCreateSerializer(ModelSerializer):
    class Meta:
        model = Issue
        fields = ['name', 'priority', 'status', 'attribution', 'balise']

    def to_internal_value(self, data):
        data = data.copy()

        if 'priority' in data:
            data['priority'] = data['priority'].strip().upper()

        if 'status' in data:
            data['status'] = data['status'].strip().upper()

        if 'balise' in data:
            data['balise'] = data['balise'].strip().upper()

        return super().to_internal_value(data)

    def create(self, validated_data):
        try:
            project = self.context['project']
            author = self.context['request'].user

            issue = Issue.objects.create(
                name=validated_data['name'],
                priority=validated_data['priority'],
                status=validated_data['status'],
                attribution=validated_data['attribution'],
                balise=validated_data['balise'],
                project=project,
                author=author)

            return issue

        except KeyError:
            raise ValidationError("Le projet n'existe pas.")


class IssueListSerializer(ModelSerializer):
    class Meta:
        model = Issue
        fields = ['id', 'name']


class IssueDetailSerializer(ModelSerializer):

    class Meta:
        model = Issue
        fields = ['id', 'name', 'priority', 'status', 'author', 'attribution', 'balise', 'created_time']

    @staticmethod
    def get_comments(instance):
        queryset = Comment.objects.filter(issue=instance, active=True)
        serializer = CommentDetailSerializer(queryset, many=True)
        return serializer.data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'project' not in kwargs['context']['request'].get_full_path():
            self.comments = SerializerMethodField()
            self.fields['comments'] = self.comments


class CommentCreateSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = ['uuid', 'description', 'link', 'created_time']

    def create(self, validated_data):
        user = self.context['request'].user
        issue = self.context['issue']

        comment = Comment.objects.create(
            description = validated_data['description'],
            author = user,
            issue = issue,
            link = validated_data['link'])

        return comment


class CommentListSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = ['uuid', 'description']


class CommentDetailSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = ['uuid', 'description', 'author', 'issue', 'link', 'created_time']
