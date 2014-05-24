from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as auth_login, logout as auth_logout

from django.shortcuts import render, render_to_response

from django.forms import ModelForm

# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader

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
def index(request):
    template = loader.get_template('home.html')
    context = RequestContext(request, {
        'msg' : 'whhyyyyy',
    })
    return HttpResponse(template.render(context))

@login_required()
def editor(request):
    template = loader.get_template('editor.html')
    context = RequestContext(request, {
    })
    return HttpResponse(template.render(context))