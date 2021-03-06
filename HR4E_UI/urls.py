from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'HR4E_UI.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^multiquest/', include('multiquest.urls')),
    url(r'', include('SurveyEditor.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
