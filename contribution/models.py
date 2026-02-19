import uuid
from datetime import datetime

from django.db import models
from django.conf import settings


class Project(models.Model):
    name = models.CharField(max_length=30, unique=False, null=False, blank=False, verbose_name='Nom du projet')

    description = models.TextField(max_length=500, unique=False, null=True, blank=True, verbose_name='Description')

    active = models.BooleanField(default=True, verbose_name='Actif')

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

    def disable(self):
        if not self.active :
            return
        self.active = False
        issues = Issue.objects.filter(project=self)
        for issue in issues:
            issue.disable()
        self.save()

    def enable(self):
        if self.active:
            return
        self.active = True
        issues = Issue.objects.filter(project=self)
        for issue in issues:
            issue.enable()
        self.save()


class Contributor(models.Model):
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Utilisateur')

    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, verbose_name='Projet')

    ROLES = (
        ('AUTHOR', 'Auteur'),
        ('CONTRIBUTOR', 'Contributeur'),
    )

    role = models.CharField(max_length=20, choices=ROLES, verbose_name='Role')

    class Meta:
        constraints = (models.UniqueConstraint(fields=['user', 'project'], name='unique_contributor'),)


class Issue(models.Model):
    name = models.CharField(max_length=100, unique=False, null=False, blank=False, verbose_name='Nom du problème')

    active = models.BooleanField(default=True, verbose_name='Actif')

    PRIORITY_CHOICES = (
        ('LOW', 'Faible'),
        ('MEDIUM', 'Moyenne'),
        ('HIGH', 'Haute'),
    )
    priority = models.CharField(max_length=20,
                                choices=PRIORITY_CHOICES,
                                null=False,
                                blank=False,
                                default='HIGH',
                                verbose_name='Priorité')

    STATUS_CHOICES = (
        ('TO DO', 'A faire'),
        ('IN PROGRESS', 'En cours'),
        ('FINISHED', 'Terminé'),
    )
    status = models.CharField(max_length=20,
                              choices=STATUS_CHOICES,
                              null=False,
                              blank=False,
                              default='TO DO',
                              verbose_name='Statut de progression')

    author = models.ForeignKey(to=settings.AUTH_USER_MODEL,
                               on_delete=models.CASCADE,
                               related_name='issue_authors',
                               verbose_name='Auteur')

    attribution = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Attribué à')

    BALISE_CHOICES = (
        ('BUG', 'Bug'),
        ('TASK', 'Tâche'),
        ('IMPROVEMENT', 'Amélioration'),
    )
    balise = models.CharField(max_length=20,
                              default='BUG',
                              null=False,
                              blank=False,
                              choices=BALISE_CHOICES,
                              verbose_name='Balise')

    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, verbose_name='Projet')

    created_time = models.DateTimeField(default=datetime.now, blank=True, verbose_name='Date de creation')

    def __str__(self):
        return self.name

    def disable(self):
        if not self.active :
            return
        self.active = False
        comments = Comment.objects.filter(issue=self)
        for comment in comments:
            comment.disable()
        self.save()

    def enable(self):
        if self.active:
            return
        self.active = True
        comments = Comment.objects.filter(issue=self)
        for comment in comments:
            comment.enable()
        self.save()


class Comment(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, verbose_name='UUID')

    active = models.BooleanField(default=True, verbose_name='Actif')

    description = models.TextField(max_length=500, unique=False, null=True, blank=True, verbose_name='Description')

    author = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Auteur')

    issue = models.ForeignKey(to=Issue, on_delete=models.CASCADE, verbose_name='Issue')

    link = models.URLField(max_length=200, null=False, blank=False, verbose_name='Link')

    created_time = models.DateTimeField(default=datetime.now, blank=True, verbose_name='Date de creation')

    class Meta:
        constraints = (models.UniqueConstraint(fields=['author', 'issue'], name='unique_comment'),)

    def __str__(self):
        return self.description

    def disable(self):
        if not self.active :
            return
        self.active = False
        self.save()

    def enable(self):
        if self.active:
            return
        self.active = True
        self.save()
