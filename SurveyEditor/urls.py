from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView
from SurveyEditor import views

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='home', permanent=False), name='index'),
    url(r'^home/', views.index, name='home'),
    url(r'^editor/', views.editor, name='editor')
)
