from django.shortcuts import render

from SurveyEditor.models import Question
from django.forms import ModelForm

# Create your views here.
from django.http import HttpResponse
from django.template import RequestContext, loader

class QuestionForm(ModelForm):
    class Meta:
        model = Question
        fields = ['questionTag', 'questionText', 'helpText', 'explanation']

def index(request):
    template = loader.get_template('home.html')
    context = RequestContext(request, {
        'yes':'yesssssss',
    })
    return HttpResponse(template.render(context))


def editor(request):
    template = loader.get_template('editor.html')
    form = QuestionForm()
    context = RequestContext(request, {
        'hum' : form,
    })
    return HttpResponse(template.render(context))