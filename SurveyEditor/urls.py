# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, include, url

from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from SurveyEditor import views

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='home', permanent=False), name='index'),
    # Home
    (r'home/', TemplateView.as_view(template_name='home.html')),
    (r'editor/', TemplateView.as_view(template_name='editor.html')),
)