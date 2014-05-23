from django.shortcuts import render

from django.forms import ModelForm

# Create your views here.
from django.http import HttpResponse
from django.template import RequestContext, loader


def index(request):
    template = loader.get_template('home.html')
    context = RequestContext(request, {
        'yes':'yesssssss',
    })
    return HttpResponse(template.render(context))


def editor(request):
    template = loader.get_template('editor.html')
    context = RequestContext(request, {
    })
    return HttpResponse(template.render(context))