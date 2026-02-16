"""
URL configuration for softdesk_support project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from rest_framework import routers
from rest_framework_nested.routers import NestedDefaultRouter

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.views import UserViewSet
from contribution.views import ProjectViewSet, IssueViewSet, CommentViewSet, ContributorViewSet

router = routers.SimpleRouter()
router.register('user', UserViewSet, basename='user')
router.register('project', ProjectViewSet, basename='project')

project_router = NestedDefaultRouter(router, 'project', lookup='project')
project_router.register('issue', IssueViewSet, basename='issue')
project_router.register('contributor', ContributorViewSet, basename='contributor')

router.register('issue', IssueViewSet, basename='issue')
issue_router = NestedDefaultRouter(router, 'issue', lookup='issue')
issue_router.register('comment', CommentViewSet, basename='comment')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include(router.urls)),
    path('api/', include(project_router.urls)),
    path('api/', include(issue_router.urls)),
]
