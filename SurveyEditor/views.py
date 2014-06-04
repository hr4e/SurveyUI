from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as auth_login, logout as auth_logout

from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader

from django.contrib import messages
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

class PageQuestionForm(ModelForm):
  def save(self, page=None, force_insert=False, force_update=False, commit=True):
    pq = super(PageQuestionForm, self).save(commit=False)
    pq.pageID = page
    if commit:
      pq.save()
    return pq
  class Meta:
    model = PageQuestion
    fields = ['questionID']

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

    # check if survey already exists in database to ensure unique survey names
    check = request.POST['shortTag']
    if Project.objects.filter(shortTag=check):
      # send 'error survey name exists' message to user
      messages.error(request, 'Error: project name \'' + check + '\' already exists.')
      return HttpResponseRedirect('/editor/')

    if form.is_valid():
      new_proj = form.save()
      messages.success(request, 'Success: new project \'' + new_proj.shortTag + '\' added to database.')
      # automatically set user's default project to newly created one
      return HttpResponseRedirect('/selectProject/?selected='+check)
    else:
      for error in form.errors:
          messages.error(request, 'Error: \'' + error + '\' is required')
    return HttpResponseRedirect('/editor/')
  else:
    template = loader.get_template('404.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))

@login_required()
def selectProject(request):
  if request.method == "GET":
    if UserProject.objects.filter(userID=request.user):
      # Update the existing record
      record = UserProject.objects.get(userID=request.user)
      record.projectID = Project.objects.get(shortTag=request.GET['selected'])
      record.save()
    else:
      # Create a new record
      record = UserProject()
      record.userID = request.user
      record.projectID = Project.objects.get(shortTag=request.GET['selected'])
      record.save()
  return HttpResponseRedirect('/editor/')

@login_required()
def newSurvey(request):
  if request.method == "POST":
    form = QuestionnaireForm(request.POST)
    binding = ProjectQuestionnaire()

    # check if survey already exists in database to ensure unique survey names
    check = request.POST['shortTag']
    if Questionnaire.objects.filter(shortTag=check):
      # send 'error survey name exists' message to user
      messages.error(request, 'Error: survey name \'' + check + '\' already exists.')
      return HttpResponseRedirect('/editor/')

    # check if user has selected a project
    try:
      binding.projectID = UserProject.objects.get(userID=request.user).projectID
    except:
      messages.error(request, "Error: User '" + str(request.user) + "' has not selected a default project.")
      return HttpResponseRedirect('/editor/')

    if form.is_valid():
      new_surv = form.save()
      binding.questionnaireID = new_surv
      binding.save()
      messages.success(request, 'Success: new survey \'' + new_surv.shortTag + '\' added to project \'' + binding.projectID.shortTag + '\'')
      return HttpResponseRedirect('/editor/' + check)
    else:
      for error in form.errors:
          messages.error(request, 'Error: \'' + error + '\' is required.')
      return HttpResponseRedirect('/editor/')
  else:
    template = loader.get_template('404.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))


@login_required()
def newPage(request):
  # We maintain the invariant that all pages have a unique shortTag
  if request.method == "POST":
    form = PageForm(request.POST)
    binding = QuestionnairePage()

    selected_survey = request.POST['selected']
    if selected_survey=='':
      # Error, no selected survey
      messages.error(request, 'Error: no survey selected.')
      return HttpResponseRedirect('/editor/')

    check = request.POST['shortTag']
    if Page.objects.filter(shortTag=check):
      # send 'error page name exists' message to user
      messages.error(request, 'Error: page name \'' + check + '\' already exists.')
      return HttpResponseRedirect('/editor/?selected=' + selected_survey)

    q_id = Questionnaire.objects.get(shortTag=selected_survey)
    binding.questionnaireID = q_id

    if form.is_valid():
      new_page = form.save()
      binding.pageID = new_page
      binding.nextPageID = new_page
      binding.save()
      messages.success(request, 'Success: new page \'' + new_page.shortTag + '\' added to survey \'' + selected_survey + '\'')
    else:
      for error in form.errors:
          messages.error(request, 'Error: \'' + error + '\' is required.')
    return HttpResponseRedirect('/editor/?selected=' + selected_survey)
  else:
    template = loader.get_template('404.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context)) 

@login_required()
def newQuestion(request):
  if request.method == "POST":
    form = QuestionForm(request.POST)
    binding = PageQuestion()

    selected_page = request.POST['page']
    selected_survey = request.POST['selected']

    try:
      p_id = Page.objects.get(shortTag=selected_page)
      binding.pageID = p_id
    except:
      messages.error(request, 'Error: no pages have been created yet.')
      return HttpResponseRedirect('/editor/?selected='+selected_survey)


    check = request.POST['questionTag']
    if Question.objects.filter(questionTag=check):
      # send 'error question name exists' message to user
      messages.error(request, 'Error: question name \'' + check + '\' already exists.')
      return HttpResponseRedirect('/editor/?selected=' + selected_survey)

    if form.is_valid():
      new_ques = form.save()
      binding.questionID = new_ques
      binding.save()
      messages.success(request, 'Success: new question \'' + new_ques.questionTag + '\' added to page: \'' + p_id.shortTag + '\'')
    else:
      for error in form.errors:
          messages.error(request, 'Error: \'' + error + '\' is required.')
    return HttpResponseRedirect('/editor/?selected='+selected_survey)
  else:
    template = loader.get_template('404.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))

@login_required()
def addExistingQuestion(request):
  if request.method == "POST":
    form = PageQuestionForm(request.POST)

    page = request.POST['page']
    survey = request.POST['survey']

    try:
      p_id = Page.objects.get(shortTag=page)
      if form.is_valid():
        pq = form.save(p_id)
        messages.success(request, "Success: question '"+pq.questionID.questionTag+"' linked to page '"+page+"'")
        return HttpResponseRedirect('/editor/?selected='+survey)
      else:
        for error in form.errors:
            messages.error(request, 'Error: \'' + error + '\' is required.')
        return HttpResponseRedirect('/editor/?selected='+survey)
    except:
      messages.error(request, "Error: page '"+page+"' was not found!")
      return HttpResponseRedirect('/editor/?selected='+survey)

  else:
    template = loader.get_template('404.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))

@login_required()
def unlinkQues(request):
  if request.method == "POST":
    question = request.POST['question']
    page = request.POST['page']
    survey = request.POST['survey']

    try:
      q_id = Question.objects.get(questionTag=question)
      p_id = Page.objects.get(shortTag=page)
      try:
        binding = PageQuestion.objects.get(pageID=p_id, questionID=q_id)
        binding.delete()
        messages.success(request, "Success: question '"+question+"' unlinked from page '"+page+"'")
        return HttpResponseRedirect('/editor/?selected='+survey)
      except:
        messages.error(request, 'Error: could not find the binding in db.')
        return HttpResponseRedirect('/editor/?selected='+survey)
    except:
      messages.error(request, "Error: page or question was not found!")
      return HttpResponseRedirect('/editor/?selected='+survey)

  else:
    template = loader.get_template('404.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))

@login_required()
def deleteProject(request):
  if request.method == "POST":
    projTag = request.POST['project']

    try:
      p_id = Project.objects.get(shortTag=projTag)
      # found project to delete
      messages.success(request, "Success: project '"+projTag+"'was deleted.")
      p_id.delete()
    except:
      # did not find question to delete
      messages.error(request, "Error: project name '"+projTag+"' was not found!")
    
    return HttpResponseRedirect('/editor/')
  else:
    template = loader.get_template('404.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))

@login_required()
def deleteSurvey(request):
  if request.method == "POST":
    survTag = request.POST['survey']

    try:
      s_id = Questionnaire.objects.get(shortTag=survTag)
      # found project to delete
      messages.success(request, "Success: survey '"+survTag+"'was deleted.")
      s_id.delete()
    except:
      # did not find question to delete
      messages.error(request, "Error: survey name '"+survTag+"' was not found!")
    
    return HttpResponseRedirect('/editor/')
  else:
    template = loader.get_template('404.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))

@login_required()
def deletePage(request):
  if request.method == "POST":
    pageTag = request.POST['page']
    selected_survey = request.POST['survey']

    try:
      p_id = Page.objects.get(shortTag=pageTag)
      # found project to delete
      messages.success(request, "Success: page '"+pageTag+"'was deleted.")
      p_id.delete()
    except:
      # did not find question to delete
      messages.error(request, "Error: page name '"+pageTag+"' was not found!")
    
    return HttpResponseRedirect('/editor/?selected='+selected_survey)
  else:
    template = loader.get_template('404.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))

@login_required()
def deleteQuestion(request):
  if request.method == "POST":
    quesTag = request.POST['question']
    selected_survey = request.POST['survey']

    try:
      q_id = Question.objects.get(questionTag=quesTag)
      # found question to delete
      messages.success(request, "Success: question '"+quesTag+"'was deleted.")
      q_id.delete()
    except:
      # did not find question to delete
      messages.error(request, "Error: question name '"+quesTag+"' was not found!")
    
    return HttpResponseRedirect('/editor/?selected='+selected_survey)
  else:
    template = loader.get_template('404.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))

@login_required()
def updateQuestion(request):
  if request.method == "POST":
    quesTag = request.POST['originalTag']
    selected_survey = request.POST['survey']

    try:
      q_id = Question.objects.get(questionTag=quesTag)
      # found question to update
      try:
        t = q_id.questionTag = request.POST['questionTag']
        q_id.questionText = request.POST['questionText']
        q_id.helpText = request.POST['helpText']
        q_id.explanation = request.POST['explanation']
        q_id.language = request.POST['language']
        q_id.description = request.POST['description']
        q_id.imageFileName = request.POST['imageFileName']
        q_id.imageFileType = request.POST['imageFileType']
        q_id.save()
        messages.success(request, "Success: question '"+t+"'was updated.")
      except:
        messages.error(request, "Error: question name '"+quesTag+"' could not be updated!")

    except:
      # did not find question to update
      messages.error(request, "Error: question name '"+quesTag+"' was not found!")
    
    return HttpResponseRedirect('/editor/?selected='+selected_survey)
  else:
    template = loader.get_template('404.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))

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
          return HttpResponseRedirect('../')
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

  try:
    default_project = UserProject.objects.get(userID=request.user).projectID
  except:
    default_project = ''

  context = RequestContext(request, {
    'defaultProject' : default_project,
    'path' : request.path.split('/')[-2],
  })
  return HttpResponse(template.render(context))

@login_required()
def editor(request):
  template = loader.get_template('SurveyEditor/editor.html')
  proj_form = ProjectForm()
  surv_form = QuestionnaireForm()
  page_form = PageForm()
  ques_form = QuestionForm()
  pageQues_form = PageQuestionForm()

  all_projects = Project.objects.all()
  try:
    default_project = UserProject.objects.get(userID=request.user).projectID
    list_surveys = ProjectQuestionnaire.objects.filter(projectID=default_project)
  except:
    messages.error(request, "Error: User '" + str(request.user) + "' has not selected a default project.")
    default_project = list_surveys  = ''
    
  if request.GET:
    selected_survey = request.GET['selected']
    q_id = Questionnaire.objects.get(shortTag=selected_survey)
    path = 'survey'
  else:
    q_id = selected_survey = list_pages = num_pages = ''
    path = request.path.split('/')[-2]
  
  if q_id:
    list_pages = QuestionnairePage.objects.filter(questionnaireID=q_id)
    num_pages = QuestionnairePage.objects.filter(questionnaireID=q_id).count()

  # Get list of all questions within a page
  all_questions = []
  for page in list_pages:
    # Append list of questions associated w/ this page
    all_questions.append(PageQuestion.objects.filter(pageID=page.pageID))

  context = RequestContext(request, {
    'projForm' : proj_form,
    'survForm' : surv_form,
    'pageForm' : page_form,
    'quesForm' : ques_form,
    'pageQuesForm' : pageQues_form,
    'defaultProject' : default_project,
    'allProjects' : all_projects,
    'selectedSurvey' : q_id,
    'listSurveys' : list_surveys,
    'numPages' : num_pages,
    'listPages' : list_pages,
    'allQuestions' : all_questions,
    'path' : path,
  })
  return HttpResponse(template.render(context))
