from rest_framework.serializers import ModelSerializer, ValidationError

from contribution.models import Project, Contributor


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
    class Meta:
        model = Project
        fields = '__all__'


class ProjectAdminDetailSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
