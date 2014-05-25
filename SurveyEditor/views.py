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

    allProjects = Project.objects.all()
    form = ProjectForm()

    context = RequestContext(request, {
        'allProjects' : allProjects,
        'project' : form,
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


    template = loader.get_template('editor.html')
    form = QuestionForm()
    context = RequestContext(request, {
        'hum' : form,
    })

    return HttpResponse(template.render(context))


def associateUserToProject(theProject, theUser):
    """
    Adds or updates a record in UserProject connecting User and Project.
    Allow only one Project associate per user.
    
    Database
    Sets and association between User and Project in UserProject.
    The combination of theProject + theUser must be unique
    
    Session data
    Untouched.
    """
    # check if already existing record.
    allSAObjs = UserProject.objects.filter(
        userID=theUser,
        )
    if len(allSAObjs)>1:
        # delete the extra records and replace with a new one
        UserProject.objects.filter(
            userID=theUser,
            ).delete()
        UserProject.objects.create(
            userID=theUser,
            projectID=theProject
            )
    elif len(allSAObjs)==1:
        # update the existing record. Don't bother checking if the Project has changed.
        theSArec = allSAObjs[0]
        theSArec.projectID=theProject
        theSArec.save()
    elif len(allSAObjs)==0:
        # No records exist for this User, so create one
        UserProject.objects.create(
            userID=theUser,
            projectID=theProject
            )
    return True

def getAssociatedProjectForUser(theUser):
    """
    Adds or updates a record in UserProject connecting User and Project.
    Allow only one Project associate per user.
    
    Database
    Reads UserProject.
    The combination of theProject + theUser must be unique
    
    Session data
    Untouched.
    """
    try:
        allSAObjs = UserProject.objects.filter(
            userID=theUser,
            )
        if len(allSAObjs)>=1:
            # Should not be greater than 1! So select 1st one in the list.
            theUSObj = allSAObjs[0]
            if len(allSAObjs)>1:
                DebugOut('getAssociatedProjectForUser:  syserrmsg: Found more than one project in UserProject table for user: %s'%theUser.username)
            theProject = theUSObj.projectID
        elif len(allSAObjs)==0:
            theProject=None
    except:
        theProject=None
    return theProject