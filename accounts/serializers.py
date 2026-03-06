from typing import Any

from rest_framework.serializers import ModelSerializer, ValidationError, CharField, IntegerField

from accounts.models import User
from contribution.models import Project, Issue, Comment, Contributor


class UserCreateSerializer(ModelSerializer):
    password = CharField(style={'input_type': 'password'}, write_only=True, label='Mot de passe')
    password2 = CharField(style={'input_type': 'password'}, write_only=True, label='Confirmer mot de passe')
    age = IntegerField(style={'input_type': 'number'}, label='Age')

    class Meta:
        model = User
        fields = ['id', 'username', 'age', 'can_be_contacted', 'can_data_be_shared', 'password', 'password2']

    def validate(self, data: Any) -> Any:
        """
        Method to validate the data : username and password.
        Args:
            data (Any): the data to be validated

        Returns:
            The validated data otherwise an error is raised.
        """
        if self.instance is None and User.objects.filter(username=data['username']).exists():
            raise ValidationError({'username': "Ce nom d'utilisateur existe déjà."})

        if data.get('password') != data.get('password2'):
            raise ValidationError({'password2': "Les mots de passe ne concordent pas."})

        return data

    @staticmethod
    def validate_password(value: str) -> str:
        """
        Method to validate the password.
        Args:
            value (str): the password to be validated

        Returns:
            The validated password otherwise an error is raised.
        """
        if len(value) < 8:
            raise ValidationError(
                "Le mot de passe doit contenir au moins 8 caractères."
            )
        return value

    @staticmethod
    def validate_age(value: int) -> int:
        """
        Method to validate the age.
        Args:
            value (int): the age to be validated

        Returns:
            The validated age otherwise an error is raised.
        """
        if value is not None and value < 15:
            raise ValidationError(
                {'age': "Vous devez avoir au moins 15 ans."})
        return value

    def create(self, validated_data: Any) -> User:
        """
        Method to create the user.
        Args:
            validated_data (Any): the validated data to be created

        Returns:
            The created user.
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            age=validated_data['age'],
            password=validated_data['password'],
            can_be_contacted=validated_data['can_be_contacted'],
            can_data_be_shared=validated_data['can_data_be_shared']
        )
        return user

    def update(self, instance: User, validated_data: Any) -> User:
        """
        Method to update the user details.
        Args:
            instance (User): the user to be updated
            validated_data (Any): the validated data to be updated

        Returns:
            The updated user instance.
        """
        instance.username = validated_data.get("username", instance.username)
        instance.age = validated_data.get("age", instance.age)
        instance.can_be_contacted = validated_data.get("can_be_contacted", instance.can_be_contacted)
        instance.can_data_be_shared = validated_data.get("can_data_be_shared", instance.can_data_be_shared)

        if "password" in validated_data:
            instance.set_password(validated_data["password"])

        instance.save()

        if not instance.can_data_be_shared:
            self.update_user_data(user=instance)

        return instance

    @staticmethod
    def update_user_data(user: User):
        """
        Method to update the user data when the user has changed their consent to data sharing.
        Args:
            user (User): the user to be updated
        """
        user_contributor_projects = Contributor.objects.filter(user=user).values_list('project_id', flat=True)

        projects_to_clean = Project.objects.exclude(id__in=user_contributor_projects)

        Comment.objects.filter(author=user, issue__project__in=projects_to_clean).delete()

        Issue.objects.filter(author=user, project__in=projects_to_clean).delete()

        Project.objects.filter(author=user, id__in=projects_to_clean).delete()


class UserListSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class UserDetailSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'age', 'can_be_contacted', 'can_data_be_shared']


class UserAdminDetailSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'is_active', 'age', 'can_be_contacted', 'can_data_be_shared']
