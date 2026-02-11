from datetime import datetime

from django.db import models
from django.conf import settings


class Project(models.Model):
    name = models.CharField(max_length=30, unique=False, null=False, blank=False, verbose_name='Nom du projet')

    description = models.TextField(max_length=100, unique=False, null=True, blank=True, verbose_name='Description')

    TYPES = (
        ('BACK-END', 'Back-end'),
        ('FRONT-END', 'Front-end'),
        ('IOS', 'Ios'),
        ('ANDROID', 'Android'),
    )

    type = models.CharField(max_length=10, choices=TYPES, verbose_name='Type', null=False, blank=False)

    author = models.ForeignKey(to=settings.AUTH_USER_MODEL,
                               on_delete=models.CASCADE,
                               related_name='authors',
                               verbose_name='Auteur')

    contributors = models.ManyToManyField(to=settings.AUTH_USER_MODEL,
                                          through='Contributor',
                                          related_name='contributors',
                                          verbose_name='Contributeurs')

    created_time = models.DateTimeField(default=datetime.now, blank=True, verbose_name='Date de creation')

    def __str__(self):
        return self.name


class Contributor(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Utilisateur')

    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name='Projet')

    ROLES = (
        ('AUTHOR', 'Auteur'),
        ('CONTRIBUTOR', 'Contributeur'),
    )

    role = models.CharField(max_length=20, choices=ROLES, verbose_name='Role')

    class Meta:
        constraints = (models.UniqueConstraint(fields=['user', 'project'], name='unique_contributor'),)
