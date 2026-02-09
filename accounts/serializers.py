from rest_framework.serializers import ModelSerializer, ValidationError, CharField

from accounts.models import User


class UserCreateSerializer(ModelSerializer):
    password = CharField(style={'input_type': 'password'}, write_only=True, label='Mot de passe')
    password2 = CharField(style={'input_type': 'password'}, write_only=True, label='Confirmer mot de passe')

    class Meta:
        model = User
        fields = ['id', 'username', 'age', 'can_be_contacted', 'can_data_be_shared', 'password', 'password2']

    def validate(self, data):
        if self.instance is None and User.objects.filter(username=data['username']).exists():
            raise ValidationError({'username': "Ce nom d'utilisateur existe déjà."})

        if data['age'] < 15:
            raise ValidationError({'age': "Vous devez avoir au moins 15 ans."})

        if data['password'] != data['password2']:
            raise ValidationError({'password2': "Les mots de passe ne concordent pas."})

        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            age=validated_data['age'],
            password=validated_data['password'],
            can_be_contacted=validated_data['can_be_contacted'],
            can_data_be_shared=validated_data['can_data_be_shared']
        )
        return user

    def update(self, instance, validated_data):
        instance.username = validated_data.get("username", instance.username)
        instance.age = validated_data.get("age", instance.age)
        instance.can_be_contacted = validated_data.get("can_be_contacted", instance.can_be_contacted)
        instance.can_data_be_shared = validated_data.get("can_data_be_shared", instance.can_data_be_shared)
        instance.password = validated_data.get("password", instance.password)
        instance.save()
        return instance


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
