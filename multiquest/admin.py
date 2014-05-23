from django.contrib import admin
from multiquest.models import *

class MultiQuestAdmin(admin.ModelAdmin):
    list_display = ('id','questionTag', 'questionText', 'responseType', 'description', 'explanation','lastUpdate')
    ordering = ('questionTag',)

admin.site.register(Question, MultiQuestAdmin)  #register models for admin
admin.site.register(ResponseChoice)
admin.site.register(Page)
admin.site.register(Project)
admin.site.register(UserProject)
admin.site.register(ProjectAttributes)
admin.site.register(Questionnaire)
admin.site.register(QuestionnaireAttributes)
admin.site.register(QuestionnairePage)
admin.site.register(ProjectQuestionnaire)
admin.site.register(PageAnalysis)
admin.site.register(QuestionnaireAnalysis)
admin.site.register(PageQuestion)
admin.site.register(Respondent)
admin.site.register(Submission)
admin.site.register(Response)
admin.site.register(ResponseSelection)
admin.site.register(PageAttributes)
admin.site.register(SubmissionAnalysis)
admin.site.register(RiskCalculation)
admin.site.register(RiskSubmission)
