# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, include, url

from django.views.generic.base import RedirectView
from SurveyEditor import views

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='home', permanent=False), name='index'),
    # Home
    url(r'^home/', views.index, name='home'),
    url(r'^editor/', views.editor, name='editor'),
)