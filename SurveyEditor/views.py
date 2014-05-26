from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as auth_login, logout as auth_logout

from django.shortcuts import render, render_to_response

from django.forms import ModelForm
from multiquest.models import Question, Project, UserProject

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader

# Backend API
class QuestionForm(ModelForm):
	class Meta:
		model = Question
		fields = ['language', 'questionTag', 'questionText', 'helpText', 'explanation']

class ProjectForm(ModelForm):
	class Meta:
		model = Project
		fields = '__all__'

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

# Views
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
	form2 = UserProjectForm()
	if UserProject.objects.filter(userID=request.user):
		# Update the existing record
		defaultProject = UserProject.objects.get(userID=request.user)
	else:
		defaultProject = ''

	context = RequestContext(request, {
		'allProjects' : allProjects,
		'projectForm' : form1,
		'userProjectForm' : form2,
		'defaultProject' : defaultProject,
		'path' : request.path.split('/')[-2],
	})
	return HttpResponse(template.render(context))

@login_required()
def newQuestion(request):
	if request.method == "POST":
		q = QuestionForm(request.POST)
		if q.is_valid():
			new_ques = q.save()
	return HttpResponseRedirect('/editor')

@login_required()
def newProject(request):
	if request.method == "POST":
		p = ProjectForm(request.POST)
		if p.is_valid():
			new_proj = p.save()
	return HttpResponseRedirect('/home')

@login_required()
def selectProject(request):
	if request.method == "POST":
		if UserProject.objects.filter(userID=request.user):
			# Update the existing record
			up = UserProject.objects.get(userID=request.user)
			p_id = request.POST.get('projectID')
			up.projectID = Project.objects.get(id=p_id)
			up.save()
		else:
			# Create a new record
			up = UserProjectForm(request.POST)
			if up.is_valid():
				new_usrproj = up.save(user=request.user)
	return HttpResponseRedirect('/home')

@login_required()
def editor(request):
	template = loader.get_template('SurveyEditor/editor.html')
	form = QuestionForm()
	context = RequestContext(request, {
		'questionForm' : form,
		'path' : request.path.split('/')[-2],
	})

	return HttpResponse(template.render(context))

