from django.contrib.auth.models import AbstractUser
from django.db import models, transaction


class User(AbstractUser):
    username = models.CharField(max_length=20, unique=True, null=False, verbose_name="Nom d'utilisateur")
    age = models.IntegerField(null=True)

    can_be_contacted = models.BooleanField(default=False, verbose_name="J'accepte d'être contacté(e)")
    can_data_be_shared = models.BooleanField(default=False, verbose_name="J'accepte le partage de mes données")

    def __str__(self):
        return self.username

    @transaction.atomic
    def disable(self):
        if self.is_active is False:
            return
        self.is_active = False
        self.save()

    @transaction.atomic
    def enable(self):
        if self.is_active is True:
            return
        self.is_active = True
        self.save()

# class Contributor(User):
#     class Meta:
#         verbose_name = 'contributor'
#         verbose_name_plural = 'contributors'
#
#     def __str__(self):
#         return super().__str__()
