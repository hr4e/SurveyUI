# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, include, url

from django.views.generic.base import RedirectView
from SurveyEditor import views


next = '/home'


urlpatterns = patterns('',
    #url(r'^$', RedirectView.as_view(url='home', permanent=False), name='index'),
    url(r'^$', views.welcome, name='welcome'),
    # Home
    url(r'^home/', views.index, name='home'),
    url(r'^editor/', views.editor, name='editor'),
    url(r'^newProject/', views.newProject, name='newProject'),
    url(r'^newQuestion/', views.newQuestion, name='newQuestion'),
    url(r'^login/', views.login, name='login'),
    url(r'^logout/', views.logout, name='logout'),
)