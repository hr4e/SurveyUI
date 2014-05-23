from django.contrib import admin
# Register your models here.
from SurveyEditor.models import Question, Page, Project

admin.site.register(Question)
admin.site.register(Page)
admin.site.register(Project)