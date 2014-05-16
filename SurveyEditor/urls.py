from django.conf.urls import patterns, url

from SurveyEditor import views

urlpatterns = patterns('',
    url(r'^home/', views.index, name='index'),
    url(r'^editor/', views.editor, name='editor')
)
