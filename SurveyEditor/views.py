from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as auth_login, logout as auth_logout

from django.shortcuts import render, render_to_response

from django.forms import ModelForm
from multiquest.models import Question, Project

# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader

class QuestionForm(ModelForm):
    class Meta:
        model = Question
        fields = ['language', 'questionTag', 'questionText', 'helpText', 'explanation']

class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = '__all__'


def login(request):
    state = next = username = password = ''

    if request.GET:  
        next = request.GET['next']

    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                state = "You're successfully logged in!"
                if next == "":
                    return HttpResponseRedirect('home/')
                else:
                    return HttpResponseRedirect(next)
            else:
                state = "Your account is not active, please contact the site admin."
        else:
            state = "Your username and/or password were incorrect."

    return render_to_response(
        'registration/login.html',
        {
        'msg':state,
        'username': username,
        'next':next,
        },
        context_instance=RequestContext(request)
    )

@login_required()
def logout(request):
    auth_logout(request, request.user)
    return HttpResponseRedirect('/test')

@login_required()
def index(request):
    template = loader.get_template('SurveyEditor/home.html')

    allProjects = Project.objects.all()
    form = ProjectForm()

    context = RequestContext(request, {
        'allProjects' : allProjects,
        'projectForm' : form,
    })
    return HttpResponse(template.render(context))

@login_required()
def newQuestion(request):
    if request.method == "POST":
        q = QuestionForm(request.POST)
        if q.is_valid():
            new_ques = q.save()
    return HttpResponseRedirect('/test/editor')

@login_required()
def newProject(request):
    if request.method == "POST":
        p = ProjectForm(request.POST)
        if p.is_valid():
            new_proj = p.save()
    return HttpResponseRedirect('/test/home')

@login_required()
def editor(request):


    template = loader.get_template('SurveyEditor/editor.html')
    form = QuestionForm()
    context = RequestContext(request, {
        'questionForm' : form,
    })

    return HttpResponse(template.render(context))

