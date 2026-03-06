from django.urls import reverse_lazy, reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed


from accounts.models import User


class AccountsTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Method to initialize the test data
        """
        cls.user = User.objects.create(username='andrew',
                                       age=18,
                                       is_active=True,
                                       can_be_contacted=False,
                                       can_data_be_shared=False,
                                       password='tc1_Std18')

        cls.user_2 = User.objects.create(username='Benoit',
                                         is_active=True,
                                         age=46,
                                         can_be_contacted=True,
                                         can_data_be_shared=False,
                                         password='tc2_Std29')

    @staticmethod
    def get_user_list_data(users: list[User]):
        """
        Method to return a list of the user restricted data.
        Args:
            users (list[User]): the users to be listed

        Returns:
            A list of the users restricted data
        """
        return [
            {
                'id': user.pk,
                'username': user.username,
            } for user in users
        ]


class TestUser(AccountsTestCase):
    url = reverse_lazy('user-list')

    @staticmethod
    def get_tokens_for_user(user: User):
        """
        Method to return a token for the given user.
        Args:
            user (User): the user

        Returns:
            The token for the given user.
        """
        if not user.is_active:
            raise AuthenticationFailed("User is not active")

        refresh = RefreshToken.for_user(user=user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def test_list(self):
        """
        Method to test if the user can be listed.
        """
        response = self.client.get(path=self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['results'],
                         self.get_user_list_data([self.user, self.user_2]))

    def test_create(self):
        """
        Method to test if the user can be created.
        """
        user_count = User.objects.count()
        response = self.client.post(path=self.url, data={'username': 'another_user',
                                                         'age': 28,
                                                         'can_be_contacted': False,
                                                         'can_data_be_shared': False,
                                                         'password': 'sc7_Smn70',
                                                         'password2': 'sc7_Smn70'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), user_count + 1)

    def test_update(self):
        """
        Method to test if the user can be updated.
        """
        tokens = self.get_tokens_for_user(user=self.user_2)
        user_count = User.objects.count()
        response = self.client.put(path=reverse('user-detail',
                                                kwargs={'pk': self.user_2.pk}),
                                   headers={'Authorization': 'Bearer '+tokens['access']},
                                   data={'username': 'Benoit',
                                         'age': 47,
                                         'can_be_contacted': False,
                                         'can_data_be_shared': False,
                                         'password': 'tc2_Std30',
                                         'password2': 'tc2_Std30'
                                         })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.count(), user_count)

    def test_delete(self):
        """
        Method to test if the user can be deleted.
        """
        tokens = self.get_tokens_for_user(user=self.user_2)
        user_count = User.objects.count()
        response = self.client.delete(path=reverse('user-detail',
                                                   kwargs={'pk': self.user_2.pk}),
                                      headers={'Authorization': 'Bearer '+tokens['access']})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), user_count - 1)
        self.user.refresh_from_db()

    def test_a_user_delete_b_user(self):
        """
        Method to test if a user can delete another user account.
        """
        tokens = self.get_tokens_for_user(user=self.user_2)
        user_count = User.objects.count()
        response = self.client.delete(path=reverse('user-detail',
                                                   kwargs={'pk': self.user.pk}),
                                      headers={'Authorization': 'Bearer '+tokens['access']})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(User.objects.count(), user_count)

    def test_update_without_token(self):
        """
        Method to test if the user can be updated without authentication token.
        """
        user_count = User.objects.count()
        response = self.client.put(path=reverse('user-detail',
                                                kwargs={'pk': self.user_2.pk}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(User.objects.count(), user_count)

    def test_update_hashed_password(self):
        """
        Method to test if the user can be updated and if password is hashed.
        """
        tokens = self.get_tokens_for_user(user=self.user_2)
        user_count = User.objects.count()
        password_to_test = 'tc2_Std30'
        response = self.client.put(path=reverse('user-detail',
                                                kwargs={'pk': self.user_2.pk}),
                                   headers={'Authorization': 'Bearer ' + tokens['access']},
                                   data={'username': 'Benoit',
                                         'age': 47,
                                         'can_be_contacted': False,
                                         'can_data_be_shared': False,
                                         'password': password_to_test,
                                         'password2': password_to_test
                                         })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.count(), user_count)
        user = User.objects.get(pk=response.json().get('id'))
        self.assertNotEqual(user.password, password_to_test)
