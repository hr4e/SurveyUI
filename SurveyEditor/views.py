from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as auth_login, logout as auth_logout

from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader

from django.utils import timezone
from django.forms import ModelForm

# Reuse existing database models
from multiquest.models import *


# Backend API
class UserProjectForm(ModelForm):
  def save(self, user=None, force_insert=False, force_update=False, commit=True):
    up = super(UserProjectForm, self).save(commit=False)
    up.userID = user
    if commit:
      up.save()
    return up
  class Meta:
    model = UserProject
    fields = ['projectID']

class ProjectForm(ModelForm):
  class Meta:
    model = Project
    fields = '__all__'

class QuestionnaireForm(ModelForm):
  def save(self, force_insert=False, force_update=False, commit=True):
    s = super(QuestionnaireForm, self).save(commit=False)
    s.versionDate = timezone.now()
    if commit:
      s.save()
    return s
  class Meta:
    model = Questionnaire
    exclude =['versionDate']

class PageForm(ModelForm):
  class Meta:
    model = Page
    fields = '__all__'

class QuestionForm(ModelForm):
  class Meta:
    model = Question
    fields = '__all__'

@login_required()
def newProject(request):
  if request.method == "POST":
    form = ProjectForm(request.POST)
    if form.is_valid():
      new_proj = form.save()
  return HttpResponseRedirect('/home/')

@login_required()
def selectProject(request):
  if request.method == "GET":
    if UserProject.objects.filter(userID=request.user):
      # Update the existing record
      record = UserProject.objects.get(userID=request.user)
      record.projectID = Project.objects.get(abbrev=request.GET['selected'])
      record.save()
    else:
      # Create a new record
      record = UserProject()
      record.userID = request.user
      record.projectID = Project.objects.get(abbrev=request.GET['selected'])
      record.save()
  return HttpResponseRedirect('/home')

@login_required()
def newSurvey(request):
  if request.method == "POST":
    form = QuestionnaireForm(request.POST)
    binding = ProjectQuestionnaire()

    # check if survey already exists in database to ensure unique survey names
    check = request.POST['shortTag']
    if Questionnaire.objects.filter(shortTag=check):
      # send 'error creating survey' message to user
      return HttpResponseRedirect('/home/')

    binding.projectID = UserProject.objects.get(userID=request.user).projectID

    if form.is_valid():
      new_surv = form.save()
      binding.questionnaireID = new_surv
      binding.save()

  return HttpResponseRedirect('/editor/' + check)

@login_required()
def newPage(request):
  if request.method == "POST":
    form = PageForm(request.POST)
    binding = QuestionnairePage()

    selected_survey = request.POST['selected']
    if selected_survey=='False':
      # Error, no selected survey
      return HttpResponseRedirect('/')
    q_id = Questionnaire.objects.get(shortTag=selected_survey)
    binding.questionnaireID = q_id

    if form.is_valid():
      new_page = form.save()
      binding.pageID = new_page
      binding.nextPageID = new_page
      binding.save()
  return HttpResponseRedirect('/editor/?selected=' + selected_survey)

@login_required()
def newQuestion(request):
  if request.method == "POST":
    form = QuestionForm(request.POST)
    if form.is_valid():
      new_ques = form.save()
  return HttpResponseRedirect('/editor')




# Frontend Views
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
          return HttpResponseRedirect('../home/')
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
    'path' : request.path.split('/')[-2],
    },
    context_instance=RequestContext(request)
  )

@login_required()
def logout(request):
  auth_logout(request, request.user)
  return HttpResponseRedirect('/')

def welcome(request):
  template = loader.get_template('SurveyEditor/welcome.html')

  context = RequestContext(request, {
    'path' : request.path.split('/')[-2],
  })
  return HttpResponse(template.render(context))

@login_required()
def home(request):
  template = loader.get_template('SurveyEditor/home.html')

  allProjects = Project.objects.all()
  form1 = ProjectForm()
  form2 = QuestionnaireForm()
  if UserProject.objects.filter(userID=request.user):
    # Update the existing record
    default_project = UserProject.objects.get(userID=request.user).projectID
    list_surveys = ProjectQuestionnaire.objects.filter(projectID=default_project)
  else:
    list_surveys = default_project = ''
  

  context = RequestContext(request, {
    'projectForm' : form1,
    'questionnaireForm' : form2,
    'defaultProject' : default_project,
    'allProjects' : allProjects,
    'listSurveys' : list_surveys,
    'path' : request.path.split('/')[-2],
  })
  return HttpResponse(template.render(context))

@login_required()
def editor(request):
  template = loader.get_template('SurveyEditor/editor.html')
  form1 = QuestionForm()
  form2 = PageForm()

  default_project = UserProject.objects.get(userID=request.user).projectID
  list_surveys = ProjectQuestionnaire.objects.filter(projectID=default_project)
  
  if request.GET:
    selected_survey = request.GET['selected']
    q_id = Questionnaire.objects.get(shortTag=selected_survey)
  else:
    q_id = selected_survey = list_pages = num_pages = ''
  
  if q_id:
    list_pages = QuestionnairePage.objects.filter(questionnaireID=q_id)
    num_pages = QuestionnairePage.objects.filter(questionnaireID=q_id).count()

  context = RequestContext(request, {
    'questionForm' : form1,
    'pageForm' : form2,
    'defaultProject' : default_project,
    'selectedSurvey' : q_id,
    'listSurveys' : list_surveys,
    'numPages' : num_pages,
    'listPages' : list_pages,
    'path' : request.path.split('/')[-2],
  })

  return HttpResponse(template.render(context))

