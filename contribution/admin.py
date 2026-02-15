from django.contrib import admin

from contribution.models import Project, Contributor, Issue, Comment


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'active', 'name', 'description', 'type', 'author', 'created_time')


class ContributorAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'project', 'role')


class IssueAdmin(admin.ModelAdmin):
    list_display = ('id', 'active', 'name', 'priority', 'status', 'author', 'attribution', 'balise', 'project',
                    'created_time')


class CommentAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'active', 'description', 'author', 'issue', 'link', 'created_time')


admin.site.register(Project, ProjectAdmin)
admin.site.register(Contributor, ContributorAdmin)
admin.site.register(Issue, IssueAdmin)
admin.site.register(Comment, CommentAdmin)
