from django.urls import path, include

from rest_framework import routers
from rest_framework_nested.routers import NestedDefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.views import UserViewSet
from contribution.views import ProjectViewSet, IssueViewSet, CommentViewSet, ContributorViewSet


router = routers.SimpleRouter()
router.register('users', UserViewSet, basename='user')
router.register('projects', ProjectViewSet, basename='project')

project_router = NestedDefaultRouter(router, 'projects', lookup='project')
project_router.register('issues', IssueViewSet, basename='issue')
project_router.register('contributors', ContributorViewSet, basename='contributor')

router.register('issues', IssueViewSet, basename='issue')
issue_router = NestedDefaultRouter(router, 'issues', lookup='issue')
issue_router.register('comments', CommentViewSet, basename='comment')


urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
    path('', include(project_router.urls)),
    path('', include(issue_router.urls)),
]
