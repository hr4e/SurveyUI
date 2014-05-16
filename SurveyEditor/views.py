from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.template import RequestContext, loader

def index(request):
    template = loader.get_template('SurveyEditor/index.html')
    world = "Django World"
    context = RequestContext(request, {
    })
    return HttpResponse(template.render(context))


def editor(request):
    template = loader.get_template('SurveyEditor/editor.html')
    world = "Django World"
    context = RequestContext(request, {
    })
    return HttpResponse(template.render(context))