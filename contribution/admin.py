from django.contrib import admin

from contribution.models import Project, Contributor


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'type', 'author', 'created_time')


class ContributorAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'project', 'role')


admin.site.register(Project, ProjectAdmin)
admin.site.register(Contributor, ContributorAdmin)
