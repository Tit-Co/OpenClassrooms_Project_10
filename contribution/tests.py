from django.urls import reverse_lazy, reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from accounts.models import User
from contribution.models import Project, Contributor, Issue, Comment


class ProjectsTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Benoit',
                                                         is_active=True,
                                                         age=46,
                                                         can_be_contacted=True,
                                                         can_data_be_shared=False,
                                                         password='tc2_Std29')

        cls.user_2 = User.objects.create(username='andrew',
                                                           age=18,
                                                           is_active=True,
                                                           can_be_contacted=False,
                                                           can_data_be_shared=False,
                                                           password='tc1_Std18')

        cls.project = Project.objects.create(name='Projet 1',
                                             description='Un super projet 1',
                                             active=True,
                                             type='FRONT-END',
                                             author=cls.user)

        cls.project_2 = Project.objects.create(name='Projet 2',
                                               description='Un super projet 1',
                                               active=True,
                                               type='BACK-END',
                                               author=cls.user_2)

    @staticmethod
    def get_project_list_data(projects):
        return [
            {
                'id': project.pk,
                'name': project.name,
            } for project in projects
        ]


class TestProject(ProjectsTestCase):
    url = reverse_lazy('project-list')

    @staticmethod
    def get_tokens_for_user(user):
        if not user.is_active:
            raise AuthenticationFailed("User is not active")

        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def test_list(self):
        tokens = self.get_tokens_for_user(self.project.author)
        response = self.client.get(self.url, headers={'Authorization': 'Bearer '+tokens['access']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['results'], self.get_project_list_data([self.project,
                                                                                 self.project_2]))

    def test_create(self):
        project_count = Project.objects.count()
        tokens = self.get_tokens_for_user(self.project.author)
        response = self.client.post(self.url,
                                    headers={'Authorization': 'Bearer '+tokens['access']},
                                    data={'name': 'Nouveau projet',
                                          'description': 'Une description du projet nouveau',
                                          'type': 'IOS',
                                          'active': True,
                                          'author': 1})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), project_count + 1)

    def test_update(self):
        tokens = self.get_tokens_for_user(self.project.author)
        project_count = Project.objects.count()
        response = self.client.put(reverse('project-detail', kwargs={'pk': self.project.pk}),
                                   headers={'Authorization': 'Bearer '+tokens['access']},
                                   data={'name': 'Nouveau grand projet',
                                         'description': 'Une description du nouveau projet',
                                         'type': 'IOS',
                                         'active': True,
                                         'author': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Project.objects.count(), project_count)

    def test_a_user_update_b_project(self):
        tokens = self.get_tokens_for_user(self.project_2.author)
        project_count = Project.objects.count()
        response = self.client.put(reverse('project-detail', kwargs={'pk': self.project.pk}),
                                   headers={'Authorization': 'Bearer '+tokens['access']},
                                   data={'name': 'Nouveau grand projet',
                                         'description': 'Une description du nouveau projet',
                                         'type': 'IOS',
                                         'active': True,
                                         'author': 1})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Project.objects.count(), project_count)

    def test_delete(self):
        tokens = self.get_tokens_for_user(self.user_2)
        user_count = User.objects.count()
        response = self.client.delete(reverse('user-detail', kwargs={'pk': self.project_2.pk}),
                                      headers={'Authorization': 'Bearer '+tokens['access']})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), user_count - 1)
        self.user.refresh_from_db()

    def test_update_without_token(self):
        project_count = Project.objects.count()
        response = self.client.put(reverse('project-detail', kwargs={'pk': self.project.pk}),
                                   data={'name': 'Nouveau grand projet',
                                         'description': 'Une description du nouveau projet',
                                         'type': 'IOS',
                                         'active': True,
                                         'author': 1})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Project.objects.count(), project_count)


class ContributorsTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Benoit',
                                                         is_active=True,
                                                         age=46,
                                                         can_be_contacted=True,
                                                         can_data_be_shared=False,
                                                         password='tc2_Std29')

        cls.user_2 = User.objects.create(username='andrew',
                                                           age=18,
                                                           is_active=True,
                                                           can_be_contacted=False,
                                                           can_data_be_shared=False,
                                                           password='tc1_Std18')

        cls.user_3 = User.objects.create(username='martine',
                                         age=35,
                                         is_active=True,
                                         can_be_contacted=False,
                                         can_data_be_shared=True,
                                         password='tc3_Std20')

        cls.project = Project.objects.create(name='Projet 1',
                                             description='Un super projet 1',
                                             active=True,
                                             type='FRONT-END',
                                             author=cls.user)

        cls.contributor_1 = Contributor.objects.create(project=cls.project, user=cls.user, role='AUTHOR')

        cls.project_2 = Project.objects.create(name='Projet 2',
                                               description='Un super projet 1',
                                               active=True,
                                               type='BACK-END',
                                               author=cls.user_2)

        cls.contributor_2 = Contributor.objects.create(project=cls.project_2, user=cls.user_2, role='AUTHOR')

    @staticmethod
    def get_contributor_list_data(project):
        return [
            {
                'id': contributor.pk,
                'user': contributor.user.id,
                'project' : project.id
            } for contributor in Contributor.objects.filter(project=project)
        ]

    @staticmethod
    def get_projet(project):
        return {
            'id': project.pk,
            'name': project.name,
            'description': project.description,
            'type': project.type,
            'author': project.author.id,
            'created_time': project.created_time.isoformat()[:19],
            'issues': []
        }


class TestContributor(ContributorsTestCase):
    url_project_1_detail = reverse_lazy('project-detail', kwargs={"pk": 1})

    url_project_1_contributors = reverse("contributor-list", kwargs={"project_pk": 1})
    url_project_1_contributor_1_detail = reverse("contributor-detail", kwargs={"project_pk": 1, "pk": 1})
    url_project_1_subscribe = reverse("project-subscribe", kwargs={"pk": 1})

    @staticmethod
    def get_tokens_for_user(user):
        if not user.is_active:
            raise AuthenticationFailed("User is not active")

        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def test_list(self):
        tokens = self.get_tokens_for_user(self.user_2)
        self.client.post(self.url_project_1_subscribe,
                         headers={'Authorization': 'Bearer '+tokens['access']})
        response = self.client.get(self.url_project_1_contributors,
                                   headers={'Authorization': 'Bearer '+tokens['access']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), self.get_contributor_list_data(self.project))

    def test_detail(self):
        tokens = self.get_tokens_for_user(self.user_2)
        response = self.client.get(self.url_project_1_contributor_1_detail,
                        headers={'Authorization': 'Bearer '+tokens['access']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {
            "id": 1,
            "project": 1,
            "user": 1,
            "role": "AUTHOR"
        })

    def test_access_without_token(self):
        response = self.client.get(self.url_project_1_contributor_1_detail)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_contributor_access(self):
        tokens = self.get_tokens_for_user(self.user_3)
        response = self.client.get(self.url_project_1_detail, headers={'Authorization': 'Bearer ' + tokens['access']})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.post(self.url_project_1_subscribe,
                         headers={'Authorization': 'Bearer ' + tokens['access']})
        response = self.client.get(self.url_project_1_detail, headers={'Authorization': 'Bearer ' + tokens['access']})
        data = response.json()
        data['created_time'] = data['created_time'][:19]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data, self.get_projet(self.project))
