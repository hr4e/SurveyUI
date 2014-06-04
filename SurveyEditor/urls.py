# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, include, url

from django.views.generic.base import RedirectView
from SurveyEditor import views


next = '/editor'


urlpatterns = patterns('',
    #url(r'^$', RedirectView.as_view(url='home', permanent=False), name='index'),
    url(r'^$', views.welcome, name='welcome'),
    url(r'^editor/', views.editor, name='editor'),
    url(r'^newProject/', views.newProject, name='newProject'),
    url(r'^selectProject/', views.selectProject, name='selectProject'),
    url(r'^deleteProject/', views.deleteProject, name='deleteProject'),
    url(r'^newSurvey/', views.newSurvey, name='newSurvey'),
    url(r'^deleteSurvey/', views.deleteSurvey, name='deleteSurvey'),
    url(r'^newPage/', views.newPage, name='newPage'),
    url(r'^deletePage/', views.deletePage, name='deletePage'),
    url(r'^newQuestion/', views.newQuestion, name='newQuestion'),
    url(r'^addExistingQuestion/', views.addExistingQuestion, name='addExistingQuestion'),
    url(r'^deleteQuestion/', views.deleteQuestion, name='deleteQuestion'),
    url(r'^updateQuestion/', views.updateQuestion, name='updateQuestion'),

    url(r'^login/', views.login, name='login'),
    url(r'^logout/', views.logout, name='logout'),
)