from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.template import RequestContext, loader


def index(request):
    template = loader.get_template('SurveyEditor/index.html')
    world = "Django World"
    context = RequestContext(request, {
        'arb_name': world,
        'hello': 'oooooo wow',

    })
    return HttpResponse(template.render(context))