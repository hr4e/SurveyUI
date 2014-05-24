from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as auth_login, logout as auth_logout

from django.shortcuts import render, render_to_response

from django.forms import ModelForm
from multiquest.models import Question

# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader

class QuestionForm(ModelForm):
    class Meta:
        model = Question
        fields = ['questionTag', 'questionText', 'helpText', 'explanation']

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
                    return HttpResponseRedirect('editor/')
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
    template = loader.get_template('home.html')
    context = RequestContext(request, {
        'msg' : 'whhyyyyy',
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
def editor(request):
    template = loader.get_template('editor.html')
    form = QuestionForm()
    context = RequestContext(request, {
        'hum' : form,
    })

    return HttpResponse(template.render(context))