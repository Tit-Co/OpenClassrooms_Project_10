from django.contrib.auth.base_user import AbstractBaseUser
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

        cls.contributor_1 = Contributor.objects.create(project=cls.project,
                                                       user=cls.user,
                                                       role='AUTHOR')

        cls.project_2 = Project.objects.create(name='Projet 2',
                                               description='Un super projet 1',
                                               active=True,
                                               type='BACK-END',
                                               author=cls.user_2)

    @staticmethod
    def get_project_list_data(projects: list[Project]):
        return [
            {
                'id': project.pk,
                'name': project.name,
            } for project in projects
        ]


class TestProject(ProjectsTestCase):
    url = reverse_lazy('project-list')

    @staticmethod
    def get_tokens_for_user(user: AbstractBaseUser):
        if not user.is_active:
            raise AuthenticationFailed("User is not active")

        refresh = RefreshToken.for_user(user=user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def test_list(self):
        tokens = self.get_tokens_for_user(user=self.project.author)
        response = self.client.get(path=self.url,
                                   headers={'Authorization': 'Bearer '+tokens['access']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['results'],
                         self.get_project_list_data([self.project_2, self.project]))

    def test_create(self):
        project_count = Project.objects.count()
        tokens = self.get_tokens_for_user(user=self.project.author)
        response = self.client.post(path=self.url,
                                    headers={'Authorization': 'Bearer '+tokens['access']},
                                    data={'name': 'Nouveau projet',
                                          'description': 'Une description du projet nouveau',
                                          'type': 'IOS',
                                          'active': True,
                                          'author': 1})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), project_count + 1)

    def test_update(self):
        tokens = self.get_tokens_for_user(user=self.project.author)
        project_count = Project.objects.count()
        response = self.client.put(path=reverse('project-detail',
                                                kwargs={'pk': self.project.pk}),
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
        response = self.client.put(path=reverse('project-detail',
                                                kwargs={'pk': self.project.pk}),
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
        response = self.client.delete(path=reverse('user-detail',
                                                   kwargs={'pk': self.project_2.pk}),
                                      headers={'Authorization': 'Bearer '+tokens['access']})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), user_count - 1)
        self.user.refresh_from_db()

    def test_update_without_token(self):
        project_count = Project.objects.count()
        response = self.client.put(path=reverse('project-detail',
                                                kwargs={'pk': self.project.pk}),
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

        cls.contributor_1 = Contributor.objects.create(project=cls.project,
                                                       user=cls.user,
                                                       role='AUTHOR')

        cls.project_2 = Project.objects.create(name='Projet 2',
                                               description='Un super projet 2',
                                               active=True,
                                               type='BACK-END',
                                               author=cls.user_2)

        cls.contributor_2 = Contributor.objects.create(project=cls.project_2,
                                                       user=cls.user_2,
                                                       role='AUTHOR')

    @staticmethod
    def get_contributor_list_data(project: Project) -> list[dict]:
        return [
            {
                'id': contributor.pk,
                'project': project.pk,
                'user': contributor.user.id
            } for contributor in Contributor.objects.filter(project=project)
        ]

    @staticmethod
    def get_project(project: Project) -> dict:
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
    url_project_1_contributor_1_detail = reverse("contributor-detail",
                                                 kwargs={"project_pk": 1, "pk": 1})
    url_project_1_subscribe = reverse("project-subscribe", kwargs={"pk": 1})

    @staticmethod
    def get_tokens_for_user(user: AbstractBaseUser):
        if not user.is_active:
            raise AuthenticationFailed("User is not active")

        refresh = RefreshToken.for_user(user=user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def test_list(self):
        tokens = self.get_tokens_for_user(user=self.user_2)
        self.client.post(path=self.url_project_1_subscribe,
                         headers={'Authorization': 'Bearer '+tokens['access']})
        response = self.client.get(path=self.url_project_1_contributors,
                                   headers={'Authorization': 'Bearer '+tokens['access']})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = (
                self.get_contributor_list_data(self.project)
        )

        self.assertCountEqual(response.json()["results"], expected)

    def test_detail(self):
        tokens = self.get_tokens_for_user(user=self.user)
        response = self.client.get(path=self.url_project_1_contributor_1_detail,
                                   headers={'Authorization': 'Bearer '+tokens['access']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"id": 1,
                                           "project": 1,
                                           "user": 1,
                                           "role": "AUTHOR"})

    def test_access_without_token(self):
        response = self.client.get(path=self.url_project_1_contributor_1_detail)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_contributor_access(self):
        tokens = self.get_tokens_for_user(user=self.user_3)
        response = self.client.get(path=self.url_project_1_detail,
                                   headers={'Authorization': 'Bearer ' + tokens['access']})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.post(path=self.url_project_1_subscribe,
                         headers={'Authorization': 'Bearer ' + tokens['access']})
        response = self.client.get(path=self.url_project_1_detail,
                                   headers={'Authorization': 'Bearer ' + tokens['access']})
        data = response.json()
        data['created_time'] = data['created_time'][:19]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data, self.get_project(project=self.project))


class IssuesTestCase(APITestCase):
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

        cls.contributor_1 = Contributor.objects.create(project=cls.project,
                                                       user=cls.user,
                                                       role='AUTHOR')

        cls.contributor_2 = Contributor.objects.create(project=cls.project,
                                                       user=cls.user_2,
                                                       role='CONTRIBUTOR')

        cls.project_2 = Project.objects.create(name='Projet 2',
                                               description='Un super projet 2',
                                               active=True,
                                               type='BACK-END',
                                               author=cls.user_2)

        cls.project_3 = Project.objects.create(name='Projet 3',
                                               description='Un super projet 3',
                                               active=True,
                                               type='FRONT-END',
                                               author=cls.user_3)

        cls.contributor_3 = Contributor.objects.create(project=cls.project_3,
                                                       user=cls.user_3,
                                                       role='AUTHOR')

        cls.contributor_4 = Contributor.objects.create(project=cls.project_2,
                                                       user=cls.user_2,
                                                       role='AUTHOR')

        cls.contributor_5 = Contributor.objects.create(project=cls.project_2,
                                                       user=cls.user,
                                                       role='CONTRIBUTOR')

        cls.issue_1 = Issue.objects.create(name='Issue in project 1',
                                           priority='LOW',
                                           status='TO DO',
                                           author=cls.user,
                                           attribution=cls.user_2,
                                           tag='BUG',
                                           project=cls.project)

        cls.issue_2 = Issue.objects.create(name='Issue in project 2',
                                           priority='MEDIUM',
                                           status='TO DO',
                                           author=cls.user_2,
                                           attribution=cls.user,
                                           tag='TASK',
                                           project=cls.project_2)

    @staticmethod
    def get_issue_list_data(project: Project) -> list[dict]:
        return [
            {
                'id': issue.pk,
                'name': issue.name
            } for issue in Issue.objects.filter(project=project)
        ]

    @staticmethod
    def get_issues(projects: list[Project], user) -> list[dict]:
        issues = []
        for project in projects:
            if Contributor.objects.filter(project=project, user=user).exists():
                issues.extend(Issue.objects.filter(project=project))

        return [
            {
                'id': issue.pk,
                'name': issue.name
            } for issue in issues
        ]

    @staticmethod
    def get_issue_with_comments(issue: Issue) -> dict:
        return {
            'id': issue.pk,
            'name': issue.name,
            'priority': issue.priority,
            'status': issue.status,
            'author': issue.author.id,
            'attribution': issue.attribution.id,
            'tag': issue.tag,
            'created_time': issue.created_time.isoformat()[:19],
            'comments': []
        }

    @staticmethod
    def get_issue_without_comments(issue: Issue) -> dict:
        return {
            'id': issue.pk,
            'name': issue.name,
            'priority': issue.priority,
            'status': issue.status,
            'author': issue.author.id,
            'attribution': issue.attribution.id,
            'tag': issue.tag,
            'created_time': issue.created_time.isoformat()[:19]
        }


class TestIssue(IssuesTestCase):
    url_project_1_detail = reverse_lazy('project-detail', kwargs={"pk": 1})

    url_project_1_issues = reverse("issue-list", kwargs={"project_pk": 1})

    url_project_1_issue_1_detail = reverse("issue-detail",
                                           kwargs={"project_pk": 1, "pk": 1})

    url_issue_1_detail = reverse("issue-detail", kwargs={"pk": 1})

    url_project_1_subscribe = reverse("project-subscribe", kwargs={"pk": 1})

    url_issues = reverse("issue-list", kwargs={})

    @staticmethod
    def get_tokens_for_user(user: AbstractBaseUser):
        if not user.is_active:
            raise AuthenticationFailed("User is not active")

        refresh = RefreshToken.for_user(user=user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def test_list(self):
        tokens = self.get_tokens_for_user(user=self.user)

        response = self.client.get(path=self.url_issues,
                                   headers={'Authorization': 'Bearer ' + tokens['access']})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = (
            self.get_issues(projects=[self.project, self.project_2],
                            user=self.user)
        )
        self.assertCountEqual(response.json()["results"], expected)

    def test_list_in_project(self):
        tokens = self.get_tokens_for_user(user=self.user_2)

        response = self.client.get(path=self.url_project_1_issues,
                                   headers={'Authorization': 'Bearer '+tokens['access']})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json()["results"], self.get_issue_list_data(self.project))

    def test_detail_in_project(self):
        tokens = self.get_tokens_for_user(user=self.user_2)
        response = self.client.get(path=self.url_project_1_issue_1_detail,
                                   headers={'Authorization': 'Bearer '+tokens['access']})
        data = response.json()
        data['created_time'] = data['created_time'][:19]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), self.get_issue_without_comments(issue=self.issue_1))

    def test_detail(self):
        tokens = self.get_tokens_for_user(user=self.user_2)
        response = self.client.get(path=self.url_issue_1_detail,
                                   headers={'Authorization': 'Bearer '+tokens['access']})
        data = response.json()
        data['created_time'] = data['created_time'][:19]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), self.get_issue_with_comments(issue=self.issue_1))

    def test_non_contributor_list_access(self):
        tokens = self.get_tokens_for_user(user=self.user_3)
        response = self.client.get(path=self.url_project_1_issues,
                                   headers={'Authorization': 'Bearer ' + tokens['access']})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.post(path=self.url_project_1_subscribe,
                         headers={'Authorization': 'Bearer ' + tokens['access']})
        response = self.client.get(path=self.url_project_1_issues,
                                   headers={'Authorization': 'Bearer ' + tokens['access']})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["results"],
                         self.get_issue_list_data(project=self.project))

    def test_non_contributor_detail_access(self):
        tokens = self.get_tokens_for_user(user=self.user_3)
        response = self.client.get(path=self.url_project_1_issue_1_detail,
                                   headers={'Authorization': 'Bearer ' + tokens['access']})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.post(path=self.url_project_1_subscribe,
                         headers={'Authorization': 'Bearer ' + tokens['access']})
        response = self.client.get(path=self.url_project_1_issue_1_detail,
                                   headers={'Authorization': 'Bearer ' + tokens['access']})

        data = response.json()
        data['created_time'] = data['created_time'][:19]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data, self.get_issue_without_comments(issue=self.issue_1))


class CommentsTestCase(APITestCase):
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

        cls.contributor_1 = Contributor.objects.create(project=cls.project,
                                                       user=cls.user,
                                                       role='AUTHOR')

        cls.contributor_2 = Contributor.objects.create(project=cls.project,
                                                       user=cls.user_2,
                                                       role='CONTRIBUTOR')

        cls.project_2 = Project.objects.create(name='Projet 2',
                                               description='Un super projet 2',
                                               active=True,
                                               type='BACK-END',
                                               author=cls.user_2)

        cls.project_3 = Project.objects.create(name='Projet 3',
                                               description='Un super projet 3',
                                               active=True,
                                               type='FRONT-END',
                                               author=cls.user_3)

        cls.contributor_3 = Contributor.objects.create(project=cls.project_3,
                                                       user=cls.user_3,
                                                       role='AUTHOR')

        cls.contributor_4 = Contributor.objects.create(project=cls.project_2,
                                                       user=cls.user_2,
                                                       role='AUTHOR')

        cls.contributor_5 = Contributor.objects.create(project=cls.project_2,
                                                       user=cls.user,
                                                       role='CONTRIBUTOR')

        cls.issue_1 = Issue.objects.create(name='Issue in project 1',
                                           priority='LOW',
                                           status='TO DO',
                                           author=cls.user,
                                           attribution=cls.user_2,
                                           tag='BUG',
                                           project=cls.project)

        cls.issue_2 = Issue.objects.create(name='Issue in project 2',
                                           priority='MEDIUM',
                                           status='TO DO',
                                           author=cls.user_2,
                                           attribution=cls.user,
                                           tag='TASK',
                                           project=cls.project_2)

        cls.issue_3 = Issue.objects.create(name='Issue in project 3',
                                           priority='HIGH',
                                           status='TO DO',
                                           author=cls.user_3,
                                           attribution=cls.user_3,
                                           tag='BUG',
                                           project=cls.project_3)

        cls.comment_1 = Comment.objects.create(description='Description comment 1',
                                               link='http://127.0.0.1:8000/project/1/issue/1/',
                                               issue=cls.issue_1,
                                               author=cls.user)

        cls.comment_2 = Comment.objects.create(description='Description comment 2',
                                               link='http://127.0.0.1:8000/project/2/issue/2/',
                                               issue=cls.issue_2,
                                               author=cls.user_2)

        cls.comment_3 = Comment.objects.create(description='Description comment 3',
                                               link='http://127.0.0.1:8000/project/3/issue/3/',
                                               issue=cls.issue_3,
                                               author=cls.user_3)

        cls.comment_4 = Comment.objects.create(description='Description comment 4',
                                               link='http://127.0.0.1:8000/project/1/issue/1/',
                                               issue=cls.issue_1,
                                               author=cls.user_2)

    @staticmethod
    def get_comment_list_data(comments: list[Comment]) -> list[dict]:
        return [
            {
                'uuid': str(comment.uuid),
                'description': comment.description
            } for comment in comments
        ]

    @staticmethod
    def get_comment_detail_data(comment: Comment) -> dict:
        return {
            'uuid': str(comment.uuid),
            'description': comment.description,
            'link': comment.link,
            'issue': comment.issue.id,
            'author': comment.author.id,
            'created_time': comment.created_time.isoformat()[:19]
        }

    def get_issue_detail_data_with_comments(self, issue: Issue) -> dict:
        return {
            'id': issue.pk,
            'name': issue.name,
            'priority': issue.priority,
            'status': issue.status,
            'author': issue.author.id,
            'attribution': issue.attribution.id,
            'tag': issue.tag,
            'created_time': issue.created_time.isoformat()[:19],
            'comments': [self.get_comment_detail_data(comment)
                         for comment in Comment.objects.filter(issue=issue).order_by("created_time")]
        }


class TestComment(CommentsTestCase):
    url_project_1_subscribe = reverse("project-subscribe", kwargs={"pk": 1})

    url_issue_1_comments = reverse("comment-list", kwargs={"issue_pk": 1})

    url_issue_1_detail = reverse("issue-detail", kwargs={"pk": 1})

    @staticmethod
    def get_tokens_for_user(user: AbstractBaseUser):
        if not user.is_active:
            raise AuthenticationFailed("User is not active")

        refresh = RefreshToken.for_user(user=user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def test_list(self):
        tokens = self.get_tokens_for_user(user=self.user)

        response = self.client.get(path=self.url_issue_1_comments,
                                   headers={'Authorization': 'Bearer ' + tokens['access']})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = (
            self.get_comment_list_data(comments=[self.comment_1, self.comment_4])
        )
        self.assertCountEqual(response.json()["results"], expected)

    def test_detail(self):
        comment_pk = str(self.comment_1.uuid)
        url_issue_1_comment_1_detail = reverse("comment-detail",
                                               kwargs={"issue_pk": 1, "pk": comment_pk})
        tokens = self.get_tokens_for_user(user=self.user)

        response = self.client.get(path=url_issue_1_comment_1_detail,
                                   headers={'Authorization': 'Bearer ' + tokens['access']})

        data = response.json()
        data['created_time'] = data['created_time'][:19]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data, self.get_comment_detail_data(comment=self.comment_1))

    def test_non_contributor_list_access(self):
        tokens = self.get_tokens_for_user(user=self.user_3)
        response = self.client.get(path=self.url_issue_1_comments,
                                   headers={'Authorization': 'Bearer ' + tokens['access']})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.post(path=self.url_project_1_subscribe,
                         headers={'Authorization': 'Bearer ' + tokens['access']})
        response = self.client.get(path=self.url_issue_1_comments,
                                   headers={'Authorization': 'Bearer ' + tokens['access']})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = (
            self.get_comment_list_data(comments=[self.comment_1, self.comment_4])
        )
        self.assertCountEqual(response.json()["results"], expected)

    def test_non_contributor_detail_access(self):
        comment_pk = str(self.comment_1.uuid)
        url_issue_1_comment_1_detail = reverse("comment-detail",
                                               kwargs={"issue_pk": 1, "pk": comment_pk})

        tokens = self.get_tokens_for_user(user=self.user_3)
        response = self.client.get(path=url_issue_1_comment_1_detail,
                                   headers={'Authorization': 'Bearer ' + tokens['access']})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.post(path=self.url_project_1_subscribe,
                         headers={'Authorization': 'Bearer ' + tokens['access']})
        response = self.client.get(path=url_issue_1_comment_1_detail,
                                   headers={'Authorization': 'Bearer ' + tokens['access']})

        data = response.json()
        data['created_time'] = data['created_time'][:19]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data, self.get_comment_detail_data(comment=self.comment_1))

    def test_issue_detail_with_comments(self):
        tokens = self.get_tokens_for_user(user=self.user)

        response = self.client.get(path=self.url_issue_1_detail,
                                   headers={'Authorization': 'Bearer ' + tokens['access']})

        data = response.json()
        data['created_time'] = data['created_time'][:19]
        for comment in data['comments']:
            comment['created_time'] = comment['created_time'][:19]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data, self.get_issue_detail_data_with_comments(issue=self.issue_1))
