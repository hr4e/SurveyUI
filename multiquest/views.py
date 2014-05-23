# This Python file uses the following encoding: utf-8

# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template.loader import get_template
from django.template import Context
from django.utils.safestring import SafeString
from django.utils.html import strip_tags
from django.utils.timezone import *
from django.utils.encoding import smart_str, smart_text
#from dateutil.relativedelta import relativedelta
from django.shortcuts import render_to_response, render, get_object_or_404
from django.conf import settings
from django import forms
from multiquest.forms import *
from multiquest.models import *
from multiquest.utilities import *
from multiquest.utilities_db import *
from datetime import datetime
import pickle
from django.db.models import Q
from django.core.mail import send_mail, EmailMessage
from django.core.context_processors import csrf
from reportlab.pdfgen import canvas
import os
from django.contrib.auth import authenticate
from django.contrib.auth.views import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User, Permission
from django.contrib.auth.decorators import login_required
from operator import itemgetter, attrgetter # used for sorting & selecting from a list

import csv
import unicodedata

allResultsDict = 'questionnaireResults'
allResultsList = 'questionnaireResultsList'
respondentIDDict = 'respondentIDInfo'

allYesButton = 'set flag when all responses are "Yes"'
anyYesButton = 'set flag when some (perhaps all) responses are "Yes"'
allNoButton = 'set flag when all responses are "No"'
anyNoButton = 'set flag when some (perhaps all) responses are "No"'

anySelectedButton = 'set flag when at least one choice is selected'
noneSelectedButton = 'set flag when no choices are selected'

multipleChoiceTypes = [
	'MultipleChoiceField',
	'MultipleChoiceRequiredField',
	'SingleChoiceField',
	]

autoDebugFlag = 'debugSessionFlag'

class ArticleForm(forms.Form):
	title = forms.CharField()
	pub_date = forms.DateField()

testCondChoices = {
	allYesButton : 'allYesButton',
	anyYesButton : 'anyYesButton',
	allNoButton : 'allNoButton',
	anyNoButton : 'anyNoButton',
	anySelectedButton : 'anySelectedButton',
	noneSelectedButton : 'noneSelectedButton',
	}

SessionAnalysisFlags = 'SessionAnalysisFlags'

analSaveButton = 'Save the condition for setting the flag to the database'
url_base = settings.WSGI_URL_PREFIX + 'multiquest/'

workingPageURL_base = url_base + 'working_pages/'
registrationURL_base = url_base + 'registration/'
workingPageTemplateRoot = 'working_pages/'

questionnaireSelectionPage = workingPageURL_base + 'setSessionProjectQuestionnaireDefault/'

from django.forms.formsets import formset_factory
def testing(request):
	errmsg = ''
	ArticleFormSet = formset_factory(ArticleForm, extra=4)
	formset = ArticleFormSet(initial=[
		{'title': u'Django is now open source',
		'pub_date': timezone.now(),}
	])
	theForm = formset
	resultMessage = ''
	localContext = {
		'errmsg' : errmsg,
		'theForm' : theForm,
		'resultMessage' : resultMessage,
		}
	return

# def userLogin(request): # not used.
# 	""" User View for login.
# 	Args:
# 		"request" input
# 	Returns:
# 		return_value: html. 	
# 	Raises:
# 		None.
# 	"""
# 	DebugOut('userLogin:  enter')
# 	errMsg=[]
# # 	# check for prior login
# # 	allU = getAllUsers()
# # 	for aUser in allU:
# # 		if aUser.is_authenticated():
# # 			errMsg.append('Current login: %s now logged out' %aUser.username)
# # 			logout(request)
# 	username = request.POST.get('username','')
# 	password = request.POST.get('password','')
# 	theUser = authenticate(username=username, password=password)
# #	login(request, theUser)
# 	theProject = getAssociatedProjectForUser(theUser)
# 	if theProject == None:
# 		# redirect to project selection
# 		redirectURL = registrationURL_base + 'selectProjectDefault/'
# 		DebugOut('userLogin:  redirect to %s' %redirectURL)
# 		return HttpResponseRedirect(redirectURL)
# 	else:
# 		# redirect to user landing
# 		redirectURL = registrationURL_base + 'userLanding/'
# 		DebugOut('userLogin:  redirect to %s' %redirectURL)
# 		return HttpResponseRedirect(redirectURL)
# 	
# 	DebugOut('userLogin:  exit')
# 	return render(request, "registration/login.html", {
# 		'errMsg' : errMsg,
# 		})

def userLogout(request):
	""" User View for logout.
	Args:
		"request" input
	Returns:
		return_value: html. 	
	Raises:
		None.
	"""
	logout(request)
	# Redirect to a success page.
	return render(request, "registration/logout.html", {})

def createNewAccount(request):
	""" User interface for creation of a User object.
	Args:
		"request" input
	Returns:
		return_value: html. 	
	Raises:
		None.
	"""
	DebugOut('createNewAccount: enter')
	if request.method == 'POST':
		regForm = RegistrationForm(request.POST)
		if regForm.is_valid():
			if request.user.is_authenticated(): # if someone is already logged in!
				logout(request)
			new_user = regForm.save()
			new_user = authenticate(username=request.POST['username'], password=request.POST['password1'])
			try:
				studentGroupObj = Group.objects.get(name='Student')
			except Group.DoesNotExist: # so create it
				studentGroupObj = Group.objects.create(name='Student')
			new_user.groups.add(studentGroupObj)
			login(request, new_user)
			redirectURL = registrationURL_base + 'selectProjectDefault/'
			DebugOut('createNewAccount: redirect to %s'%redirectURL)
			return HttpResponseRedirect(redirectURL)
	else:
		regForm = RegistrationForm()

	DebugOut('createNewAccount: exit')

	currentContext = {
		'regForm': regForm,
		}
	currentContext.update(csrf(request))
	return render(request, "registration/createNewAccount.html", currentContext)

@login_required()
def selectProjectDefault(request):
	"""
	Allow the selection of a Project as a default to fill the UserProject table.
	Args
	http request
	
	Database
	Sets an association between User and Project in UserProject
	
	Session data
	Sets Project default.
	Uses temporary 'FselectProjectDefault'
	"""
	DebugOut('selectProjectDefault:  enter')
		
	# allProjectInfo record structure
	# [ Project short tag, name, email, projectAddress, contactPhone, internetLocation,
	# record number in the Project table ]
	errMsg = []
	theUser = request.user
	if request.method == 'POST':
		# Default project selected.
		# retrieve table from Session data
		if 'SelectProject' in request.POST:
			allProjectInfo = displayProjectsWithinScope() # display project information for selection
			[dummyText, listRecNum] = request.POST['SelectProject'].split(" ") #decode the response
			# format is "Select" "record number in display list"
			recNum = int(listRecNum) - 1 # start with zero
			theProjectIDinDB = allProjectInfo[recNum][-1] # is the record number for the project
			try:
				theProject = Project.objects.get(id=theProjectIDinDB)
				setSessionProject(request, theProject) # set Session data default
				associateUserToProject(theProject, theUser)
				projectTag = theProject.shortTag
				# remove Questionnaire default since it is invalid
				if 'theQuestionnaire' in request.session:
					del request.session['theQuestionnaire']
				errMsg.append('Project "%s" selected.' %projectTag)
				redirectURL = registrationURL_base + 'userLanding/'
				return HttpResponseRedirect(redirectURL)
			except Project.DoesNotExist:
				errMsg.append('System error (syserrmsg):  Project does not exist')
		elif 'returnToHome' in request.POST:
			theProjectTesting = getAssociatedProjectForUser(theUser)
			if theProjectTesting == None: # no default for the user!
				errMsg.append('Please select a Project.')	
			else:
				redirectURL = registrationURL_base + 'userLanding/'
				DebugOut('selectProjectDefault:  exit to %s'%redirectURL)
				return HttpResponseRedirect(redirectURL)
	allProjectInfo = displayProjectsWithinScope() # display project information for selection
	theCurrentDefaultProject = getSessionProject(request)
	if not theCurrentDefaultProject: # not in session data
		# fall back to user default
		theCurrentDefaultProject = getAssociatedProjectForUser(theUser)
	# If no project, Don't redirect!! This page allows a new user to select
		
	currentContext = {
		'theUser' : theUser,
		'allProjectInfo' : allProjectInfo,
		'theCurrentDefaultProject' : theCurrentDefaultProject,
		'errMsg' : errMsg,
		}
	DebugOut('selectProjectDefault:  exit')
	return render(request,'registration/selectProjectDefault.html',
		currentContext)

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

@login_required()
def uploadDownloadQuestionnaire(request):
	"""Dumps a csv-type file of the default Questionnaire.

	This is a one line or more descriptive summary.
	Blah Blah Blah.

	Args:
		argument_one: This is of some type a and does x.
		arg....:...

	Returns:
		http response 	

	Raises:
		none.
	"""
	DebugOut('uploadDownloadQuestionnaire:  enter')
	errMsg = ''
#Standards: “Handling Session values of Project and Questionnaire” for Groups
	[theProject, theQuestionnaire] = getSessionQuestionnaireProject(request)
	theUser = request.user
	if not theProject:
			theProject = getAssociatedProjectForUser(theUser)
	if not theQuestionnaire:
		errMsg = ['The questionnaire has not been selected']
		redirectURL = registrationURL_base + 'selectQuestionnaireDefault/'
		DebugOut('No questionnaire selected, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)
	workingQuestionnaireTag = theQuestionnaire.shortTag
	if not theProject:
		# select a project.
		DebugOut('The Project has not been selected')
		errMsg = ['The Project has not been selected']
		redirectURL = registrationURL_base + 'selectProjectDefault/'
		DebugOut('No project, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)
	theProjectTag = theProject.shortTag
	DebugOut('Project: %s, Questionnaire: %s' %(theProject.shortTag, theQuestionnaire.shortTag))
	
	if request.method == 'POST':
		if 'dumpQuestionnaireSpecification' in request.POST:
			redirectURL = url_base + 'working_pages/dumpQuestionnaireSpecification/'
			return HttpResponseRedirect(redirectURL)
		elif 'uploadQuestionnaireSpecification' in request.POST:
			DebugOut('in uploadQuestionnaireSpecification')
			redirectURL = url_base + 'working_pages/uploadQuestionnaireSpecification/'
			return HttpResponseRedirect(redirectURL)
		elif 'returnToHome' in request.POST:
			redirectURL = registrationURL_base + 'userLanding/'
			DebugOut('selectProjectDefault:  exit to %s'%redirectURL)
			return HttpResponseRedirect(redirectURL)
	
	currentContext = {
		'theProject' : theProject,
		'theUser' : theUser,
		'theQuestionnaire' : theQuestionnaire,
		'errMsg' : errMsg,
		}
	DebugOut('uploadDownloadQuestionnaire: exit')
	return render(request,'working_pages/uploadDownloadQuestionnaire.html',
		currentContext)

@login_required()
def uploadQuestionnaireSpecification(request):
	"""Loads a csv-type file of a Questionnaire specification.

	The text-editable file is a serialization of the database.

	Args:
		http request
		
	Returns:
		http response 	

	Raises:
		none.
	"""
	DebugOut('uploadQuestionnaireSpecification: Enter')
	errMsg = []
	DebugOut('User is: %s'%request.user)
	if request.method == 'POST':
		DebugOut('in UploadQuestionnaire')
		DebugOut('request.POST:  %s'%request.POST)
		theForm = UploadFileForm(request.POST, request.FILES)
		if 'returnToHome' in request.POST:
			redirectURL = registrationURL_base + 'userLanding/'
			DebugOut('selectProjectDefault:  exit to %s'%redirectURL)
			return HttpResponseRedirect(redirectURL)
		if theForm.is_valid():
# 			handle_uploaded_file(request.FILES['theFile'])
			errMsg.append('This feature is under development.')
			urlPrefix = request.get_host()+settings.WSGI_URL_PREFIX
			return render(request, 'InfoScreenExit.html', { 'errMsg': errMsg, 'wsgiPrefix':urlPrefix})
		else:
			DebugOut('Form errors %s'%theForm.errors)
	else:
		DebugOut('Not a POST')
		theForm = UploadFileForm()

	DebugOut('uploadQuestionnaireSpecification: Exit')
	return render(request,'working_pages/uploadQuestionnaireSpecification.html', {'theForm': theForm})

@login_required()
def handle_uploaded_file(thePost):
	DebugOut('handle_uploaded_file: enter')
	
	return

@login_required()
def dumpQuestionnaireSpecification(request):
	"""Dumps a csv-type file of the default Questionnaire.

	This is a one line or more descriptive summary.
	Blah Blah Blah.

	Args:
		argument_one: This is of some type a and does x.
		arg....:...

	Returns:
		http response 	

	Raises:
		none.
	"""
	DebugOut('dumpQuestionnaireSpecification: Enter')
	errMsg = []
	[theProject, theQuestionnaire] = getSessionQuestionnaireProject(request)
	# Create the HttpResponse object with the appropriate CSV header.
	response = HttpResponse(content_type='text/csv')
	now = str(timezone.now())
	questionnaireSpecFileName = "Questionnaire specification %s_%s.txt"%(theProject.shortTag, theQuestionnaire.shortTag)
	contentDispo = 'attachment; filename=' + '"' + questionnaireSpecFileName + '"'
	response['Content-Disposition'] = contentDispo

	response.write('ProjectSeparator'+os.linesep)
	# Dump Project record
	# make project pointer into a queryset which adheres to dumpQuerySet requirements
	projectQS = Project.objects.filter(id=theProject.id)
	nRecs = dumpQuerySet(response, projectQS)
	DebugOut('Project nRecs: %s'%nRecs)
	
	# dump questionnaire record
	questionnaireQS = Questionnaire.objects.filter(id=theQuestionnaire.id)
	nRecs = dumpQuerySet(response, questionnaireQS)
	DebugOut('Questionnaire nRecs: %s'%nRecs)
	
	# dump Pages
	pageQS = getAllPageObjsForQuestionnaire(theQuestionnaire)
	nRecs = dumpQuerySet(response, pageQS)
	DebugOut('Page nRecs: %s'%nRecs)
	
	# dump Questions
	questQS = getAllQuestionObjsForQuestionnaire(theQuestionnaire)
	nRecs = dumpQuerySet(response, questQS)
	DebugOut('Question nRecs: %s'%nRecs)
	
	# dump ProjectQuestionnaire
	pqQS = ProjectQuestionnaire.objects.filter(
		projectID=theProject,
		questionnaireID=theQuestionnaire,
		)
	nRecs = dumpQuerySet(response, pqQS)
	DebugOut('ProjectQuestionnaire nRecs: %s'%nRecs)
	
	# Dump PageQuestion table
	# build an "or" query to include all pages
	# initialize query
	queryOR = Q(pageID=pageQS[0])
	for anID in pageQS[1:]:
		queryOR = queryOR | Q(pageID=anID)
	PageQuestionQS = PageQuestion.objects.filter(queryOR)
	nRecs = dumpQuerySet(response, PageQuestionQS)
	DebugOut('PageQuestion nRecs: %s'%nRecs)

	# Dump ResponseChoice table
	# build an "or" query to include all pages
	# initialize query
	queryOR = Q(questionID=questQS[0])
	for anID in questQS[1:]:
		queryOR = queryOR | Q(questionID=anID)
	ResponseChoiceQS = ResponseChoice.objects.filter(queryOR)
	nRecs = dumpQuerySet(response, ResponseChoiceQS)
	DebugOut('ResponseChoice nRecs: %s'%nRecs)

	# Dump ProjectAttributes table
	ProjectAttributesQS = ProjectAttributes.objects.filter(projectID=theProject)
	nRecs = dumpQuerySet(response, ProjectAttributesQS)
	DebugOut('ProjectAttributes nRecs: %s'%nRecs)

	# Dump QuestionnaireAttributes table
	QuestionnaireAttributesQS = QuestionnaireAttributes.objects.filter(questionnaireID=theQuestionnaire)
	nRecs = dumpQuerySet(response, QuestionnaireAttributesQS)
	DebugOut('QuestionnaireAttributes nRecs: %s'%nRecs)
	
	# Dump PageAnalysis table
	PageAnalysisQS = PageAnalysis.objects.filter(questionnaireID=theQuestionnaire)
	nRecs = dumpQuerySet(response, PageAnalysisQS)
	DebugOut('PageAnalysis nRecs: %s'%nRecs)
	
	# Dump PageAttribute table
	PageAttributesQS = PageAttributes.objects.all()
	nRecs = dumpQuerySet(response, PageAttributesQS)
	DebugOut('PageAttribute nRecs: %s'%nRecs)
		
	DebugOut('dumpQuestionnaireSpecification: Exit')
	return response


@login_required()
def userLanding(request):
	"""
	Next page after login. Set various defaults associated with the user.
	Check for preexisting Project association. If not associated, redirect to selection.
	
	Database
	
	Session data
	Untouched.
	"""
	DebugOut('userLanding: enter')
	errMsg = []
	theUser = request.user
	DebugOut('the user is: %s' %theUser)
	theProject = getSessionProject(request)
	if not theProject: # if not already set in session data, then use User default
		theProject = getAssociatedProjectForUser(theUser) # retrieve default project for User
		if theProject == None:
			# redirect to project selection
			redirectURL = registrationURL_base + 'selectProjectDefault/'
			DebugOut('No project, so redirect to: %s' %redirectURL)
			return HttpResponseRedirect(redirectURL)
		else: # set default project in session data
			setSessionProject(request, theProject)
			# remove Questionnaire default since it may be invalid
			if 'theQuestionnaire' in request.session:
				del request.session['theQuestionnaire']
	theQuestionnaire = getSessionQuestionnaire(request) # May be None
	
	if request.method == 'POST':
		if 'differentProject' in request.POST:
			redirectURL = registrationURL_base + 'selectProjectDefault/'
			return HttpResponseRedirect(redirectURL)
		elif 'editProject' in request.POST:
			redirectURL = url_base + 'registration/editProjectRecord/'
			return HttpResponseRedirect(redirectURL)
		elif 'displayRunQuestionnaire' in request.POST:
			redirectURL = url_base + 'working_pages/selectProjectsQuestionnairesToExecute/'
			return HttpResponseRedirect(redirectURL)
		elif 'duplicateQuestionnaireView' in request.POST:
			redirectURL = url_base + 'working_pages/duplicateQuestionnaireView/'
			return HttpResponseRedirect(redirectURL)
		elif 'runTheQuestionnaire' in request.POST:
			removeResponsesFromSessionData(request)
			questionnaireEnvironmentPrep( request, theProject, theQuestionnaire)
			urltogo = questionnaireToGo(request, theProject, theQuestionnaire)
			return HttpResponseRedirect(urltogo)
		elif 'selectQuestionnaireDefault' in request.POST:
			redirectURL = url_base + 'registration/selectQuestionnaireDefault/'
			return HttpResponseRedirect(redirectURL)
		elif 'createPageTransition' in request.POST:
			redirectURL = url_base + 'working_pages/setPageToPageTransitionCalculated/'
			return HttpResponseRedirect(redirectURL)
		elif 'editDefaultPageTransitions' in request.POST:
			redirectURL = url_base + 'working_pages/editDefaultPageTransitions/'
			return HttpResponseRedirect(redirectURL)
		elif 'dumpSubmissionDataForProject' in request.POST:
			redirectURL = url_base + 'working_pages/dumpSubmissionDataForProject/'
			return HttpResponseRedirect(redirectURL)
		elif 'createProjectWithSamples' in request.POST:
			redirectURL = url_base + 'working_pages/createProjectWithSamples/'
			return HttpResponseRedirect(redirectURL)
		elif 'uploadDownloadQuestionnaire' in request.POST:
			redirectURL = url_base + 'working_pages/uploadDownloadQuestionnaire/'
			return HttpResponseRedirect(redirectURL)
		elif 'dumpSubmissionDataForProject' in request.POST:
			redirectURL = url_base + 'working_pages/dumpSubmissionDataForProject/'
			return HttpResponseRedirect(redirectURL)
		elif 'responseViewer' in request.POST:
			redirectURL = url_base + 'working_pages/responseViewer/'
			return HttpResponseRedirect(redirectURL)
		elif 'responseDelete' in request.POST:
			redirectURL = url_base + 'working_pages/responseDelete/'
			return HttpResponseRedirect(redirectURL)
		elif 'editQuestionnaireInfo' in request.POST:
			redirectURL = url_base + 'working_pages/editQuestionnaire/'
			return HttpResponseRedirect(redirectURL)
		elif 'bulkPageEdit' in request.POST:
			redirectURL = url_base + 'working_pages/bulkPageEdit/'
			return HttpResponseRedirect(redirectURL)
		elif 'editQuestionNames' in request.POST:
			redirectURL = url_base + 'working_pages/editQuestionNames/'
			return HttpResponseRedirect(redirectURL)
		elif 'bulkQuestionEdit' in request.POST:
			redirectURL = url_base + 'working_pages/bulkQuestionEdit/'
			return HttpResponseRedirect(redirectURL)
		elif 'deleteQuestionnaireView' in request.POST:
			redirectURL = url_base + 'working_pages/deleteQuestionnaireView/'
			return HttpResponseRedirect(redirectURL)
		elif 'savecsvDecoder' in request.POST:
			redirectURL = url_base + 'working_pages/savecsvDecoder/'
			return HttpResponseRedirect(redirectURL)
		elif 'logout' in request.POST:
			redirectURL = url_base + 'registration/logout/'
			return HttpResponseRedirect(redirectURL)
#http://10.0.1.73:8000/multiquest/working_pages/savecsvDecoder/
	currentContext = {
		'theProject' : theProject,
		'theUser' : theUser,
		'theQuestionnaire' : theQuestionnaire,
		'errMsg' : errMsg,
		}
	DebugOut('userLanding: exit')
	return render(request,'registration/userLanding.html',
		currentContext)

@login_required()
def createProjectWithSamples(request):
	"""
	Create a new Questionnaire object in the current Project.
	
	Database
	Create a new record in the Questionnaire table.
	Create sample Questionnaires.
	
	Session data
	Untouched.
	"""
	DebugOut('createProjectWithSamples:  enter')
	errMsg = []
	theProject = getSessionProject(request)
	if not theProject: # not in session data
		# fall back to user default
		theUser = request.user
		theProject = getAssociatedProjectForUser(theUser)
	if not theProject:
		# Redirect if still no project
		redirectURL = registrationURL_base + 'selectProjectDefault/'
		DebugOut('No project, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)

	# find the sample questionnaire
	projectTagforSample = 'test_project'
	questionnaireTagforSample = 'TestQuest' # "Get" this Questionnaire
	questionnaireTagforTarget = 'SampleQ'	# and "Put" it into the current project under this name
	sampleQuestionnaire = getQuestionnaireObjFromTags( projectTagforSample, questionnaireTagforSample)
	existingQuestionnaireTags = getQuestionnaireTagsForProject(theProject)
	# Capture request to go home
	if request.method == 'POST':
		if 'returnToHome' in request.POST:
			redirectURL = registrationURL_base + 'userLanding/'
			DebugOut('createProjectWithSamples:  exit to %s'%redirectURL)
			return HttpResponseRedirect(redirectURL)
		
	if not sampleQuestionnaire:
		errMsg.append('syserrmsg:  Sample questionnaire name %s does not exist for copying!'%questionnaireTagforSample)
		currentContext = {
			'questionnaireTagforTarget' : questionnaireTagforTarget,
			'existingQuestionnaireTags' : existingQuestionnaireTags,
			'theProject' : theProject,
			'errMsg' : errMsg,
			}
		DebugOut('createProjectWithSamples:  exit')
		return render(request,'working_pages/createProjectWithSamples.html',
			currentContext)
	DebugOut('The Sample questionnaire name is: %s'%sampleQuestionnaire.shortTag)
	
	if request.method == 'POST':
		if 'CreateSampleQuestionnaire' in request.POST:
			DebugOut('In CreateSampleQuestionnaire')
			# Before creation check to see if the name conflicts
			DebugOut('Start name: %s'%questionnaireTagforTarget)
			maxLength = 30 # maximum length of a Questionnaire shortTag.
			theNewName = makeUniqueTag( existingQuestionnaireTags, questionnaireTagforTarget, maxLength)
			DebugOut('Updated name: %s'%theNewName)
			newQuestionnaire = duplicateQuestionnaire( theProject, sampleQuestionnaire, theNewName)
			# update the list with the new Questionnaire
			existingQuestionnaireTags = getQuestionnaireTagsForProject(theProject)
			DebugOut('The new Sample questionnaire name is: %s'%newQuestionnaire.shortTag)

	currentContext = {
		'questionnaireTagforTarget' : questionnaireTagforTarget,
		'existingQuestionnaireTags' : existingQuestionnaireTags,
		'theProject' : theProject,
		'errMsg' : errMsg,
		}
	
	DebugOut('createProjectWithSamples:  exit')
	return render(request,'working_pages/createProjectWithSamples.html',
		currentContext)

@login_required()
def editProjectRecord(request):
	"""
	Edit the current default Project record
	
	Database
	Create a new record in the Project table.
	Create sample Questionnaires.
	
	Session data
	Untouched.
	"""
	DebugOut('editProjectRecord: enter')
	errMsg = []
	theUser = request.user
	theProject = getAssociatedProjectForUser(theUser)
	if request.method == 'POST':
		theForm = ProjectForm(request.POST)
		if 'submitButton' in request.POST: # accept the Project edits
			if request.POST['submitButton'] == 'accept Project Edits':
				if theForm.is_valid():
					# Save the edited Project record.
					DebugOut('after is_valid')
					cleanedData = theForm.cleaned_data
					DebugOut('cleanedData %s' %cleanedData)
					theForm = ProjectForm(cleanedData)
					# want to UPDATE the Project record
					updateProjectRecord(theProject,cleanedData)
# 					theForm.save() # error:  creates a new record rather than updates
		elif 'returnToHome' in request.POST: # return to Home Page
					redirectURL = registrationURL_base + 'userLanding/'
					return HttpResponseRedirect(redirectURL)
	else:
		theForm = ProjectForm(instance=theProject)
	currentContext = {
		'theProject' : theProject,
		'theForm' : theForm,
		'errMsg' : errMsg,
		}
	DebugOut('editProjectRecord: exit')
	return render(request,'registration/editProjectRecord.html',
		currentContext)

# **** How to do this without calling out each field!
def updateProjectRecord(theProject,cleanedData): # Alas, how to get rid of this!!
	"""
	Edit the current default Project record using the data dictionary input.
	
	Args
	theProject
	cleanedData:  dictionary
	
	Database
	Update the input record in the Project table.
	Create sample Questionnaires.
	
	Session data
	Untouched.
	"""
	if 'shortTag' in cleanedData:
		theProject.shortTag=cleanedData['shortTag']
	if 'abbrev' in cleanedData:
		theProject.abbrev=cleanedData['abbrev']
	if 'name' in cleanedData:
		theProject.name=cleanedData['name']
	if 'projectAddress' in cleanedData:
		theProject.projectAddress=cleanedData['projectAddress']
	if 'email' in cleanedData:
		theProject.email=cleanedData['email']
	if 'contactPhone' in cleanedData:
		theProject.contactPhone=cleanedData['contactPhone']
	if 'internetLocation' in cleanedData:
		theProject.internetLocation=cleanedData['internetLocation']
	theProject.save()
	return theProject
	
def listRegistration(request):
	"""
	List information about the registered users.
	"""
	DebugOut('listRegistration:  enter')
	errMsg = [] # Initialize error messages
	allG=Group.objects.all()
	colList = [
		'Project',
		'User Name',
		'Last Name',
		'First Name',
		'Email',
		'Last Login',
		'Date Joined',
		'Group Name',
		]

	allMemberInfo = []
	for aGroup in allG:
		allMembs=User.objects.filter(
			groups=aGroup) # Lists the members of a group
		for aMem in allMembs:
			username = aMem.username
			last_name = aMem.last_name
			first_name = aMem.first_name
			email = aMem.email
			last_login = aMem.last_login
			date_joined = aMem.date_joined
			groupName = aGroup.name
			try:
				projectTag = UserProject.objects.get(userID=aMem).projectID.shortTag
			except:
				projectTag = ''
			allMemberInfo.append([
				projectTag,
				username,
				last_name,
				first_name,
				email,
				last_login,
				date_joined,
				groupName,
				])
	
	if len(allMemberInfo)==0:
		errMsg.append('No members to be listed')
	
	DebugOut('listRegistration:  exit')
	return render(request, workingPageTemplateRoot + 'tablelisting.html',
		{'pageTitle' : 'List the Groups and their members',
		'allValues' : allMemberInfo,
		'colList' : colList,
		'bannerText' : 'List the Groups and their members',
		'bannerText1' : '',
		'back_to' : settings.WSGI_URL_PREFIX + 'multiquest/intro/',
		'back_toPrompt' : 'Return to the Introduction Page',
		'errMsg' : errMsg,
		})
	
def intro(request):
	DebugOut('intro:  enter')
	[currentProject, currentQuestionnaire] = getSessionQuestionnaireProject(request)
	if request.method == 'POST':
		DebugOut('In "post"')

	if currentProject:
		projectName = currentProject.shortTag
	else:
		projectName = ''
		
	if currentQuestionnaire:
		questionnaireName = currentQuestionnaire.shortTag
	else:
		questionnaireName = ''
	
	introContext = {'current_date' : timezone.now(),
		'thishost' : request.get_host(),
		'back_to' : 'multiquest/intro/',
		'projectName' : projectName,
		'questionnaireName' : questionnaireName,
		'imageloc' : settings.MEDIA_URL,
		'workingPageTemplateRoot' : workingPageTemplateRoot,
		'workingPageURL_base' : workingPageURL_base,
		'registrationURL_base' : registrationURL_base,
		'urlprefix' : settings.WSGI_URL_PREFIX,
		'debug' : settings.DEBUG}
	DebugOut('intro:  exit')
	return render(request, workingPageTemplateRoot + 'intro.html', introContext)

def selectPages(request):
	"""Select pages to include in a Questionnaire from a list.
	
	This function displays a list

	Args:
		"request" input

	Returns:
		return_value: html. 	

	Raises:
		None.
	"""
	DebugOut('selectPages:  enter')
	[theProject, theQuestionnaire] = getSessionQuestionnaireProject(request)
	if not theQuestionnaire:
		errMsg = ['The questionnaire has not been selected']
		return render(request, 'system_error.html', { 'syserrmsg': errMsg})
	# list the columns
	colList = ['Page Tag','Description (not displayed)','Explanation','Prologue','Epilogue','Language','Page Type', 'Questionnaire member']

	allValuesUnsorted = [] # table rows
	pageObjs = getAllPageObjsInQuestionnaires()
	
	for aPage in pageObjs:
		theQaires = getAllQuestionnairesReferencingAPage( aPage )
		theQTags = [aQ.shortTag for aQ in theQaires]
		tagListStr = ', '.join(theQTags)
		rowValues = [
			aPage.shortTag,
			aPage.description,
			aPage.explanation,
			aPage.prologue,
			aPage.epilogue,
			aPage.language,
			aPage.pageType,
			tagListStr,
			]
		allValuesUnsorted.append(rowValues)
	allValues = sorted( allValuesUnsorted, key=itemgetter(0,7))

	DebugOut('selectPages:  exit')
	return render(request, workingPageTemplateRoot + 'selectPages.html',
		{'allValues' : allValues})
	
	
def listPages(request):
	"""View a listing of pages.
	
	This function displays a list

	Args:
		"request" input

	Returns:
		return_value: html. 	

	Raises:
		None.
	"""
	DebugOut('listPages:  enter')
	errMsg = [] # Initialize error messages

	try:
		pageListing = Page.objects.all().order_by('shortTag')
	except:
		errMsg.append('List Pages:  query to database failed.')
	if errMsg != []:
		DebugOut(str(errMsg))
		return render(request, 'system_error.html', { 'syserrmsg': errMsg})
	allPages = getAllPageObjsInQuestionnaires() # All Pages referenced
	[allValues, colList, pageRecordDict1 ] = displayAllPageInfo(allPages)
	if errMsg == []:
		errMsg = ''
	missingPages = getAllPageObjsNotReferenced() # All Pages referenced
	[allValues2, colList, pageRecordDict2 ] = displayAllPageInfo(missingPages)
	DebugOut('listPages:  exit')
	return render(request, workingPageTemplateRoot + 'tablelisting.html',
		{'pageTitle' : 'List the available Pages',
		'allValues' : allValues,
		'colList' : colList,
		'allValues2' : allValues2,
		'colList2' : colList,
		'imageloc' : settings.MEDIA_URL,
		'bannerText' : 'List the available Pages',
		'bannerText1' : '',
		'bannerText2' : 'Page list NOT in any Questionnaire',
		'back_to' : settings.WSGI_URL_PREFIX + 'multiquest/intro/',
		'back_toPrompt' : 'Return to the Introduction Page',
		'errMsg' : errMsg,
		})


def listQuestions(request):
	errMsg = [] # Initialize error messages
	workingPageTemplateRoot = 'working_pages/'

	tableListing = getAllQuestionObjsEditable()
	
	numberOfQuestions = tableListing.count()
	
	if errMsg != []:
		DebugOut(str(errMsg))
		return render(request, 'system_error.html', { 'syserrmsg': errMsg})

	colList = ['Question Text','Question Tag','Response Type','Explanation (viewed by respondent)','Description (not viewed by respondent)',"Page Tag('s)"]
	dbNames = ['questionText','questionTag','responseType','explanation','description','shortTag' ]
	allValues = []
	for questionObj in tableListing:
		rowValues = []
		for item in dbNames:
			if item == 'shortTag':
				allPQs = PageQuestion.objects.filter(questionID=questionObj)
				allTags = [aPQ.pageID.shortTag for aPQ in allPQs] # list comprehension
				tagListStr = ', '.join(allTags)
				rowValues.append(tagListStr)
			else:
				rowValues.append(unicode(getattr(questionObj, item)).encode('utf-8'))		
		allValues.append(rowValues)
	if errMsg == []:
		errMsg = ''

	return render(request, workingPageTemplateRoot + 'tablelisting.html',
		{'pageTitle' : 'List the available Questions',
		'allValues' : allValues,
		'colList' : colList,
		'allValues2' : '',
		'colList2' : '',
		'imageloc' : settings.MEDIA_URL,
		'bannerText' : 'List the available Questions',
		'bannerText1' : 'Number of questions:  %s' %numberOfQuestions,
		'bannerText2' : '',
		'back_to' : settings.WSGI_URL_PREFIX + 'multiquest/intro/',
		'back_toPrompt' : 'Return to the Introduction Page',
		'errMsg' : errMsg,
		})

def verifyQuestionnaireProjectDB(request, whichProject, whichQuest):
	"""Checks input Project tag and Questionnaire tag against the database
	if both exist in the database, then return the corresponding objects errMsg = False
	Does not set Session Data, does not write to the database
	
	Purpose:  help with translating a url and mapping the page tag to a page record
	
	Args:
		request:  request sent from client browser
		whichProject: Project Tag:  character string
		whichQuest: Questionnaire Tag:  character string

	Returns:
		Project and Questionnaire objects from Session Data

	Raises:
		None.
	"""	
	errMsg = []
	try:
		theProject = getProjectObj(whichProject)
	except:
		errMess = 'syserrmsg:  url "%s/" does not match any project in the database' %(whichProject)
		errMsg.append(errMess)
	
	try:
		theQuestionnaire = getQuestionnaireObjFromTags(whichProject, whichQuest)
	except:
		errMess = 'syserrmsg:  url "%s/" does not match any questionnaire in the database' %(whichQuest)
		errMsg.append(errMess)
	
	if errMsg == []:
		errMsg = False
	
	return [theProject, theQuestionnaire, errMsg]
	
def verifyQuestionnaireProject(request, whichProject, whichQuest):
	"""Checks input Project tag and Questionnaire tag against the session data.
	If both exist in the database, then return the corresponding objects errMsg = False
	Does not set Session Data, does not write to the database
	
	Purpose:  help with translating a url and mapping the page tag to a page record
	
	Args:
		request:  request sent from client browser
		whichProject: Project Tag:  character string
		whichQuest: Questionnaire Tag:  character string

	Returns:
		Project and Questionnaire objects from Session Data

	Raises:
		None.
	"""	
	# checks input Project tag and Questionnaire tag against session data
	# if both exist in the session data, then return the corresponding objects errMsg = False
	# Session data is read, but not altered.
	errMessOut = []
	if not whichProject:
		errMess = 'Debug:  Project tag is missing from url.'
		DebugOut(errMess)
		errMessOut.append(errMess)
	
	if not whichQuest:
		errMess = 'syserrmsg: Questionnaire tag is missing from url.'
		DebugOut(errMess)
		errMessOut.append(errMess)

	if errMessOut != []:
		return [None, None, errMessOut]

	if request:
		[theProject, theQuestionnaire] = getSessionQuestionnaireProject(request) # retrieve from session data
	else:
		errMess = 'No session data'
		DebugOut(errMess)
		errMessOut.append(errMess)
		return [None, None, errMessOut]
		

	if not theProject:
		errMess = 'Debug:  current Project is not specified for this Session.'
		DebugOut(errMess)
		errMessOut.append(errMess)
	
	if not theQuestionnaire:
		errMess = 'syserrmsg: current Questionnaire is not specified for this Session.'
		DebugOut(errMess)
		errMessOut.append(errMess)
	
	if errMessOut != []:
		return [theProject, theQuestionnaire, errMessOut]

	# Verify that whichProject matches session data
	if theProject.shortTag != whichProject:
		errMess = 'syserrmsg:  url "%s/" does not match current project "%s/"' %(whichProject, theProject.shortTag)
		DebugOut(errMess)
		errMessOut.append(errMess)

	# Verify that whichQuest matches session data
	if theQuestionnaire.shortTag != whichQuest:
		errMess = 'syserrmsg:  url "%s/" does not match current questionnaire "%s"/' %(whichQuest, theQuestionnaire.shortTag)
		DebugOut(errMess)
		errMessOut.append(errMess)

	if errMessOut != []:
		return [theProject, theQuestionnaire, errMessOut]

	return [theProject, theQuestionnaire, errMessOut]
	
def getSessionQuestionnaireProject(request):
	"""Retrieve a Project and Questionnaire object from session data. Use database query
	to update the object.
	
	Args:
		"request" input

	Returns:
		return_value: html. 	

	Raises:
		None.
	"""
			
	if 'theProject' in request.session:
		projRecNo = request.session['theProject']
		try: # update the object by querying the database
			theProject = Project.objects.get(id= projRecNo)
		except Project.DoesNotExist:
			theProject = None
	else:
		theProject = None
		
	if 'theQuestionnaire' in request.session:
		questRecNo = request.session['theQuestionnaire']
		try:
			theQuestionnaire = Questionnaire.objects.get(id= questRecNo)
		except Questionnaire.DoesNotExist:
			theQuestionnaire = None
	else:
		theQuestionnaire = None

	return [theProject, theQuestionnaire ]

def displayQuestionnairesAndProjectsRetrieve(allQuestionnaireInfo, listRecNum):
	"""Return the Project and Questionnaire objects, given the record number of the list
	row selection as displayed to the user.
	
	Display list is formatted in function displayQuestionnairesAndProjects.
	
	Project may not always exist.
	
	Args:
		listRecNum, integer (first row is a text "1") of row in list displayed to the user.
	Returns:
		ProjectObj, QuestionnaireObj:  objects referenced in the list row.
	"""
	DebugOut('displayQuestionnairesAndProjectsRetrieve enter')
	DebugOut('listRecNum %s' %listRecNum)
	recNum = int(listRecNum) - 1 # start with zero
	theProjectIDinDB = allQuestionnaireInfo[recNum][-2] # is the record number for the project
	theQuestIDinDB = allQuestionnaireInfo[recNum][-1] # is the record number for the questionnaire
	DebugOut('theProjectIDinDB %s' %theProjectIDinDB)
	theQuestionnaire = Questionnaire.objects.get(id=theQuestIDinDB)
	DebugOut('theQuestionnaire %s' %theQuestionnaire)
	if theProjectIDinDB: # project may not exist
		theProject = Project.objects.get(id=theProjectIDinDB)
	else:
		theProject = Project.objects.none()
	DebugOut('displayQuestionnairesAndProjectsRetrieve exit')
	return [theProject, theQuestionnaire]

def displayProjectsWithinScope():
	"""Prepare a list for display of all Projects within scope
	"""
	DebugOut('displayProjectsWithinScope:  enter')
	allProjectObjs = getAllProjectsWithinScope()
	allProjectInfo = []
	for aProject in allProjectObjs:
		allProjectInfo.append([
			aProject.shortTag,
			aProject.name,
			aProject.email,
			aProject.projectAddress,
			aProject.contactPhone,
			aProject.internetLocation,
			aProject.id,
			])
	# record structure
	# [ Project short tag, name, email, projectAddress, contactPhone, internetLocation,
	# record number in the Project table ]
	DebugOut('displayProjectsWithinScope:  exit')
	return allProjectInfo # list
	
def displayQuestionnairesAndProjects(limitScope, limitProjectView, thisProject):
	"""Prepare a list for display of all active questionnaires and the corresponding
	project.
	Args:
		limitScope:  True if ProjectAttributes is to be consulted for permission to display.
		limitProjectView:  True if list contains only the Questionnaires from thisProject
		thisProject:  "None" displays all projects permitted, otherwise only the specific
				project is displayed.
	"""
	DebugOut('displayQuestionnairesAndProjects:  enter')
	if not limitScope: # unlimited scope. Display all
		allProjects = getAllProjects()
	else: # limited scope, Display Projects permitted by ProjectAttributes
		allProjects = getAllProjectsWithinScope()
	# further reduce the scope.
	if limitProjectView: # limit Questionnaires only in thisProject
		allProjects = Project.objects.filter(id=thisProject.id)
		
	allQuestionnaireInfo = []
	for aProject in allProjects:
		allQuestionnaires = getQuestionnaireObjsForProject(aProject)
		for aQuest in allQuestionnaires:
			# get info about the Questionnaire
			questionnaireStatus = getQuestionnaireStatusValue(aProject, aQuest)
			#DebugOut('Status for questionnaire %s is %s.' %(aQuest.shortTag,questionnaireStatus))
			spTag = aProject.shortTag
			spRec = aProject.id
			allQuestionnaireInfo.append([
				aQuest.shortTag,	# 0
				aQuest.pageTitle,	# 1
				aQuest.description,	# 2
				aQuest.version,	# 3
				aQuest.versionDate,	# 4
				aQuest.lastUpdate,	# 5
				questionnaireStatus,	# 6
				aQuest.language,	# 7
				spTag,	# 8
				spRec,	# 9
				aQuest.id	# 10
				])
	# record structure
	# [ questionnaire short tag, Page Title, Description, Version, Version Date,
	# Last Update, Enabled/Disabled, Language, Project, record number in Questionnaire
	DebugOut('displayQuestionnairesAndProjects:  exit')
	return allQuestionnaireInfo # list
		
@login_required()
def deleteQuestionnaireView(request):
	"""Delete a Questionnaire.
	
	This function displays a list of Questionnaires and Projects for the user to select
	for deletion. If a Submission exists which points to this record, no deletion actually
	occurs.

	Args:
		"request" input

	Returns:
		return_value: html. 	

	Raises:
		None.
	"""
	DebugOut('deleteQuestionnaireView:  enter')
	limitScope = True # limit view of Projects to those permitted by PorjectAttributes
	# find if default project has been set in the database
	theUser = request.user
	theUserDefaultProject = getAssociatedProjectForUser(theUser)
	limitProjectView = getSessionLimitViewProjectSetting(request)
	currentProjectDefault = theUserDefaultProject
	if limitProjectView: # limit the view to the current project
		if not currentProjectDefault: # Project default not actually set in database
			DebugOut('Current project not defined.')
			limitProjectView = False # Current project not defined, so do not limit scope
		else:
			DebugOut('currentProjectDefault:  %s' %currentProjectDefault.shortTag)
			limitProjectView = True # redundant
	else:
		DebugOut('limitProjectView:  is false, therefore send flag to displayQuestionnairesAndProjects')
		currentProjectDefault = theUserDefaultProject		
	errMsg = []
	if request.method == 'POST':
		DebugOut('after POST')
		if 'SelectQuestionnaire' in request.POST:
			# Default questionnaire selected. It may be different than current working questionnaire
			allQuestionnaireInfo = displayQuestionnairesAndProjects(limitScope, limitProjectView, currentProjectDefault) # this is the list the user is looking at
			[dummyText, listRecNum] = request.POST['SelectQuestionnaire'].split(" ")
			# format is "Select" "record number in display list"
			[theProject, theQuestionnaire] = displayQuestionnairesAndProjectsRetrieve(allQuestionnaireInfo, listRecNum)
			workingQuestionnaireTag = theQuestionnaire.shortTag
			DebugOut('new default questionnaire selected %s' %workingQuestionnaireTag)
			setSessionQuestionnaireProject(request, theProject, theQuestionnaire)
			request.session['delete_QandS'] = [theProject.id, theQuestionnaire.id] # force a second stage for deletion.
			questName = theQuestionnaire.pageTitle
			firstPageObj = getStartPageObj(theQuestionnaire)
			if firstPageObj:
				firstPageInQuestTag = firstPageObj.shortTag
			else:
				firstPageInQuestTag = ''
			barTitle=theQuestionnaire.barTitle
			language=theQuestionnaire.language
		elif 'DeleteQuestionnaire' in request.POST:
			# delete questionnaire
			DebugOut('after DeleteQuestionnaire')
			# retrieve previous selection, if any
			if 'delete_QandS' in request.session:
				# then set
				[theProjectid, theQuestionnaireid] = request.session['delete_QandS']
				theProject = Project.objects.get(id=theProjectid)
				theQuestionnaire = Questionnaire.objects.get(id=theQuestionnaireid)
				[deleteSuccess, errMsg] = deleteQuestionnaireInDB(theQuestionnaire) # Performs delete with additional logic
				del request.session['delete_QandS'] # No defaults
			# Must select a questionnaire!
			workingQuestionnaireTag = '' # no longer exists
			questName = ''
			firstPageInQuestTag = ''
			barTitle = ''
			language = ''
			allQuestionnaireInfo = displayQuestionnairesAndProjects(limitScope, limitProjectView, currentProjectDefault) # display new list
		elif 'returnToHome' in request.POST:
			redirectURL = registrationURL_base + 'userLanding/'
			DebugOut('selectProjectDefault:  exit to %s'%redirectURL)
			return HttpResponseRedirect(redirectURL)
	else:
		allQuestionnaireInfo = displayQuestionnairesAndProjects(limitScope, limitProjectView, currentProjectDefault) # this is the list the user is looking at
		if 'delete_QandS' in request.session:
			# then set
			[theProjectid, theQuestionnaireid] = request.session['delete_QandS']
			theProject = Project.objects.get(id=theProjectid)
			theQuestionnaire = Questionnaire.objects.get(id=theQuestionnaireid)
			# verify that the questionnaire exists in the database.
			workingQuestionnaireTag = theQuestionnaire.shortTag
			questName = theQuestionnaire.pageTitle
			firstPageObj = getStartPageObj(theQuestionnaire)
			if firstPageObj:
				firstPageInQuestTag = firstPageObj.shortTag
			else:
				firstPageInQuestTag = ''
			barTitle=theQuestionnaire.barTitle
			language=theQuestionnaire.language
		else:
			workingQuestionnaireTag = '' # no longer exists
			questName = ''
			firstPageInQuestTag = ''
			barTitle = ''
			language = ''

	currentContext = {
		'workingQuestionnaireTag' : workingQuestionnaireTag,
		'allQuestionnaireInfo' : allQuestionnaireInfo,
		'allowToggleEnable' : False,
		'questName' : questName,
		'firstPageInQuestTag' : firstPageInQuestTag,
		'barTitle' : barTitle,
		'language' : language,
		'back_to_intro' : 'Return to the Introduction Page',
		'url_base' : url_base,
		'errMsg' : errMsg,
		}
	currentContext.update(csrf(request))
	DebugOut('deleteQuestionnaireView:  exit')
	return render(request, workingPageTemplateRoot + 'deleteQuestionnaireView.html',
		currentContext)
def duplicateQuestionnaireView(request):
	"""Select a Questionnaire from a list for duplication.
	Only Questionnaires in the default Project are listed.
	"""
	# retrieve from session data.
	DebugOut('duplicateQuestionnaireView:  enter')
	limitScope = True # limit view of Projects to those permitted by ProjectAttributes
	limitProjectView = True # limit view of Questionnaires to those belonging to the current project
	# find if default project has been set in the database
	[theProject, theQuestionnaire] = getSessionQuestionnaireProject(request)
	theUser = request.user
	if not theProject:
			theProject = getAssociatedProjectForUser(theUser)
	if not theProject:
		# select a project.
		DebugOut('The Project has not been selected')
		errMsg = ['The Project has not been selected']
		redirectURL = registrationURL_base + 'selectProjectDefault/'
		DebugOut('No project, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)
	theProjectTag = theProject.shortTag
	# prepare a list for display of all questionnaires for the project
	errMsg = []
	if request.method == 'POST':
		allQuestionnaireInfo = displayQuestionnairesAndProjects(limitScope, limitProjectView, theProject)
		if 'SelectQuestionnaire' in request.POST:
			DebugOut('SelectQuestionnaire button')
			[dummyText, recNum] = request.POST['SelectQuestionnaire'].split(" ") # format is "Select" "record number"
			recNum = int(recNum) - 1 # start with zero
			workingQuestionnaireTag = allQuestionnaireInfo[recNum][0] # see function 
			workingQuestionnaireRecInDB = allQuestionnaireInfo[recNum][-1] # last element is the record number for the questionnaire
			duplicateThisQuestionnaire = Questionnaire.objects.get(id=workingQuestionnaireRecInDB)
			errMsg.append('Selected Questionnaire:  %s' %workingQuestionnaireTag)
			# Before creation generate a unique name
			DebugOut('Start name: %s'%workingQuestionnaireTag)
			maxLength = 30 # maximum length of a Questionnaire shortTag.
			existingQuestionnaireTags = getQuestionnaireTagsForProject(theProject)
			theNewName = makeUniqueTag( existingQuestionnaireTags, workingQuestionnaireTag, maxLength)
			DebugOut('Updated name: %s'%theNewName)
			newQuestionnaire = duplicateQuestionnaire( theProject, duplicateThisQuestionnaire, theNewName)
			# update the list with the new Questionnaire
			allQuestionnaireInfo = displayQuestionnairesAndProjects(limitScope, limitProjectView, theProject)
			if newQuestionnaire:
				DebugOut('The duplicated Questionnaire name is: %s'%newQuestionnaire.shortTag)
		elif 'returnToHome' in request.POST:
			redirectURL = registrationURL_base + 'userLanding/'
			DebugOut('selectProjectDefault:  exit to %s'%redirectURL)
			return HttpResponseRedirect(redirectURL)
	else:
		allQuestionnaireInfo = displayQuestionnairesAndProjects(limitScope, limitProjectView,theProject)
		newQuestionnaire = None # no questionnaire duplicated

	debugOn = settings.DEBUG
	currentContext = {
		'allQuestionnaireInfo' : allQuestionnaireInfo,
		'newQuestionnaire' : newQuestionnaire,
		'allowToggleEnable' : False,
		'theUser' : theUser,
		'limitProjectView' : True,
		'theProject' : theProject,
		'debugOn' : debugOn,
		'url_base' : url_base,
		'errMsg' : errMsg,
		}
	
	DebugOut('duplicateQuestionnaireView:  exit')
	return render(request, workingPageTemplateRoot + 'duplicateQuestionnaireView.html',
		currentContext)

def selectProjectsQuestionnairesToExecute(request):
	"""Select a Questionnaire and Project from a list for default reference when editing.
	# might be obselete ***
	This function displays a list

	Args:
		"request" input

	Returns:
		return_value: html. 	

	Raises:
		None.
	"""
	# retrieve from session data.
	DebugOut('selectProjectsQuestionnairesToExecute:  enter')
	limitScope = True # limit view of Projects to those permitted by ProjectAttributes
	# find if default project has been set in the database
	theUser = request.user
	theUserDefaultProject = getAssociatedProjectForUser(theUser)
	limitProjectView = getSessionLimitViewProjectSetting(request) #limit questionnaire list to default project
	currentProjectDefault = theUserDefaultProject
	if limitProjectView: # limit the view to the current project
		if not currentProjectDefault: # Project default not actually set in database
			DebugOut('Current project not defined.')
			limitProjectView = False # Current project not defined, so do not limit scope
		else:
			DebugOut('currentProjectDefault:  %s' %currentProjectDefault.shortTag)
			limitProjectView = True # redundant
	else:
		DebugOut('limitProjectView:  is false, therefore send flag to displayQuestionnairesAndProjects')
		currentProjectDefault = theUserDefaultProject		
	# prepare a list for display of all active questionnaires and the project
	errMsg = []
	if request.method == 'POST':
		# prepare a list for display of all active questionnaires and the project
		allQuestionnaireInfo = displayQuestionnairesAndProjects(limitScope, limitProjectView, currentProjectDefault)
		if 'SelectQuestionnaire' in request.POST:
			DebugOut('SelectQuestionnaire button')
			[dummyText, recNum] = request.POST['SelectQuestionnaire'].split(" ") # format is "Select" "record number"
			recNum = int(recNum) - 1 # start with zero
			workingQuestionnaireTag = allQuestionnaireInfo[recNum][0] # see function 
			workingProjectTag = allQuestionnaireInfo[recNum][8] # see function 
			if not workingProjectTag: # if project is not specified
				errMsg.append('Please add a project to "%s" before executing the questionnaire.' %workingQuestionnaireTag)
			workingProjectRec = allQuestionnaireInfo[recNum][9] # see function 
			theProject = Project.objects.get(id=workingProjectRec)
			workingProjectTag = theProject.shortTag # should be the same!
			theRecInDB = allQuestionnaireInfo[recNum][-1] # last element is the record number for the questionnaire
			theQuestionnaire = Questionnaire.objects.get(id=theRecInDB)
			
			if getQuestionnaireStatusValue(theProject,theQuestionnaire) != 'enabled':
				errMsg.append('Please enable "%s" before executing the questionnaire.' %workingQuestionnaireTag)
				enabledFlag = False
			else:
				enabledFlag = True
			if workingProjectTag and enabledFlag: # two conditions required for executing the questionnaire
				# set defaults in session data
				# prepare Session Data environment for running the questionnaire
				removeResponsesFromSessionData(request)
				DebugOut('Removed Response data from Session Data')
				questionnaireEnvironmentPrep( request, theProject, theQuestionnaire)
				urltogo = questionnaireToGo(request, theProject, theQuestionnaire)
				return HttpResponseRedirect(urltogo) # next screen url
		elif 'ToggleDisable' in request.POST:
			# toggle the enable/disable flag for the selected questionnaire
			toggleSelectText = request.POST['ToggleDisable']
			[toggleValue,theRecText]=toggleSelectText.split("_")
			theRecInList = int(theRecText)-1
			theRecInDB = allQuestionnaireInfo[theRecInList][-1] # last element is the record number
			theQuestionnaire = Questionnaire.objects.get(id=theRecInDB)
			if toggleValue == 'enabled':
				setEnabledFlag = 'disabled'
			elif toggleValue == 'disabled':
				setEnabledFlag = 'enabled'
			else: # error none of the above, so enable
				setEnabledFlag = 'enabled'
			theProject = getProjectObjForQuestionnaire( theQuestionnaire)
			setQuestionnaireStatusValue(theProject, theQuestionnaire, setEnabledFlag)
			currentProjectDefault = theProject
			allQuestionnaireInfo = displayQuestionnairesAndProjects(limitScope, limitProjectView, currentProjectDefault) # refresh
		elif 'limitProjectViewSelection' in request.POST:
			DebugOut('In limitProjectViewSelection')
			limitProjectView = getSessionLimitViewProjectSetting(request)
			# toggle
			if limitProjectView:
				limitProjectView = False
			else:
				limitProjectView = True
			setSessionLimitViewProjectSetting(request, limitProjectView) # save the new value
			allQuestionnaireInfo = displayQuestionnairesAndProjects(limitScope, limitProjectView, currentProjectDefault) # refresh
		elif 'returnToHome' in request.POST:
			redirectURL = registrationURL_base + 'userLanding/'
			DebugOut('selectProjectDefault:  exit to %s'%redirectURL)
			return HttpResponseRedirect(redirectURL)
	else:
		allQuestionnaireInfo = displayQuestionnairesAndProjects(limitScope, limitProjectView,currentProjectDefault)
	
	thisHost = request.get_host()
	debugOn = settings.DEBUG
	currentContext = {
		'allQuestionnaireInfo' : allQuestionnaireInfo,
		'allowToggleEnable' : True,
		'theUser' : theUser,
		'limitProjectView' : limitProjectView,
		'currentProjectDefault' : currentProjectDefault,
		'debugOn' : debugOn,
		'thisHost' : thisHost,
		'url_base' : url_base,
		'errMsg' : errMsg,
		}
	currentContext.update(csrf(request))
	DebugOut('selectProjectsQuestionnairesToExecute:  exit')
	return render(request, workingPageTemplateRoot + 'selectProjectsQuestionnairesToExecute.html',
		currentContext)

def simplyExecuteTheQuestionnaire(request):
	"""Run the default questionnaire.
	
	Args:
		"request" input

	Returns:
		return_value: html. 	

	Raises:
		None.
	"""
	DebugOut('simplyExecuteTheQuestionnaire:  enter')
	limitScope = True # limit view of Projects to those permitted by PorjectAttributes
	# prepare a list for display of all active questionnaires and the project

	[theProject, theQuestionnaire] = getSessionQuestionnaireProject(request)
	if not theQuestionnaire:
		errMsg = ['The questionnaire has not been selected']
		return render(request, 'system_error.html', { 'syserrmsg': errMsg})
	workingQuestionnaireTag = theQuestionnaire.shortTag
	if theProject:
		workingProjectTag = theProject.shortTag
	else:
		workingProjectTag = ''
			
	errMsg = []
	limitProjectView = False # does not matter since list is not displayed
	if request.method == 'POST':
		DebugOut('after POST')
		# prepare a list for display of all active questionnaires and the project
		allQuestionnaireInfo = displayQuestionnairesAndProjects(limitScope, limitProjectView, None)
		if 'runQuestionnaire' in request.POST:
			if not workingProjectTag: # if project is not specified
				errMsg.append('Please add a project to "%s" before executing the questionnaire.' %workingQuestionnaireTag)
			if getQuestionnaireStatusValue(theProject,theQuestionnaire) != 'enabled':
				errMsg.append('Please enable "%s" before executing the questionnaire.' %workingQuestionnaireTag)
				enabledFlag = False
			else:
				enabledFlag = True
			if workingProjectTag and enabledFlag: # two conditions required for executing the questionnaire
				# set defaults in session data
				# prepare Session Data environment for running the questionnaire
				removeResponsesFromSessionData(request)
				DebugOut('Removed previous Response data from Session Data')
				urltogo = questionnaireToGo(request, theProject, theQuestionnaire)
				DebugOut('Run Questionnaire %s' %workingQuestionnaireTag)
				return HttpResponseRedirect(urltogo) # next screen url
		elif 'ToggleDisable' in request.POST:
			# toggle the enable/disable flag for the selected questionnaire
			toggleValue = request.POST['ToggleDisable']
			if toggleValue == 'enabled':
				setEnabledFlag = 'disabled'
			elif toggleValue == 'disabled':
				setEnabledFlag = 'enabled'
			else: # error none of the above, so enable
				setEnabledFlag = 'enabled'
			setQuestionnaireStatusValue(theProject, theQuestionnaire, setEnabledFlag)
	
	# Display questionnaire information
	pageTitle = theQuestionnaire.pageTitle
	pageSubTitle = theQuestionnaire.pageSubTitle
	description = theQuestionnaire.description
	footerText = theQuestionnaire.footerText
	version = theQuestionnaire.version
	versionDate = theQuestionnaire.versionDate
	lastUpdate = theQuestionnaire.lastUpdate
	questEnabled = getQuestionnaireStatusValue(theProject,theQuestionnaire)
	language = theQuestionnaire.language
	firstPageObj = getStartPageObj(theQuestionnaire)
	if firstPageObj:
		firstPageTag = firstPageObj.shortTag
	else:
		firstPageTag = ''

	
	thisHost = request.get_host()

	currentContext = {
		'workingQuestionnaireTag' : workingQuestionnaireTag,
		'workingProjectTag' : workingProjectTag,
		'allowToggleEnable' : True,
		'thisHost' : thisHost,
		'pageTitle' : pageTitle,
		'pageSubTitle' : pageSubTitle,
		'description' : description,
		'footerText' : footerText,
		'version' : version,
		'versionDate' : str(versionDate),
		'lastUpdate' : str(lastUpdate),
		'questEnabled' : questEnabled,
		'language' : language,
		'firstPageTag' : firstPageTag,
		'back_to_intro' : 'Return to the Introduction Page',
		'url_base' : url_base,
		'errMsg' : errMsg,
		}
	currentContext.update(csrf(request))
	DebugOut('simplyExecuteTheQuestionnaire:  exit')
	return render(request, workingPageTemplateRoot + 'simplyExecuteTheQuestionnaire.html',
		currentContext)

def restartSession(request,whichProject,whichQuestionnaire):
	""" Allow urls of the type /project/questionnaire to get to the start page of the questionnaire.
	"""
	DebugOut('restartSession:  called when clicking Back to splash')
	DebugOut('whichProject %s, whichQuestionnaire %s' %(whichProject,whichQuestionnaire))
	# Standard verification w.r.t. project and questionnaire
	[theProject, theQuestionnaire, errMess] = verifyQuestionnaireProject(request, whichProject, whichQuestionnaire)
	if errMess != []:
		DebugOut('test %s' %str(errMess))
		# last ditch effort.
		theProject = getProjectObj( whichProject) # query the database
		theQuestionnaire = getQuestionnaireObjFromTags(whichProject, whichQuestionnaire)
		if not theProject or not theQuestionnaire:
			return selectProjectsQuestionnairesToExecute(request)
	# set up environment
	removeResponsesFromSessionData(request) # remove detritus
	DebugOut('Removed Response data from Session Data')
	urltogo = questionnaireToGo(request, theProject, theQuestionnaire)
	DebugOut('restartSession: exit. Calling start page')
	return HttpResponseRedirect(urltogo) # next screen url

@login_required()
def selectQuestionnaireDefault(request):
	"""Select a Questionnaire within scope of the Project as Session Data default.
	"""
	DebugOut('selectQuestionnaireDefault:  enter')
	errMsg = []
	# select a default Questionnaire and Project tag to start.
	[workingProject, workingQuestionnaire] = getSessionQuestionnaireProject(request)
	if not workingProject:
		# select a project.
		errMsg = ['The Project has not been selected']
		redirectURL = registrationURL_base + 'selectProjectDefault/'
		DebugOut('No project, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)
	allQuestionnaires = getQuestionnaireObjsForProject(workingProject)
	
	if request.method == 'POST':
		# Default project selected.
		if 'SelectQuestionnaire' in request.POST:
			[dummyText, listRecNum] = request.POST['SelectQuestionnaire'].split(" ") #decode the response
			# format is "Select" "record number in display list"
			recNum = int(listRecNum) - 1 # start with zero
			theQuestionnaire = allQuestionnaires[recNum]
			setSessionQuestionnaire(request, theQuestionnaire)
			redirectURL = registrationURL_base + 'userLanding/'
			return HttpResponseRedirect(redirectURL)
		elif 'returnToHome' in request.POST:
			redirectURL = registrationURL_base + 'userLanding/'
			DebugOut('selectProjectDefault:  exit to %s'%redirectURL)
			return HttpResponseRedirect(redirectURL)
	
	currentContext = {
		'allQuestionnaires' : allQuestionnaires,
		'workingProject' : workingProject,
		'url_base' : url_base,
		'errMsg' : errMsg,
		}
	currentContext.update(csrf(request))
	DebugOut('selectQuestionnaireDefault:  exit')
	return render(request, 'registration/selectQuestionnaireDefault.html',
		currentContext)
		
def setSessionProjectQuestionnaireDefault(request):
	"""Select a Questionnaire and Project as Session Data default.
	
	This function displays a list of Questionnaires and Projects for the user to select
	as a default. "Default" means that the identities of the Questionnaire and Project
	are saved in Session Data for later retrieval during the life of the Session.

	Args:
		"request" input

	Returns:
		return_value: html. 	

	Session Data:
		Sets session data with function setSessionQuestionnaireProject.
	
	Raises:
		None.
	"""
	DebugOut('setSessionProjectQuestionnaireDefault:  enter')
	limitScope = True # limit view of Projects to those permitted by PorjectAttributes
	limitProjectView = False # do not limit scope to current default project
	errMsg = []
	if request.method == 'POST':
		DebugOut('after POST')
		if 'SelectQuestionnaire' in request.POST:
			DebugOut('after SelectQuestionnaire')
			# Default questionnaire selected. It may be different than current working questionnaire
			allQuestionnaireInfo = displayQuestionnairesAndProjects(limitScope, limitProjectView, None) # generate the list for the user to view
			[dummyText, listRecNum] = request.POST['SelectQuestionnaire'].split(" ") #decode the response
			# format is "Select" "record number in display list"
			[theProject, theQuestionnaire] = displayQuestionnairesAndProjectsRetrieve(allQuestionnaireInfo, listRecNum)
			workingQuestionnaireTag = theQuestionnaire.shortTag
			setSessionQuestionnaire(request, theQuestionnaire)
			errMsg.append('The default Questionnaire selected: %s' %workingQuestionnaireTag)
			if theProject:
				workingProjectTag = theProject.shortTag
				errMsg.append('The default Project selected: %s' %workingProjectTag)
				setSessionProject(request, theProject)
			else:
				workingProjectTag = ''
				errMsg.append('A Project has not been assigned to this questionnaire.')
			removeResponsesFromSessionData(request) # remove previous questionnaire responses
			# prepare environment
			pageBaseURL = questionnaireEnvironmentPrep( request, theProject, theQuestionnaire)
			DebugOut('questionnaireEnvironmentPrep called')
			questName = theQuestionnaire.pageTitle
			firstPageObj = getStartPageObj(theQuestionnaire)
			if firstPageObj:
				firstPageInQuestTag = firstPageObj.shortTag
			else:
				firstPageInQuestTag = ''
			barTitle=theQuestionnaire.barTitle
			language=theQuestionnaire.language
		elif 'returnToHome' in request.POST: # return to Home Page
					redirectURL = registrationURL_base + 'userLanding/'
					return HttpResponseRedirect(redirectURL)
	else: # not a POST
		allQuestionnaireInfo = displayQuestionnairesAndProjects(limitScope, limitProjectView, None) # this is the list the user is looking at
		[theProject, theQuestionnaire] = getSessionQuestionnaireProject(request)
		if theProject:
			workingProjectTag = theProject.shortTag
		else:
			workingProjectTag = ''
		if theQuestionnaire:
			# then set project and questionnaire objects
			workingQuestionnaireTag = theQuestionnaire.shortTag
			questName = theQuestionnaire.pageTitle
			firstPageObj = getStartPageObj(theQuestionnaire)
			if firstPageObj:
				firstPageInQuestTag = firstPageObj.shortTag
			else:
				firstPageInQuestTag = ''
			barTitle=theQuestionnaire.barTitle
			language=theQuestionnaire.language
		else:
			workingQuestionnaireTag = '' # no longer exists
			questName = ''
			firstPageInQuestTag = ''
			barTitle = ''
			language = ''

	currentContext = {
		'workingQuestionnaireTag' : workingQuestionnaireTag,
		'workingProjectTag' : workingProjectTag,
		'allQuestionnaireInfo' : allQuestionnaireInfo,
		'allowToggleEnable' : False,
		'questName' : questName,
		'firstPageInQuestTag' : firstPageInQuestTag,
		'barTitle' : barTitle,
		'language' : language,
		'back_to_intro' : 'Return to the Introduction Page',
		'url_base' : url_base,
		'errMsg' : errMsg,
		}
	currentContext.update(csrf(request))
	DebugOut('setSessionProjectQuestionnaireDefault:  exit')
	return render(request, workingPageTemplateRoot + 'setSessionProjectQuestionnaireDefault.html',
		currentContext)

@login_required()
def editDefaultPageTransitions(request):
	"""Shuffle page order within a Questionnaire.
	
	Args:
		"request" input

	Returns:
		return_value: html. 	

	Raises:
		None.
	"""
	DebugOut('editDefaultPageTransitions:  enter')
	errMsg = []
	[theProject, theQuestionnaire] = getSessionQuestionnaireProject(request)
	DebugOut('Project: %s, Questionnaire: %s' %(theProject, theQuestionnaire))
	if not theProject:
		# select a project.
		DebugOut('The Project has not been selected')
		errMsg = ['The Project has not been selected']
		redirectURL = registrationURL_base + 'selectProjectDefault/'
		DebugOut('No project, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)
	theProjectTag = theProject.shortTag
	if not theQuestionnaire:
		errMsg = ['The questionnaire has not been selected']
		redirectURL = registrationURL_base + 'selectQuestionnaireDefault/'
		DebugOut('No questionnaire selected, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)
	workingQuestionnaireTag = theQuestionnaire.shortTag

	# Will be problems if no pages.
	pagesTF = testForPages(theQuestionnaire)
	if not pagesTF:
		errMsg.append('This questionnaire has no associated pages')
		
	if request.method == 'POST':
		DebugOut('after POST')
		theForm = editDefaultTransitions(request.POST)
		if 'acceptEdits' in request.POST: # accept page transition
			DebugOut('after submitButton')
			if theForm.is_valid():
				DebugOut('Form is valid')
				cleanedData = theForm.cleaned_data
				DebugOut('Cleaned data:  %s' %cleanedData)
				# save ptl list separately
				savePTL = cleanedData['ptlString']
				# edits submitted
				# maintain uniqueness of Questionnaire shortTag
				# set the new ptl whether edited or not
				DebugOut('savePTL:  %s' %savePTL)
				[tagsMissing, tagsAdded] = savePTLToDB(theQuestionnaire, savePTL) # if errors, do not save!
				DebugOut('tagsMissing: %s' %str(tagsMissing))
				if tagsMissing:
					errMsg.append('The following Pages in the Questionnaire were not found in the entered transition table.')
					for aTag in tagsMissing:
						errMsg.append(aTag)
					errMsg.append('Correct this error by adding them to the transition table.')
					errMsg.append('All Pages in the Questionnaire must have a place in the transition table.')
				if tagsAdded:
					errMsg.append('The following Page tags are not in the Questionnaire.')
					for aTag in tagsAdded:
						errMsg.append(aTag)
					errMsg.append('Correct this error by removing new pages from the transition table:')
					errMsg.append('New Pages cannot be added here.')
				if errMsg: # any errors, do not save the transition table
					errMsg.append('The Page transition table is unchanged')
					errMsg.append('Try again with another edit to the page transition table')
					theForm = editDefaultTransitions(cleanedData)
				else: # no errors, update the transition table display to the user
					defaultPTDict = getPageToPageShortTags( theQuestionnaire ) # returns as Dictionary!
					defaultPTString = transitionMatrixToMultiLineDisplay(defaultPTDict)
					DebugOut('No errors, so update defaultPTString: %s' %defaultPTString)
					fieldValueDict = {'ptlString' : defaultPTString}
					errMsg.append('Transition matrix updated.')
					theForm = editDefaultTransitions(initial=fieldValueDict)
			else:
				pass #Form data is not valid
				DebugOut('Form data is not valid')
		elif 'startPage' in request.POST: # accept new start page
			DebugOut('after startPage')
			startPageTag = request.POST['startPage']
			[pageTagToRecord, recordToPageTag ] = getPageToRecordMapping(theQuestionnaire) # returns two dictionaries
			DebugOut('pageTagToRecord: %s' %str(pageTagToRecord))
# 			try:
			startPageObj = Page.objects.get(id=pageTagToRecord[startPageTag])
			errMsg.append('Start page "%s" selected.' %startPageTag)
			# update  or create the start page record
			setStartPageObj(theQuestionnaire, startPageObj)
# 			except:
# 				DebugOut('syserrmsg:  Not able to select start page')
		elif 'returnToHome' in request.POST:
			redirectURL = registrationURL_base + 'userLanding/'
			DebugOut('selectProjectDefault:  exit to %s'%redirectURL)
			return HttpResponseRedirect(redirectURL)
		elif 'executeQuestionnaire' in request.POST:
			redirectURL = url_base + theProjectTag + '/' + workingQuestionnaireTag
			return HttpResponseRedirect(redirectURL)
		else:
			pass #Unknown button hit
			DebugOut('syserrmsg:  Unknown button hit')
			DebugOut('request.POST')
			DebugOut(str(request.POST))
	else: # GET
		DebugOut('after GET')
		# retrieve from the db the transition matrix between pages
		defaultPTDict = getPageToPageShortTags( theQuestionnaire ) # returns as Dictionary!
		defaultPTString = transitionMatrixToMultiLineDisplay(defaultPTDict)
		DebugOut('defaultPTString: %s' %defaultPTString)
		fieldValueDict = {'ptlString' : defaultPTString}
		DebugOut('after GET, fieldValueDict:  %s' %fieldValueDict)
		theForm = editDefaultTransitions(initial=fieldValueDict)

	defaultPT = getDefaultPageTransitions( theQuestionnaire) # as transition list
	# defaultPT is a 2D List of strings - shortTags
	if not defaultPT:
		DebugOut('defaultPT is blank')
		errMsg.append('The page transition matrix does not exist for this questionnaire.')

	questName = theQuestionnaire.pageTitle
	firstPageObj = getStartPageObj(theQuestionnaire)
	if firstPageObj:
		firstPageInQuestTag = firstPageObj.shortTag
	else:
		firstPageInQuestTag = ''
	[pageTagToRecord, recordToPageTag ] = getPageToRecordMapping(theQuestionnaire) # returns two dictionaries
	allPageTags = pageTagToRecord.keys()
	barTitle=theQuestionnaire.barTitle
	language=theQuestionnaire.language
	# getFirstPageObj
	currentContext = {
		'theForm' : theForm,
		'defaultPT' : defaultPT, # from/to pairs
		'workingQuestionnaireTag' : workingQuestionnaireTag,
		'theProjectTag' : theProjectTag,
		'allPageTags' : allPageTags,
		'questName' : questName,
		'firstPageInQuestTag' : firstPageInQuestTag,
		'barTitle' : barTitle,
		'language' : language,
		'back_to_intro' : 'Return to the Introduction Page',
		'url_base' : url_base,
		'errMsg' : errMsg,
		}
	DebugOut('editDefaultPageTransitions:  exit')
	return render(request, workingPageTemplateRoot + 'editDefaultPageTransitions.html',
		currentContext)


@login_required()
def editQuestionnaire(request):
	"""Create a new Questionnaire, or edit an existing Questionnaire.
	
	Args:
		"request" input

	Returns:
		return_value: html. 	

	Raises:
		None.
	"""
	DebugOut('editQuestionnaire:  enter')
	errMsg = []
	[theProject, theQuestionnaire] = getSessionQuestionnaireProject(request)
	if not theQuestionnaire:
		errMsg = ['The questionnaire has not been selected']
		redirectURL = registrationURL_base + 'selectQuestionnaireDefault/'
		DebugOut('No questionnaire selected, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)
	workingQuestionnaireTag = theQuestionnaire.shortTag
	if not theProject:
		# select a project.
		errMsg = ['The Project has not been selected']
		redirectURL = registrationURL_base + 'selectProjectDefault/'
		DebugOut('No project, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)
	theProjectTag = theProject.shortTag

	# May be problems if no pages.
	pagesTF = testForPages(theQuestionnaire)
	if not pagesTF:
		errMsg.append('This questionnaire has no associated pages')
		
	if request.method == 'POST':
		DebugOut('after POST')
# 		DebugOut('request.POST:  %s'%request.POST)
		if 'acceptEdits' in request.POST: # accept questionnaire edits
			DebugOut('after submitButton')
			theForm = editQuestionnaireForm(request.POST)
			if theForm.is_valid():
				DebugOut('Form is valid')
				# check if project change selected.
				if 'ProjectSelect' in request.POST:
					newProjectTag = request.POST['ProjectSelect']
					DebugOut('newProjectTag: %s'%newProjectTag)
					newProjectObj = getProjectObj( newProjectTag)
					setSessionProject(request, newProjectObj)
					setProjectForQuestionnaire(newProjectObj, theQuestionnaire)
					theProject=newProjectObj
					theProjectTag=newProjectTag
				# check the questionnaire tag for identity with an existing tag
				cleanedData = theForm.cleaned_data
				DebugOut('Cleaned data:  %s' %cleanedData)
				cleanedData['versionDate'] = str(cleanedData['versionDate'])
				request.session['editQuestionnaireForm'] = cleanedData # save cleaned data
				# edits submitted
				tempShortTag = cleanedData['shortTag'] # must be unchanged or different from the remainder
				# maintain uniqueness of Questionnaire shortTag
				questTags = getQuestionnaireTagsForProject(theProject)
				workingQuestionnaireTag = theQuestionnaire.shortTag # from database
				if tempShortTag == workingQuestionnaireTag:
					# same record - tag unchanged
					DebugOut('tag is unchanged')
					theQuestionnaire = updateQuestionnaireObj( theQuestionnaire, cleanedData ) # update the record
					theQuestionnaire.save() # update the questionnaire record
# 					saveQuestionnaireObj( theQuestionnaire) # test for Submission against Questionnaire
				elif tempShortTag in questTags:
					DebugOut('Another existing tag selected. No no! Will overwrite')
					# Selected a different existing tag for editing.
					errMsg.append('Questionnaire name %s is identical to an existing Questionnaire.' %stempShortTag)
					errMsg.append('Delete the other Questionnaire first.')
					errMsg.append('Questionnaires %s and %s are untouched.' %(workingQuestionnaireTag,tempShortTag))
				else: # tag is different from any existing tag.
					DebugOut('tag is different')
					theQuestionnaire = updateQuestionnaireObj( theQuestionnaire, cleanedData ) # update the record
					theQuestionnaire.save() # update the questionnaire record
					errMsg.append('Questionnaire %s has been updated.' %tempShortTag)
				DebugOut('Time field in object: %s' %str(theQuestionnaire.versionDate))
				workingQuestionnaireTag = tempShortTag
				theForm = editQuestionnaireForm(cleanedData)
			else:
				pass #Form data is not valid
				DebugOut('Form data is not valid')
		elif 'returnToHome' in request.POST:
			redirectURL = registrationURL_base + 'userLanding/'
			DebugOut('selectProjectDefault:  exit to %s'%redirectURL)
			return HttpResponseRedirect(redirectURL)
		else:
			pass #Unknown button hit
			DebugOut('syserrmsg:  Unknown button hit')
			DebugOut('request.POST')
			DebugOut(str(request.POST))
	else: # GET
		DebugOut('after GET')
		# retrieve from the database
		fieldValueDict = questionnaireOutput( theQuestionnaire )
		DebugOut('after GET, fieldValueDict:  %s' %fieldValueDict)
		# Dates cannot be saved to session data, therefore make into a string
		# delete the "lastUpdate" tag
		del fieldValueDict['lastUpdate']
		fieldValueDict['versionDate'] = str(fieldValueDict['versionDate'])
		fieldValueDict['imageFilePath'] = str(fieldValueDict['imageFilePath'])
		theForm = editQuestionnaireForm(initial=fieldValueDict)
		request.session['editQuestionnaireForm'] = fieldValueDict

	questName = theQuestionnaire.pageTitle
	firstPageInQuestTag = getStartPageObj(theQuestionnaire).shortTag
	barTitle=theQuestionnaire.barTitle
	language=theQuestionnaire.language
	questTags = getQuestionnaireTagsForProject(theProject)
	questTagsList = ', '.join(questTags)
	allProjectTags = getAllProjectTags()
	
	currentContext = {
		'theForm' : theForm,
		'questTagsList' : questTagsList,
		'theProjectTag' : theProjectTag,
		'allProjectTags' : allProjectTags,
		'workingQuestionnaireTag' : workingQuestionnaireTag,
		'questName' : questName,
		'firstPageInQuestTag' : firstPageInQuestTag,
		'barTitle' : barTitle,
		'language' : language,
		'back_to_intro' : 'Return to the Introduction Page',
		'url_base' : url_base,
		'errMsg' : errMsg,
		}
	DebugOut('editQuestionnaire:  exit')
	return render(request, workingPageTemplateRoot + 'editQuestionnaire.html',
		currentContext)

@login_required()
def bulkQuestionEdit(request):
	"""Edit existing questions.
	
	Args:
		"request" input

	Returns:
		return_value: html. 	

	Raises:
		None.
	"""
	DebugOut('bulkQuestionEdit:  enter')
	errMsg = []
	# get default Project and Questionnaire
	[theProject, theQuestionnaire] = getSessionQuestionnaireProject(request)
	DebugOut('Project: %s, Questionnaire: %s' %(theProject, theQuestionnaire))
	if not theProject:
		# select a project.
		DebugOut('The Project has not been selected')
		errMsg = ['The Project has not been selected']
		redirectURL = registrationURL_base + 'selectProjectDefault/'
		DebugOut('No project, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)
	theProjectTag = theProject.shortTag
	if not theQuestionnaire:
		errMsg = ['The questionnaire has not been selected']
		redirectURL = registrationURL_base + 'selectQuestionnaireDefault/'
		DebugOut('No questionnaire selected, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)

	# must have pages associated with the Questionnaire to do anything.
	pagesTF = testForPages(theQuestionnaire)
	if not pagesTF:
		errMsg.append('The questionnaire has no associated pages.')
		return render(request, 'system_error.html', { 'syserrmsg': errMsg})

	# and the pages must have questions
	allQuestions = getAllQuestionObjsForQuestionnaire(theQuestionnaire)
	if allQuestions.count() == 0:
		errMsg.append('The questionnaire has no associated Questions.')
		return render(request, 'system_error.html', { 'syserrmsg': errMsg})
	
	# questionnaire information
	firstPageObj = getStartPageObj(theQuestionnaire)
	firstPageInQuestTag = firstPageObj.shortTag

	# retrieve current page, if any
	if 'currentPageTag_bulkPageEdit' in request.session:
		thisPageObjid = request.session['currentPageTag_bulkPageEdit']
		thisPageObj = Page.objects.get(id=thisPageObjid)
	else:
		thisPageObj = firstPageObj

	# Update form with questions
	thePageQuestions = getPageQuestions(thisPageObj)
	
	initialValues = []
	for aQuestion in thePageQuestions:
		theQRespType = aQuestion.responseType
		theQTag = aQuestion.questionTag
		theQText = aQuestion.questionText # allow html
		initialValues.update({theQTag : theQText})

	theQuestionForm = BulkQuestionEditForm(initial=initialValues, questions=thePageQuestions)
	if request.method == 'POST':
		DebugOut('after POST')
		if 'acceptQuestionEdits' in request.POST:
			theQuestionForm = BulkQuestionEditForm(request.POST, questions=thePageQuestions)
			if theQuestionForm.is_valid():
				DebugOut('after theQuestionForm.is_valid')
				# check the question tag for identity with an existing tag
				cleanedData = theQuestionForm.cleaned_data
				DebugOut('Cleaned data:  %s' %cleanedData)
				# Update the Question record.
				for theQuestion in thePageQuestions:
					[aQuestion, isQuestionUpdated] = updateObjFields(theQuestion,cleanedData)
					if isQuestionUpdated: # so update
						DebugOut('Question updated %s' %theQuestion.shortTag)
# 						aQuestion.save() # debugxx
		elif 'returnToHome' in request.POST:
			redirectURL = registrationURL_base + 'userLanding/'
			DebugOut('selectProjectDefault:  exit to %s'%redirectURL)
			return HttpResponseRedirect(redirectURL)
		else:
			DebugOut('syserrmsg:  bulkQuestionEdit:  unknown button option')
			errMsg.append('bulkQuestionEdit:  unknown button option')




	currentContext = {
		'questionDescription' : 'Good question',
		}
	DebugOut('bulkQuestionEdit:  exit')
	return render(request, 'working_pages/bulkPageEdit.html', currentContext)
	
@login_required()
def bulkPageEdit(request):
	"""Edit existing pages.
	
	Args:
		"request" input

	Returns:
		return_value: html. 	

	Raises:
		None.
	"""
	DebugOut('bulkPageEdit:  enter')
	errMsg = []
	infoMsg = []
	hasEdits = False # no edits yet
	# get default Project and Questionnaire
	[theProject, theQuestionnaire] = getSessionQuestionnaireProject(request)
	DebugOut('Project: %s, Questionnaire: %s' %(theProject, theQuestionnaire))
	if not theProject:
		# select a project.
		DebugOut('The Project has not been selected')
		errMsg = ['The Project has not been selected']
		redirectURL = registrationURL_base + 'selectProjectDefault/'
		DebugOut('No project, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)

	if not theQuestionnaire:
		errMsg = ['The questionnaire has not been selected']
		redirectURL = registrationURL_base + 'selectQuestionnaireDefault/'
		DebugOut('No questionnaire selected, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)
	
	# must have pages associated with the Questionnaire to do anything.
	pagesTF = testForPages(theQuestionnaire)
	if not pagesTF:
		errMsg.append('The questionnaire has no associated pages.')
		return render(request, 'system_error.html', { 'syserrmsg': errMsg})

	# questionnaire information
	firstPageObj = getStartPageObj(theQuestionnaire)
	firstPageInQuestTag = firstPageObj.shortTag
	language=theQuestionnaire.language
	
	# retrieve current page, if any
	if 'currentPageTag_bulkPageEdit' in request.session:
		thisPageObjid = request.session['currentPageTag_bulkPageEdit']
		try:
			thisPageObj = Page.objects.get(id=thisPageObjid)
		except Page.DoesNotExist:
			thisPageObj = firstPageObj
	else:
		thisPageObj = firstPageObj
	
	# Make sure this page is part of the project! Might have switched questionnaires
	allPages = getAllPageObjsForQuestionnaire(theQuestionnaire)
	allPageTags = [ap.shortTag for ap in allPages]
	if thisPageObj not in allPages:
		thisPageObj = firstPageObj # choose the first page not legal. Should not happen!
	
	initialValues ={ # for forms initial data
		'pageTitle' : theQuestionnaire.pageTitle,
		'pageSubTitle' : theQuestionnaire.pageSubTitle,
		'description' : thisPageObj.description,
		'explanation' : thisPageObj.explanation,
		'prologue' : thisPageObj.prologue,
		'epilogue' : thisPageObj.epilogue,
		}
	# Update form with questions
	thePageQuestions = getPageQuestions(thisPageObj)
	# add a blank question to the list
	thePageQuestions.append(Question())
	thePageForm = BulkPageEditForm(initial=initialValues, questions=thePageQuestions)
	theResponseChoices = getResponseChoicesForAPage(thisPageObj)
	
	if request.method == 'POST':
		DebugOut('after POST')
		#DebugOut('request.POST %s'%request.POST)
		if 'acceptPageEdits' in request.POST:
			DebugOut('after accept Page Edits')
			thePageForm = BulkPageEditForm(request.POST, questions=thePageQuestions)
			if thePageForm.is_valid():
				DebugOut('after thePageForm.is_valid')
				# check the question tag for identity with an existing tag
				cleanedData = thePageForm.cleaned_data
				#DebugOut('Cleaned data:  %s' %cleanedData)
				# check the page record and all questions
				isPageUpdated = False
				if thisPageObj.description != cleanedData['description']:
					thisPageObj.description = cleanedData['description']
					isPageUpdated = True
				if thisPageObj.explanation != cleanedData['explanation']:
					thisPageObj.explanation = cleanedData['explanation']
					isPageUpdated = True
				if thisPageObj.prologue != cleanedData['prologue']:
					thisPageObj.prologue = cleanedData['prologue']
					isPageUpdated = True
				if thisPageObj.epilogue != cleanedData['epilogue']:
					thisPageObj.epilogue = cleanedData['epilogue']
					isPageUpdated = True
				if isPageUpdated: # so update the Page record
					if thisPageObj.shortTag == '':
						# Invent a name of the name is null in the object (may or may not be saved)
						newShortTag = 'Page'
						maxLength = 30
						newUniqueName = makeUniqueTag( allPageTags, newShortTag, maxLength)
						thisPageObj.shortTag = newUniqueName
					DebugOut('Page updated %s' %thisPageObj.shortTag)
					infoMsg.append('Page updated')
					thisPageObj.save() # remove for sessionstest**************
				# Update the Question record.
				questionCount = 0
				for theQuestion in thePageQuestions: # already sorted in order of appearance on page
					questionCount+=1
					theQuestionFormTag = 'QuestionText_'+str(questionCount)
					theQuestionTypeTag = 'QuestionType_'+str(questionCount)
					DebugOut('questionCount: %s'%questionCount)
					questSeq = str(questionCount).zfill(3) # will be character sorted
					questionText = theQuestion.questionText
					if theQuestion.questionTag == '':
						theQuestion.questionTag = 'Quest'+questSeq # Kludge - insert a non-blank tag
					updatedQuestionText = cleanedData[theQuestionFormTag]
					responseType = theQuestion.responseType
					upatedResponseType = cleanedData[theQuestionTypeTag]
					DebugOut('Question text: %s' %questionText)
					DebugOut('Question form tag: %s' %theQuestionFormTag)
					if updatedQuestionText == '': # signal to delete the Question if it exists in the DB
						DebugOut('Question text is blank') # therefore delete
						if theQuestion.id: # avoid AssertionError if id set to None
							DebugOut('Question "%s" deleted'%theQuestionFormTag)
							theQuestion.delete()
						continue # continue to the next question
					elif questionText != updatedQuestionText or responseType != upatedResponseType: # so update
						theQuestion.questionText = updatedQuestionText
						if upatedResponseType:
							theQuestion.responseType = upatedResponseType
						elif not responseType:
							theQuestion.responseType = 'CharField'
						
						DebugOut('Question updated %s' %theQuestionFormTag)
						theQuestion.save() # remove for sessionstest**************
						# Update or create the PageRecord table
						updatePageQuestionSequence(thisPageObj,theQuestion, questSeq)
					else:
						DebugOut('Question NOT updated %s' %theQuestionFormTag)
						# however, update PageQuestion table which might have changed due to deletions
						updatePageQuestionSequence(thisPageObj,theQuestion, questSeq)
# 					theResponses = ResponseChoice.objects.order_by('choiceSequence').filter(questionID=theQuestion)
					theResponses = theResponseChoices.order_by('choiceSequence').filter(questionID=theQuestion)
					numResponses = theResponses.count()
					newChoiceList = numResponses == 0 and upatedResponseType in multipleChoiceTypes						
					if upatedResponseType in multipleChoiceTypes:
						# convert choices to a list rather than a query set and add one blank choice
						responseObjList = []
						for aResp in theResponses:
							responseObjList.append(aResp)
						# add one more empty Choice
						blkResp = ResponseChoice(
							questionID = theQuestion,
							)
						responseObjList.append(blkResp) # add blank response to the end.
						if numResponses == 0: # first entry
							# A newly created multiple choice has no "choices", so add an entry
							# Add text as if the user created the entry
							cleanedData.update({'Choice_'+str(1):'this is choice 1'})
					else:
						responseObjList = []
					choiceCount=0
					for aResponse in responseObjList:
						choiceCount+=1
						DebugOut('choiceCount: %s'%choiceCount)
						choiceTag = 'Choice_'+str(choiceCount)
						choiceSequence = str(choiceCount).zfill(2) # zfill pads a string with zeroes
						updatedChoiceText = cleanedData.get(choiceTag,'')
						isResponseChoiceUpdated = False
						if updatedChoiceText == '': # blank so delete the record
							DebugOut('updatedChoiceText text is blank')
							if aResponse.id: # avoid AssertionError if id set to None
								aResponse.delete()
								DebugOut('Choice "%s" deleted'%choiceTag)
							continue # continue to next choice
						elif aResponse.choiceText != updatedChoiceText: # so update
							aResponse.choiceText = updatedChoiceText
							if aResponse.choiceTag == '':
								aResponse.choiceTag = choiceTag
							aResponse.choiceSequence = choiceSequence
							DebugOut('ResponseChoice choiceTag updated %s' %choiceTag)
							DebugOut('ResponseChoice choiceText updated %s' %cleanedData[choiceTag])
							isResponseChoiceUpdated = True
						else:
							if aResponse.choiceTag == '':
								aResponse.choiceTag = choiceTag
								isResponseChoiceUpdated = True
								DebugOut('ResponseChoice choiceTag was null, now is updated.' %choiceTag)
							if aResponse.choiceSequence != choiceSequence:
								aResponse.choiceSequence = choiceSequence
								isResponseChoiceUpdated = True
								DebugOut('ResponseChoice Sequence number is updated.' %choiceTag)
						aResponse.save()
			else:
				msg = 'Page edits not accepted'
				DebugOut(msg)
				errMsg.append(msg)
		elif 'changePageTag' in request.POST: # rename the current page
			DebugOut('in changePageTag')
			# change the name of this page
			if 'newPageTag' in request.POST:
				newShortTag = request.POST['newPageTag'] # interpret this as a "new" page name
				DebugOut('after newPageTag: %s'%newShortTag)
				# subtract the current page name
				# find all existing page shortTag's for this questionnaire
				if newShortTag == thisPageObj.shortTag: # name is unchanged
					infoMsg.append('Page name unchanged.')
				elif newShortTag in allPageTags: # Different from current, but not unique among all tags
					maxLength = 30
					newUniqueName = makeUniqueTag( allPageTags, newShortTag, maxLength)
					infoMsg.append('Page tags for this questionnaire are:')
					infoMsg.append(allPageTags)
					infoMsg.append('Name "%s" changed to unique name: %s'%(newShortTag,newUniqueName))
					newShortTag = newUniqueName
					thisPageObj.shortTag = newShortTag
					thisPageObj.save()
				else:
					thisPageObj.shortTag = newShortTag
					thisPageObj.save()
			else:
				errMsg.append('No page name specified.') # not sure when this would happen.
			DebugOut('out of changePageTag')
		elif 'Back' in request.POST:
			[pageToPageTrackNext, pageToPageTrackPrev] = oneTrackPageToPage(theQuestionnaire)
# 				errMsg.append('Input page is %s' %thisPageObj.shortTag)
# 				for kw,kv in pageToPageTrackPrev.iteritems():
# 					errMsg.append('%s to %s' %(kw.shortTag,kv.shortTag))
			try:
				thisPageObj = pageToPageTrackPrev[thisPageObj]
				request.session['currentPageTag_bulkPageEdit'] = thisPageObj.id
			except:
				errMsg.append('No more pages')
		elif 'Next' in request.POST:
			[pageToPageTrackNext, pageToPageTrackPrev] = oneTrackPageToPage(theQuestionnaire)
			try:
				thisPageObj = pageToPageTrackNext[thisPageObj]
				request.session['currentPageTag_bulkPageEdit'] = thisPageObj.id
			except:
				errMsg.append('No more pages')
		elif 'createNewPageAfter' in request.POST:
			# maintain uniqueness of the short tags for this questionnaire.
			DebugOut('in createNewPageAfter')
			if 'newPageTag' in request.POST:
				newShortTag = request.POST['newPageTag']
				# find all page shortTag's for this questionnaire
				if newShortTag in allPageTags: # not unique
					maxLength = 30
					newUniqueName = makeUniqueTag( allPageTags, newShortTag, maxLength)
					errMsg.append('Name "%s" changed to unique name: %s'%(newShortTag,newUniqueName))
					newShortTag = newUniqueName
				# tag name is unique
				theNewPageObj = createNewPageForQuestionnaireAfter(theQuestionnaire, thisPageObj, newShortTag) # remove for sessiontest********
				request.session['currentPageTag_bulkPageEdit'] = theNewPageObj.id # define this as new page
				thisPageObj = theNewPageObj
			else:
				DebugOut('newPageTag not found')
				errMsg.append('newPageTag not found')
			DebugOut('exit createNewPageAfter')
		elif 'createNewPageBefore' in request.POST:
			# maintain uniqueness of the short tags for this questionnaire.
			DebugOut('in createNewPageBefore')
			if 'newPageTag' in request.POST:
				newShortTag = request.POST['newPageTag']
				# find all page shortTag's for this questionnaire
				if newShortTag in allPageTags: # not unique
					maxLength = 30
					newUniqueName = makeUniqueTag( allPageTags, newShortTag, maxLength)
					errMsg.append('Page tags for this questionnaire are:')
					errMsg.append(allPageTags)
					errMsg.append('Name "%s" changed to unique name: %s'%(newShortTag,newUniqueName))
					newShortTag = newUniqueName
				# tag name is unique
				theNewPageObj = createNewPageForQuestionnaireBefore(theQuestionnaire, thisPageObj, newShortTag) # remove for sessiontest********
				request.session['currentPageTag_bulkPageEdit'] = theNewPageObj.id # define this as new page
				thisPageObj = theNewPageObj
			else:
				DebugOut('newPageTag not found')
				errMsg.append('newPageTag not found')
			DebugOut('exit createNewPageBefore')
		elif 'deleteThisPage' in request.POST:
			DebugOut('in deleteThisPage')
			# try changing the default to the "next" page
			[pageToPageTrackNext, pageToPageTrackPrev] = oneTrackPageToPage(theQuestionnaire)
			DebugOut('pageToPageTrackNext; %s'%str(pageToPageTrackNext))
			try:
				nextPageObj = pageToPageTrackNext[thisPageObj]
				deletePageInQuestionnaire(theQuestionnaire, thisPageObj) # repairs the transition matrix
				thisPageObj = nextPageObj
				request.session['currentPageTag_bulkPageEdit'] = thisPageObj.id
			except: # no pages following.
				deletePageInQuestionnaire(theQuestionnaire, thisPageObj) # repairs the transition matrix
				thisPageObj = getStartPageObj(theQuestionnaire)
				if thisPageObj:
					errMsg.append('No more pages. Go to start page.')
					request.session['currentPageTag_bulkPageEdit'] = thisPageObj.id
				else:
					errMsg.append('The questionnaire has no start page.')
					return render(request, 'system_error.html', { 'syserrmsg': errMsg})			
		elif 'returnToHome' in request.POST:
			redirectURL = registrationURL_base + 'userLanding/'
			DebugOut('selectProjectDefault:  exit to %s'%redirectURL)
			return HttpResponseRedirect(redirectURL)
		else:
			DebugOut('syserrmsg:  bulkPageEdit:  unknown button option')
			errMsg.append('bulkPageEdit:  unknown button option')
		
	# Update form with questions (page perhaps changed with Back or Next
	thePageQuestions = getPageQuestions(thisPageObj)
	# add a blank question to the list
	thePageQuestions.append(Question())
	initialValues ={
		'pageTitle' : theQuestionnaire.pageTitle, # from Questionnaire object
		'pageSubTitle' : theQuestionnaire.pageSubTitle, # from Questionnaire object
		'description' : thisPageObj.description,
		'explanation' : thisPageObj.explanation,
		'prologue' : thisPageObj.prologue,
		'epilogue' : thisPageObj.epilogue,
		}
	thePageForm = BulkPageEditForm(initial=initialValues, questions=thePageQuestions)
# 	infoMsg.append('before attempt') # test
# 	infoMsg.append(thePageForm['Quest_1'])
# 	infoMsg.append('after attempt')
	pageDescription = thisPageObj.description
	
	# Questionnaires referencing this page
	sharingQuestionnaires = getAllQuestionnairesReferencingAPage(thisPageObj)
	# remove the Questionnaire we are editing!
	sharingQuestionnaireTags = []
	for aQuest in sharingQuestionnaires:
		if aQuest != theQuestionnaire:
			sharingQuestionnaireTags.append(aQuest.shortTag)

	lastUpdate = str(thisPageObj.lastUpdate)
	currentContext = {
		'pageDescription' : pageDescription,
		'sharingQuestionnaireTags' : sharingQuestionnaireTags,
		'thePageForm' : thePageForm,
		'theProjectTag' : theProject.shortTag,
		'theQuestionnaire' : theQuestionnaire, # object
		'thisPageObj' : thisPageObj, # object
		'thePageQuestions' : thePageQuestions, # query set
		'thisPageTag' : thisPageObj.shortTag,
		'errMsg' : errMsg,
		'infoMsg' : infoMsg,
		}
	DebugOut('bulkPageEdit:  exit')
	return render(request, 'working_pages/bulkPageEdit.html', currentContext)

@login_required()
def editQuestionNames( request):
	"""All questions in the entire questionnaire are presented in table form.
	Various aspects can be edited:  including the question names.
	"""
	def makeQuestionInfoList(allQuestions):
		allQuestionInfo = []
		ii = 0
		for aQuestion in allQuestions:
			# get all Pages where this Question appears.
			pageTagList = []
			allPQs = PageQuestion.objects.filter(questionID=aQuestion)
			allTags = [aPQ.pageID.shortTag for aPQ in allPQs] # list comprehension
			tagListStr = ', '.join(allTags)
			aRow = [
				aQuestion.questionText, # Text
				aQuestion.questionTag,	# Short tag
				aQuestion.explanation,	# Explanation (viewed by respondent)
				aQuestion.description,	# Description (not viewed by respondent)
				aQuestion.responseType,	# Response type
				str(tagListStr),		# pages which contain this question
				str(aQuestion.id),			# Question record number
				]
			allQuestionInfo.append(aRow)
			ii += 1
		return allQuestionInfo
	DebugOut('editQuestionNames:  enter')
	errMsg = [] # Initialize error messages
	# get default Project and Questionnaire
	[theProject, theQuestionnaire] = getSessionQuestionnaireProject(request)
	DebugOut('Project: %s, Questionnaire: %s' %(theProject, theQuestionnaire))
	if not theProject:
		# select a project.
		DebugOut('The Project has not been selected')
		errMsg = ['The Project has not been selected']
		redirectURL = registrationURL_base + 'selectProjectDefault/'
		DebugOut('No project, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)

	if not theQuestionnaire:
		errMsg = ['The questionnaire has not been selected']
		redirectURL = registrationURL_base + 'selectQuestionnaireDefault/'
		DebugOut('No questionnaire selected, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)
	theQuestionnaireTag = theQuestionnaire.shortTag
	theProjectTag = theProject.shortTag
	# get all possible questions and question tags
	allQuestions = getAllQuestionObjsForQuestionnaire(theQuestionnaire)
	allQuestionInfo = makeQuestionInfoList(allQuestions)
	# List the columns in the Question model
	colList = [
		'Text',
		'Short tag',
		'Explanation',
		'Description (not viewed by respondent)',
		'Response type',
		"Page Tag('s)",
		]
	
	if request.method == 'POST':
		DebugOut('after POST')
		DebugOut('request.POST: %s'%request.POST)
		DebugOut('request.POST type: %s'%type(request.POST))
		if 'acceptEdits' in request.POST: # accept questionnaire edits
			# search for any changes in the data
			for aRow in allQuestionInfo:
				theQRec = aRow[6] # the record number
				theQuestion = allQuestions.get(id=int(theQRec))
				# Test each field for an update.
				updateRecord = False
				if request.POST['ShortTag_Rec_'+theQRec] != theQuestion.questionTag:
					theQuestion.questionTag = request.POST['ShortTag_Rec_'+theQRec]
					updateRecord = True
				if request.POST['Descr_Rec_'+theQRec] != theQuestion.description:
					theQuestion.description = request.POST['Descr_Rec_'+theQRec]
					updateRecord = True
				if updateRecord:
					theQuestion.save()
					DebugOut('Record "%s" updated'%theQRec)
			allQuestions = getAllQuestionObjsForQuestionnaire(theQuestionnaire)
			allQuestionInfo = makeQuestionInfoList(allQuestions)
		elif 'returnToHome' in request.POST:
			redirectURL = registrationURL_base + 'userLanding/'
			DebugOut('selectProjectDefault:  exit to %s'%redirectURL)
			return HttpResponseRedirect(redirectURL)
		else:
			pass #Unknown button hit
			DebugOut('syserrmsg:  Unknown button hit')
			DebugOut('request.POST')
			DebugOut(str(request.POST))
	else: # GET
		DebugOut('after GET')

	currentContext = {
		'allQuestionInfo' : allQuestionInfo,
		'theProjectTag' : theProjectTag,
		'theQuestionnaireTag' : theQuestionnaireTag,
		'colList' : colList,
		'field_types' : FIELD_TYPES,
		'url_base' : url_base,
		'errMsg' : errMsg,
		}
	DebugOut('editQuestionNames:  exit')
	return render(request, workingPageTemplateRoot + 'editQuestionNames.html',
		currentContext)
	
def questionnaireOutput( theQuestionnaire ):
	"""extract Questionnaire data from a query object, and reformat for text display via form
	
	output is a dictionary
	"""
	DebugOut('questionnaireOutput: enter')
	fieldValueDict = getModelFieldValueDict(theQuestionnaire)
	# Make some corrections to make the data display properly!
		
	# fix the time stamp
	if 'versionDate' in fieldValueDict:
		# clip off the right most characters for the time zone setting.
		# must be a better way to do this ***
		versionDateVal = str(fieldValueDict['versionDate'])
		if len(versionDateVal) > 19: # must have timezone information
			versionDateVal = versionDateVal[:-6] # clip it off
			fieldValueDict['versionDate'] = versionDateVal
		
	DebugOut('questionnaireOutput: exit')
	return fieldValueDict
	
def createQuestionnaireObj( inputDict ):
	# Create a questionnaire Object from the input dictionary which is not saved.
	# Will accept a dictionary from questionnaireOutput()

	localInput = {}
	localInput.update(inputDict) # Don't change the input dictionary
	if 'globalFlags' in localInput: # make any corrections to the format
		gflunclean = localInput['globalFlags']
		localInput['globalFlags'] = cleanUpKeywords( gflunclean) # remove blanks, & newlines
	if 'versionDate' not in localInput: # required date field
		localInput['versionDate'] = timezone.now()
	try:
		ptlText = localInput['ptl'].replace(" ","") # assume text input
	except: # don't set ptl value because of error. Perhaps not included in input
		theQuestionnaireObj = Questionnaire(**localInput)
		return theQuestionnaireObj
	if ptlText: # not null
		ptlListOut = ptlText.split(os.linesep) # splits at the end of line
		# now split each csv line a the comma, eliminating blanks.
		ptlListInput = []
		for aLine in ptlListOut:
			fieldsInLine = aLine.replace(" ","").replace("'","").split(',')
			newLine = []
			for oldField in fieldsInLine:
				newLine.append(oldField.strip())
			ptlListInput.append(newLine) # get rid of whitespace and trailing & leading blanks
		localInput['ptl'] = pickle.dumps(ptlListInput) # pickle the list of lists
	
	theQuestionnaireObj = Questionnaire(**localInput)
	return theQuestionnaireObj
	
def updateQuestionnaireObj( qObj, inputDict ):
	DebugOut('updateQuestionnaireObj:  enter')
	#Update a questionnaire Object from the input dictionary.
	# The questionnaire Object is not saved.
	#Will accept a dictionary from questionnaireOutput()

	localInput = {}
	localInput.update(inputDict) # Don't change the input dictionary
	if 'globalFlags' in localInput: # make any corrections to the format
		gflunclean = localInput['globalFlags']
		localInput['globalFlags'] = cleanUpKeywords( gflunclean) # remove blanks, & newlines
	if 'versionDate' not in localInput: # required date field
		localInput['versionDate'] = timezone.now()
	
	for key,value in localInput.iteritems():
			setattr(qObj, key, value)
	DebugOut('updateQuestionnaireObj:  exit')
	return qObj

def cleanUpKeywords( kwInput):
	# Input is a character string with possibly 'linesep' and commas.
	# Linesep are converted to commas. CSV values have blanks removed within and left right.
	kwLinesep = kwInput.split(os.linesep) # break lines into elements of a list
	kwList = []
	for aLine in kwLinesep:
		fieldsInLine = aLine.replace(" ","").split(',')
		newLine = []
		for oldField in fieldsInLine:
			newLine.append(oldField.strip())
		kwList.extend(newLine) # get rid of whitespace and trailing & leading blanks
		kwStr = ','.join(kwList)
	return kwStr
		
def respondentIdent(request, whichProject, whichQuest):
	DebugOut( 'In respondentIdent. whichProject: %s whichQuest: %s' %(whichProject, whichQuest))
	
	errMess = []
	# Standard verification w.r.t. project and questionnaire
	[theProject, theQuestionnaire, errMess] = verifyQuestionnaireProject(request, whichProject, whichQuest)
	if errMess != []:
		return render(request, 'system_error.html', { 'syserrmsg': errMess})
	
	pageBaseURL = request.session['pageBaseURL']
	this_page = 'respondentIdent'
	# Standard page object retrieval
	[thePageObj, success] = getPageObj(theQuestionnaire, this_page)
	if not success:
		errMsg=['Could not find a page transition for %s'%this_page]
		return render(request, 'system_error.html', {'syserrmsg': errMess})
	description = thePageObj.description
	prologue = thePageObj.prologue
	if 'constantPageDataDict' in request.session:
		constantPageDataDict = request.session['constantPageDataDict']
	else:
		return render(request, 'system_error.html', {'syserrmsg': ['Debug:  header and footer page data is missing.']})

	
	# fill fields with previously entered data from this session - if any
	# query Session data for previously entered pt name & bd
	if 'currentRespondent' in request.session:
		DebugOut('form data: %s' %str(request.session['currentRespondent']))
		currentRespondent = request.session['currentRespondent'] # retrieve a dictionary of values
		theForm = RespondentIdentForm(currentRespondent)
	else:
		theForm = RespondentIdentForm()
	
	errmsg = ''
	computerT = computertype(request) # identify computer type
	if request.method == 'POST':
		theForm = RespondentIdentForm(request.POST)
		if request.POST['submitButton'] == 'Back': # save no data
			back_to = UpdateLast_URL_Back(request, this_page)
			return HttpResponseRedirect(pageBaseURL+back_to) # previous screen url
		# Assume clicked button 'Next'
		elif theForm.is_valid():
			UpdateLast_URL_Next(request, this_page) # ignore 'back to' output
			DebugOut('form data: %s' %str(theForm.cleaned_data))
			if 'birthDate' in theForm.cleaned_data:
				# make it JSON searlializable by making it a string
				theForm.cleaned_data['birthDate'] = str(theForm.cleaned_data['birthDate'])
			request.session['currentRespondent'] = theForm.cleaned_data
			if respondentIDDict in request.session: # aggregate user identification
				request.session[respondentIDDict].update(theForm.cleaned_data)
			else: # create user identification
				request.session[respondentIDDict] = theForm.cleaned_data
			next_pageObj = pageCalc(request,theQuestionnaire, thePageObj )
			next_page = next_pageObj.shortTag
			DebugOut( 'respondentIdent: exit')
			return HttpResponseRedirect(pageBaseURL+next_page) # next screen url

	computerT = computertype(request) # identify computer type
	dynamicPageDetails = pagePerComputer(computerT)
	fontSize = dynamicPageDetails['fontSize']
	fontSizeTextBox = dynamicPageDetails['fontSizeTextBox']

	contextDict = {'theForm': theForm,
		'errmsg' : errmsg,
		'computerT' : computertype(request),
		'theProject' : theProject,
		'explanation' : SubstituteWords( thePageObj.explanation ),
		'prologue' : prologue,
		'field_border' : '0',	# border width - zero is ok.
		'field_style' : 'as_p',
		'fontSize' : fontSize,
		'fontSizeTextBox' : fontSizeTextBox,
		'barTitle' : 'Respondent Identity',
		}
	currentContext = constantPageDataDict.copy()
	currentContext.update(contextDict)
	DebugOut( 'respondentIdent: exit')
	return render(request, 'respondentIdent.html', currentContext)
	
def pageCalc(request,theQuestionnaire, thePageObj, **kwargs ):
	# calculates the next page tag given the current state of the session data.
	DebugOut('pageCalc: entering')
	currentPageTag = thePageObj.shortTag
	DebugOut('pageCalc: current page is %s' %currentPageTag)
	nextPageObj = getNextPageFromDB(theQuestionnaire, thePageObj)
	if nextPageObj:
		nextPageTag = nextPageObj.shortTag
		DebugOut('pageCalc: used Default to calculate current/next page %s/%s' %(currentPageTag,nextPageTag))
	else:
		DebugOut('syserrmsg: pageCalc: no default page available!')
		nextPageTag = 'completion'
		# Standard page object retrieval
		[nextPageObj,success] = getPageObj(theQuestionnaire, nextPageTag)
		if not success:
			nextPageObj = Page() # Punt the problem upstairs
	
	if 'questionResults' in kwargs: # incoming question results ****************
		DebugOut('pageCalc:  incoming question results')
		questionResults = kwargs.pop('questionResults')
		DebugOut('pageCalc:  questionResults: %s' %questionResults)
		# check for calculated next page
		nextfromCalc =getNextPageFromCalculation(theQuestionnaire, thePageObj, questionResults)
		if nextfromCalc:
			nextPageTag = nextfromCalc.shortTag
			nextPageObj = nextfromCalc
			DebugOut('pageCalc:  Have a match for a calculated next page: %s' %nextPageTag)
		else:
			DebugOut('pageCalc:  No match for a calculated next page')

	# Check for global flags match to question response
	[nextfromGlobal, useGlobal] = getNextPageFromGlobalFlags(request, theQuestionnaire, thePageObj)
	if useGlobal:
	   nextPageObj = nextfromGlobal # next page
	   DebugOut('pageCalc:  Match for a global flag determined next page %s' %nextPageObj.shortTag)

	DebugOut('pageCalc: exit')
	return nextPageObj

def imageCalc(current_page ):
	# calculates True or False, if an image is present on the page.

	if current_page in ['P1','P2']:
		imagePresent = True
	else:
		imagePresent = False

	return imagePresent


def Completion(request, whichProject, whichQuest):
	"""Completion is the last page of the questionnaire. This page offers buttons to
	email the summary data or to return to the start page.
	
	"""
	
	DebugOut( 'In Completion.')

	# Standard verification w.r.t. project and questionnaire
	[theProject, theQuestionnaire, errMess] = verifyQuestionnaireProject(request, whichProject, whichQuest)
	if errMess != []:
		return render(request, 'system_error.html', { 'syserrmsg': errMess})

	firstpage = getStartPageObj(theQuestionnaire).shortTag # return to first page

	if 'constantPageDataDict' in request.session:
		constantPageDataDict = request.session['constantPageDataDict']
	else:
		return render(request, 'system_error.html', {'syserrmsg': ['Debug:  header and footer page data is missing.']})


	current_date = timezone.now()
	pageBaseURL = request.session['pageBaseURL']
	try:
		request.session.delete_test_cookie() # remove cookie
		DebugOut('Completion:  cookie removed.')
	except:
		DebugOut('Completion:  cookie not removed.')

	if respondentIDDict in request.session: # aggregate user identification
		try:
			contactEmail = request.session[respondentIDDict]["contactEmail"]
		except:
			contactEmail = ""
	else:
		contactEmail = ""

	if not contactEmail:
		removeResponsesFromSessionData(request) # No contact email, so delete
		# pt data in session data.
			
	if "summaryPagehtml" in request.session:
		summaryExist = True
	else:
		summaryExist = False
		sentMail = "Questionnaire summary data not created"

	sentMail = ""
	if request.method == 'POST':
		DebugOut( 'In POST.')
		if "submitButton" in request.POST:
			DebugOut( 'In submitButton.')
			if request.POST["submitButton"] == "Submit e-mail": # html checks contactEmail
				DebugOut( 'In Submit e-mail.')
				current_date_short = str(current_date)[:16]
				emailSubj = 'screener results for %s' % current_date_short
				questionnaireEmail = theProject.email # email "from" this address
				DebugOut('questionnaireEmail: %s'%questionnaireEmail)
				if summaryExist: # send risk page with html
					DebugOut('Found summary information to send.')
					html_content = "%s" %request.session["summaryPagehtml"]
					msg = EmailMessage(emailSubj, html_content, questionnaireEmail, [contactEmail])
					msg.content_subtype = "html"  # Main content is now text/html
					sentMail = "Email has been sent to: " + contactEmail
					summaryExist = True
				else:
					DebugOut('No summary information.')
					adminEmail = settings.DEFAULT_FROM_EMAIL # send error message back to screener
					emailBody = 'Error message to '+adminEmail +'\n Error, no summary data %s' % current_date
					msg = EmailMessage(emailSubj, emailBody, questionnaireEmail, [adminEmail])
					sentMail = 'Admin has been informed of an error: ' + adminEmail
					summaryExist = False
				try:
					msg.send()
					removeResponsesFromSessionData(request) # remove Respondent data
# 				except SMTPAuthenticationError:
# 					DebugOut('SMTPAuthenticationError ')
# 					sentMail = 'SMTP Authenticaion Error - try again in a few minutes'
				except:
					DebugOut('Other exception upon attempting to send email ')
					sentMail = 'Unknown error sending email. Please report.'
					removeResponsesFromSessionData(request) # remove Respondent data
			elif request.POST["submitButton"] == "start": # return to start page
				DebugOut( 'In start.')
				removeResponsesFromSessionData(request) # remove Respondent data
				questionnaireEnvironmentPrep( request, theProject, theQuestionnaire)
				urltogo = questionnaireToGo(request, theProject, theQuestionnaire)
				return HttpResponseRedirect(urltogo)
			else:	# not contactEmail
				removeResponsesFromSessionData(request) # remove respondent data
		
	computerT = computertype(request) # identify computer type
	dynamicPageDetails = pagePerComputer(computerT)
	fontSize = dynamicPageDetails['fontSize']

	computerT = computertype(request) # identify computer type
	dynamicPageDetails = pagePerComputer(computerT)
	fontSize = dynamicPageDetails['fontSize']
	fontSizeTextBox = dynamicPageDetails['fontSizeTextBox']

	contextDict = {
		'thishost' : request.get_host(),
		'summaryExist' : summaryExist,
		'contactEmail' : contactEmail,
		'current_date' : current_date,
		'fontSize' : fontSize,
		'fontSizeTextBox' : fontSizeTextBox,
		'sentMail' : 	sentMail,
		'fontSize' : fontSize,
		}
	currentContext = constantPageDataDict.copy()
	currentContext.update(contextDict)

	return render(request, 'Completion.html', contextDict)

def uniquePTID(firstName, middleName, lastName, birthDate):
	# construct a unique Respondent id
	respondentName = firstName+' '+middleName+' '+lastName
	respondentName = respondentName.title() # capitalize each word to reduce variation
	respondentName = respondentName.replace(' ','').replace('.','') # reduce variation
	uid = "%s %s" % (birthDate, respondentName)
	return uid
	
def ListQuestionsForQuestionnaire(aQuaireObj):
	"""List all questions from all pages belonging to a Questionnaire
	Args:
		aQuaireObj:  a Questionnaire object
		
	Returns: a list with the record structure: [pageList, fieldList, theList, tagToText]
		pageList:  a list of Page.shortTags in a standard order
		fieldList:  a list of Unique tags for questions (or muliple choices)
			This tag is constructed out of the record numbers, which guarentees uniqueness
		theList: a list with record structure:
			[aPageTag, theQLabel, qText]
				aPageTag:  Page.shortTag
				theQLabel:  a Unique tag for question (or muliple choices)
				qText:  human readable text which is displayed with the multiple choice
					Question.questionText for question prompt OR
					ResponseChoice.choiceText for multiple choice
		tagToText: a dictionary tranlation of the Unique tag to question text
			theQLabel: (key) 
			qText: Question.questionText
			OR
			qText: ResponseChoice.choiceText
	"""
	DebugOut('Entering ListQuestionsForQuestionnaire')
	qpObj = allPagesInDefaultOrder(aQuaireObj)
	fieldList = []
	theList = []
	pageList = []
	tagToText = {}
	for ap in qpObj: # examine each page in the questionnaire
		DebugOut('Top of page loop')
		aPageObj = ap
		aPageTag = aPageObj.shortTag
		DebugOut('processing page: %s' %aPageTag)
		pageList.append(aPageTag)
		thePageQuestionsAll = getPageQuestions(aPageObj) # get all questions on the page
		DebugOut('Number of questions found: %s' %len(thePageQuestionsAll))
		DebugOut('thePageQuestionsAll: %s' %thePageQuestionsAll)
		for aQuest in thePageQuestionsAll: # examine each question on a page
			DebugOut('at the top of the questions on the page loop')
			theQRecNum = str(aQuest.id)
			theQLabel = encodeQuestionResponseLabel(theQRecNum,'')
			DebugOut('after theQLabel: %s'% theQLabel)
			qText = aQuest.questionText
			DebugOut('question text: %s' %qText)
			questionType = aQuest.responseType # look for MultipleChoiceField
			DebugOut('Before determining multichoice')
			responseCount = ResponseChoice.objects.filter( questionID=aQuest).count()
			if responseCount>0: # go down to sublist for MultipleChoiceField
				DebugOut('found a MultipleChoiceField for question label: %s' %theQLabel)
				DebugOut('questionType: %s' %questionType)
				tagToText.update({theQLabel:qText}) # add the tag for the multi choice
				fieldList.append(theQLabel)
				theList.append([aPageTag, theQLabel, qText])
				theResponses = ResponseChoice.objects.order_by('choiceSequence').filter(questionID=aQuest)
				# collect the multiple responses
				DebugOut('Number of multiple responses: %s' %len(theResponses))
				for aResponse in theResponses:
					DebugOut('aResponse: "%s"'%aResponse.choiceText)
					theChoiceRecNum = str(aResponse.id)
					theQResponseLabel = encodeQuestionResponseLabel(theQRecNum,theChoiceRecNum)
					DebugOut('Multiple choice label %s' %theQResponseLabel)
					qText = aResponse.choiceText
					DebugOut('MultipleChoiceField tag & text: %s %s' %(theQResponseLabel,qText))
					tagToText.update({theQResponseLabel:qText}) # add Subchoices
					fieldList.append(theQResponseLabel)
					theList.append([aPageTag, theQResponseLabel, qText])
					DebugOut('Multiple choice appended to the list %s' %theQResponseLabel)
				DebugOut('Exiting multiple choice.')
			else:
				DebugOut('found a single choice for tag: %s' %theQLabel)
				tagToText.update({theQLabel:qText})
				fieldList.append(theQLabel)
				theList.append([aPageTag, theQLabel, qText])
				DebugOut('Single choice appended to the list')
	# make the output list of question field tags unique by eliminating the first of a succession of duplicate
	DebugOut('Before makeUniqueListReverse')
	fieldList = makeUniqueListReverse(fieldList)
	DebugOut('After makeUniqueListReverse')
	DebugOut('Exiting ListQuestionsForQuestionnaire')
	return [pageList, fieldList, theList, tagToText]

def formatResponseforDisplay(request):
	"""Pull questionnaire response data from session data, then reformat into a list
	ultimately for display via a template.
	"""
	DebugOut('formatResponseforDisplay:  enter')
	success = True
	if allResultsList in request.session:
		allResults = request.session[allResultsList]
		DebugOut('Have results data')
	else:
		errMsg = 'No questionnaire response session data'
		DebugOut(errMsg)
		success = False
		questionResponseList = ['']
		return [questionResponseList, success]

	# go through all key values, in order answered
	questionResponseList = []
	# create the page results list
	# reverse the list to get time-ordered output
# 	allResults.reverse()
	for aline in allResults:
		# request.session[allResultsList] structure: 
	#	[questionResponse, questionText,questionRecNum,responseChoiceRecNum,pageShortTag,pageRecNum, uniqueQuestionLabel, questionTag]
		rawQuestionResponse = aline[0]
		questionText = strip_tags(aline[1]) # no html in the Summary
		#DebugOut('questionText: %s' %questionText)
		questionRecNum = aline[2]
		responseChoiceRecNum = aline[3]
		pageShortTag = aline[4]
		pageRecNum = aline[5]
		uniqueTagNotUsed = aline[6]
		questionTag = aline[7]
		if type(rawQuestionResponse) == list:
			# null value since value is a set of keywords
			listLevel = 'sub'
			questionResponseList.append([listLevel, questionText,"", pageShortTag])
			#DebugOut('rawQuestionResponse: "%s"'%rawQuestionResponse)
			for aValue in rawQuestionResponse: # create additional lines, one for each element in the list
				#DebugOut('in choice loop: aValue %s' %aValue)
				questionResponseList.append([listLevel, aValue,'', pageShortTag])
		else:# not a list, therefore at the main level
			listLevel = 'main'
			questionResponse = str(rawQuestionResponse)
			#DebugOut('questionResponse: %s' %questionResponse)
			theLine = [listLevel, questionText, questionResponse, pageShortTag]
			questionResponseList.append(theLine)
			#DebugOut(theLine)
	# questionResponseList record structure:
	# [listLevel, questionText, questionResponse, pageShortTag]
	DebugOut('formatResponseforDisplay:  exit')
	return [questionResponseList, success]

def questionnaireSummary(request, whichProject, whichQuest, whichPage):
	DebugOut("questionnaireSummary:  enter")
	# Standard verification w.r.t. project and questionnaire
	[theProject, aQuaireObj, errMess] = verifyQuestionnaireProject(request, whichProject, whichQuest)
	if errMess != []:
		return render(request, 'system_error.html', { 'syserrmsg': errMess})
		
	[thePageObj, success] = getPageObj(aQuaireObj, whichPage)
	if not success:
		errMsg=['Could not find page %s'%whichPage]
		return render(request, 'system_error.html', {'syserrmsg': errMess})

	this_page = whichPage
	pageBaseURL = settings.WSGI_URL_PREFIX + 'multiquest/' + whichProject+'/'+whichQuest+'/'
	DebugOut('Current page url: %s' %this_page)
	
	explanation = SubstituteWords( thePageObj.explanation )
	prologue = SubstituteWords( thePageObj.prologue )
	epilogue = SubstituteWords( thePageObj.epilogue )
	
	# debug
# 	[pageList, fieldList, theList, tagToText ] = List__QuestionsForQuestionnaire(aQuaireObj) # name mangled intentionally.
	
	# reformat the responses residing in session data to a list
	[questionResponseList, success] = formatResponseforDisplay(request)
	# strip_tags
	if not success:
		errMsg = ['No questionnaire response session data']
		DebugOut(errMsg)
		return render(request, 'system_error.html', {'syserrmsg': errMess})
	
	if allResultsDict not in request.session:
		errMsg = ['No session data']
		DebugOut(errMsg)
		return render(request, 'system_error.html', {'syserrmsg': errMess})


	# find key values in session data which are NOT in "fieldList". If so document
# 	keyList = allResultsDictValues.keys()
# 	DebugOut('Debug only: Following is a list of pt entered keys unknown:')
# 	kk = 0
# 	for aKey in keyList:
# 		if aKey not in fieldList:
# 			DebugOut('syserrmsg: questionnaireSummary: Unknown key: %s' %aKey)
# 			kk = kk+1
# 	if kk == 0:
# 		DebugOut('All keys were found.')


	if 'constantPageDataDict' in request.session:
		constantPageDataDict = request.session['constantPageDataDict']
	else:
		return render(request, 'system_error.html', {'syserrmsg': ['Debug:  header and footer page data is missing.']})

	# must have the following data
	if respondentIDDict in request.session:
		respIDDict = request.session[respondentIDDict]
	else:
		# pt data is missing
		# return to respondent id page
		next_pageObj = pageCalc(request,aQuaireObj, thePageObj )
		next_page = next_pageObj.shortTag
		DebugOut('Pt data NOT found for questionnaireSummary page. Next page is: %s' %next_page)
		return HttpResponseRedirect(pageBaseURL+next_page) # next screen url
		
	if "lastName" in respIDDict:
		lastName = respIDDict['lastName'].title() # capitalize each word
		respIDDict['lastName'] = lastName # save capitalized form
	else: # if no Respondent name, return to splash screen
		return render(request, 'system_error.html', {'syserrmsg': ['Debug:  Pt lastName is missing.']})

	if "middleName" in respIDDict:
		middleName = respIDDict['middleName'].title() # capitalize each word
		respIDDict['middleName'] = middleName # save capitalized form
	else: # if no Respondent name, return to splash screen
		pass # not required

	if "firstName" in respIDDict:
		firstName = respIDDict['firstName'].title() # capitalize each word
		respIDDict['firstName'] = firstName # save capitalized form
	else: # if no Respondent name, return to splash screen
		return render(request, 'system_error.html', {'syserrmsg': ['Debug:  Pt firstName is missing.']})

	if len(middleName) == 0:
		respondentName = lastName+', '+firstName
	else:
		respondentName = lastName+', '+firstName+', '+middleName

	if "birthDate" in respIDDict:
		birthDate = respIDDict['birthDate']
	else: # if no respondent bd, return to splash screen
		return render(request, 'system_error.html', {'syserrmsg': ['Debug:  Pt birthdate is missing.']})
	current_date = timezone.now()
	DebugOut('birthDate')
	DebugOut(str(birthDate))
	DebugOut('data type: %s' %type(birthDate))
#	pt_currentAge = calculate_ptAge_now( datetime.strptime(str(birthDate), '%Y-%m-%d'))
	pt_currentAge = ''
	# *** the preceding line is a mess and should be improved - but how?
	# error is obtained without "datetime.strptime(str(birthDate), '%Y-%m-%d')"
	# the following obtains a TypeError:
	# 'tzinfo' is an invalid keyword argument for this function
	# Location:  /Library/Python/2.7/site-packages/django/utils/timezone.py in make_aware
	# make_aware, inside calculate_ptAge_now, is very simple:  value.replace(tzinfo=timezone)
	#pt_currentAge = calculate_ptAge_now( birthDate)
	
	if 'contactEmail' in respIDDict:
		contactEmail = respIDDict['contactEmail']
	else:
		contactEmail = "" # not required

	if 'contactPhone' in respIDDict:
		contactPhone = respIDDict['contactPhone']
	else:
		contactPhone = "" # not required
	
	pageBaseURL = request.session['pageBaseURL']
	projectAbbrev = theProject.abbrev
	
	projectContactPhone = theProject.contactPhone
	DebugOut('questionnaireSummary:  creating contextDict')
	
	computerT = computertype(request) # identify computer type
	dynamicPageDetails = pagePerComputer(computerT)
	fontSize = dynamicPageDetails['fontSize']
	fontSizeTextBox = dynamicPageDetails['fontSizeTextBox']

	contextDict = {
		'barTitle' : 'Questionnaire Summary Page',
		'respondentName' : respondentName,
		'birthDate' : birthDate,
		'pt_currentAge': pt_currentAge,
		'startQURL' : pageBaseURL,
		'contactEmail' : contactEmail,
		'contactPhone' : contactPhone, # respondent contact phone
		'current_date' : current_date,
		'explanation' : explanation,
		'prologue' : prologue,
		'epilogue' : epilogue,
		'projectAbbrev' : whichProject,
		'projectContactPhone' : projectContactPhone,
		'questionResponseList': questionResponseList,
		'fontSize' : fontSize,
		'fontSizeTextBox' : fontSizeTextBox,
# 		'respondentCallbackNumber' : request.session["respondentCallbackNumber"],
		}

	if request.method == 'POST':
		DebugOut('questionnaireSummary:  inside POST')
		DebugOut('this_page %s' %this_page)
		if request.POST['submitButton'] == 'Back':
			DebugOut( 'BACK button clicked')
			back_to = UpdateLast_URL_Back(request, this_page)
			DebugOut('back to page %s' %back_to)
			return HttpResponseRedirect(pageBaseURL+back_to) # previous screen url
		elif request.POST['submitButton'] == 'Next':
			DebugOut('Next button clicked')
			UpdateLast_URL_Next(request, this_page) # ignore 'back to' output
			# make a copy of the summary page and save it
			currentContext = constantPageDataDict.copy()
			currentContext.update(contextDict)
			currentContext.update({'buttons_not_enabled': True}) # leave off the buttons for email!
# 			DebugOut('questionnaireSummary: page context: %s' %currentContext)
			summaryPagehtml = render(request, 'questionnaireSummary.html', currentContext)
			request.session["summaryPagehtml"]=str(summaryPagehtml) # save the html for possible email
			savePtResponse(request) # save data to database
			next_pageObj = pageCalc(request,aQuaireObj, thePageObj )
			next_page = next_pageObj.shortTag
			UpdateLast_URL_Next(request, this_page) # ignore 'back to' output
			if next_page != '':
				DebugOut('Edits to the summary done, so exit page "%s" to next page "%s"' %(this_page, next_page))
				return HttpResponseRedirect(pageBaseURL+next_page) # next screen url
			else: # assume at the end of the questionnaire
				DebugOut( 'syserrmsg: Next page is null. Completion? this_page: %s, next_page: %s' %(this_page,next_page))
				return HttpResponseRedirect( pageBaseURL+'completion/')
	else:  # not POST
		DebugOut('questionnaireSummary:  inside GET')
		DebugOut('this_page %s' %this_page)

	currentContext = constantPageDataDict.copy()
	currentContext.update(contextDict)

# 	summaryPagehtml = render(request, 'questionnaireSummary.html', contextDict)
# 	request.session["summaryPagehtml"]=str(summaryPagehtml) # save the context for possible email
	DebugOut('questionnaireSummary:  exit')
	return render(request, 'questionnaireSummary.html', contextDict)

def respondentName( respodentObj ):
	# return respondent concatenated name
	firstName = respodentObj.firstName
	middleName = respodentObj.middleName
	lastName = respodentObj.lastName
	if len(middleName) == 0:
		respName = lastName+', '+firstName
	else:
		respName = lastName+', '+middleName+', '+firstName
	return respName

@login_required()
def displaySubmissionDataForProject(request):
	"""Displays all submissions pointing to questionnaires in a project.
	"""
	theProject = getSessionProject(request)
	if not theProject:
		# fall back to user default
		theUser = request.user
		theProject = getAssociatedProjectForUser(theUser)
	if not theProject:
		# Redirect if still no project
		redirectURL = registrationURL_base + 'selectProjectDefault/'
		DebugOut('No project, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)
	# Display Submissions
	DebugOut('Output csv file for Proejct %s'%theProject.shortTag)
	result = responseViewer(request, forProject=theProject)
	return result

def makeSubmissionListForDisplay(allSubmissions, firstColLabel='Select', firstColPrefix='R_'):
	"""
	Format Submissions as a list to prepare for display.
	"""
	submitTable = []
	ii = 1
	for aSubmission in allSubmissions:
		theResppondent = aSubmission.respondentID
		DebugOut('Including Respondent: %s' %theResppondent.ptUniqueID)
		respObj = aSubmission.respondentID
		respName = respondentName( respObj )
		contactEmail = respObj.contactEmail
		aRow = [
			firstColPrefix+str(ii), # provide a selection method
			aSubmission.lastUpdate,
			respName,
			aSubmission.questionnaireID.barTitle,
#			aSubmission.completedYN,
			contactEmail,
			aSubmission.reviewedBy,
			aSubmission.reviewDate,
			aSubmission.okForExport,
			]			
		submitTable.append(aRow)
		ii = ii+1
	submitTableCols = [
		firstColLabel,
		'Submit date',
		"Respondent's Name",
		'Questionnaire',
		"Respondent's Email",
#		'Completed?',
		'Reviewed By',
		'Review Date',
		'Ok for data Export?',
		]			

	return [submitTable, submitTableCols]

def dumpSubmissionTable(request):
	"""
	# Dump the Submission table.
	Do not limit scope to that of the Project
	"""
	DebugOut('responseViewerAll:  entering')
	errMsg = []
	allSubmissions = Submission.objects.all().order_by('questionnaireID__shortTag', '-lastUpdate')
	if len(allSubmissions) == 0:
		errMsg.append('Zero submissions. No Questionnaire submissions to display for this Project.')
		urlPrefix = request.get_host()+settings.WSGI_URL_PREFIX
		return render(request, 'InfoScreenExit.html', { 'errMsg': [errMsg], 'wsgiPrefix':urlPrefix})
	# make a table of submissions
	[submitTable, submitTableCols] = makeSubmissionListForDisplay(allSubmissions)
	tableName = 'List the Submission Table - all Projects'
	
	return render(request, workingPageTemplateRoot + 'tablelisting.html',
		{'pageTitle' : tableName,
		'allValues' : submitTable,
		'colList' : submitTableCols,
		'bannerText' : tableName,
		'bannerText1' : '',
		'back_to' : registrationURL_base + 'userLanding/',
		'back_toPrompt' : 'Return to the Home Page',
		'errMsg' : errMsg,
		})

def getSubmissionsForProject(theProject):
	"""
	Retrieve all Submission objects for a Project
	"""
	# Get the Questionnaires for this project.
	allQuestionnaires = getQuestionnaireObjsForProject(theProject)
	# get all Submissions for these questionnaires
	# set up a query "OR"
	if allQuestionnaires.count() == 0: # no Projects, so return empty queryset
		allSubmissions = Submission.objects.none()
	else:
		queryOR = Q(questionnaireID=allQuestionnaires[0].id)
		DebugOut('Including Questionnaire: %s' %allQuestionnaires[0].shortTag)
		if len(allQuestionnaires) >1:
			for aQuestionnaire in allQuestionnaires[1:]:
				DebugOut('Including Questionnaire: %s' %aQuestionnaire.shortTag)
				queryOR = queryOR | Q(questionnaireID=aQuestionnaire.id)
		allSubmissions = Submission.objects.filter(queryOR).order_by('questionnaireID__shortTag', '-lastUpdate')

	return allSubmissions
	
@login_required()
def responseDelete(request,selectAllSubmissions=False):
	"""
	# Select and delete questionnaire responses.
	Limit scope to that of the Project
	"""
	DebugOut('responseDelete:  entering')
	errMsg = []
	theProject = getSessionProject(request)
	if not theProject: # not in session data
		# fall back to user default
		theUser = request.user
		theProject = getAssociatedProjectForUser(theUser)
	if not theProject:
		# Redirect if still no project
		redirectURL = registrationURL_base + 'selectProjectDefault/'
		DebugOut('No project, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)
	# Get the Submissions for this project or for all projects.
	if selectAllSubmissions:
		allSubmissions = Submission.objects.all()
	else:
		allSubmissions = getSubmissionsForProject(theProject)
	if len(allSubmissions) == 0:
		errMsg.append('Zero submissions. No Questionnaire submissions to display for this Project.')
		urlPrefix = request.get_host()+settings.WSGI_URL_PREFIX
		return render(request, 'InfoScreenExit.html', { 'errMsg': errMsg, 'wsgiPrefix':urlPrefix})
	# make a table of submissions
	[submitTable, submitTableCols] = makeSubmissionListForDisplay(allSubmissions,
		firstColLabel='Delete', firstColPrefix='D_')
	
	deleteSelected = False # initialize whether a submission has been selected

	if request.method == 'POST':
		DebugOut('after POST')
		DebugOut('POST: %s' %str(request.POST))
		if 'deleteSelected' in request.POST:
			DebugOut('deleteSelected button hit')
			respSelectionText = request.POST['deleteSelected']
			DebugOut('respSelectionText: %s' %respSelectionText)
			responseIndex = int(respSelectionText[2:])-1 # requires detailed format knowledge!!! 'D_'+int
			theSubmission = allSubmissions[responseIndex]
			DebugOut('theSubmission: %s' %str(theSubmission))
			# delete theSubmission
			# make a table of submissions - again
			theSubmission.delete()
			errMsg.append('Selection deleted.')
			if selectAllSubmissions:
				allSubmissions = Submission.objects.all()
			else:
				allSubmissions = getSubmissionsForProject(theProject)
			if len(allSubmissions) == 0:
				errMsg.append('Zero submissions. No Questionnaire submissions to display for this Project.')
				urlPrefix = request.get_host()+settings.WSGI_URL_PREFIX
				return render(request, 'InfoScreenExit.html', { 'errMsg': errMsg, 'wsgiPrefix':urlPrefix})
			[submitTable, submitTableCols] = makeSubmissionListForDisplay(allSubmissions,
				firstColLabel='Delete', firstColPrefix='D_')
		elif 'returnToHome' in request.POST:
			DebugOut('returnToHome button hit')
			redirectURL = registrationURL_base + 'userLanding/'
			DebugOut('responseViewer:  exiting to Home')
			return HttpResponseRedirect(redirectURL) # previous screen url
		else:
			DebugOut('Unknown button hit')
			pass
	else:
		DebugOut('NOT A POST')
		pass

	currentContext = {
		'theProject' : theProject,
		'submitTableCols' : submitTableCols,
		'submitTable' : submitTable,
		'back_to_intro' : 'Return to the Home Page',
		'url_base' : url_base,
		'errMsg' : errMsg,
		}
	DebugOut('responseViewer:  exiting')
	return render(request, 'working_pages/responseDelete.html', currentContext)

@login_required()
def responseViewer(request,forProject=None):
	"""
	# Select and view questionnaire responses.
	Limit scope to that of the Project
	"""
	DebugOut('responseViewer:  entering')
	errMsg = []
	theProject = getSessionProject(request)
	if not theProject: # not in session data
		# fall back to user default
		theUser = request.user
		theProject = getAssociatedProjectForUser(theUser)
	if not theProject:
		# Redirect if still no project
		redirectURL = registrationURL_base + 'selectProjectDefault/'
		DebugOut('No project, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)
	# Get the Questionnaires for this project.
	allSubmissions = getSubmissionsForProject(theProject)
	
#	allSubmissions = Submission.objects.all().order_by('questionnaireID__shortTag', '-lastUpdate')
	if len(allSubmissions) == 0:
		errMsg.append('Zero submissions. No Questionnaire submissions to display for this Project.')
		urlPrefix = request.get_host()+settings.WSGI_URL_PREFIX
		return render(request, 'InfoScreenExit.html', { 'errMsg': [errMsg], 'wsgiPrefix':urlPrefix})
	# make a table of submissions
	[submitTable, submitTableCols] = makeSubmissionListForDisplay(allSubmissions)

	submitSelected = False # initialize whether a submission has been selected
	if 'submitSelected' in request.session:
		DebugOut('submitSelected in request.session')
		responseIndex = request.session['submitSelected']
		theSubmission = allSubmissions[responseIndex]
		submitSelected = True
	
	if request.method == 'POST':
		DebugOut('after POST')
		if 'respSelection' in request.POST:
			respSelectionText = request.POST['respSelection']
			responseIndex = int(respSelectionText[2:])-1 # requires detailed format knowledge!!! 'R_'+int
			theSubmission = allSubmissions[responseIndex]
			DebugOut('theSubmission: %s' %str(theSubmission))
			request.session['submitSelected'] = responseIndex
			submitSelected = True
		elif 'dataItemSelection' in request.POST:
			DebugOut('dataItemSelection in request.POST')
			dataItemSelection = request.POST['dataItemSelection']
		elif 'returnToHome' in request.POST:
			DebugOut('returnToHome button hit')
			redirectURL = registrationURL_base + 'userLanding/'
			return HttpResponseRedirect(redirectURL) # previous screen url
	else:
		DebugOut('NOT A POST')
		pass

	# make a table of Questionnaire responses
	if submitSelected:
		DebugOut('submit Selected')
		# get the questionnaire object
		aquaireObj = theSubmission.questionnaireID
		# construct a table with field names and field values
		# Again add pt id and header information
		respObj = theSubmission.respondentID
		respName = respondentName( respObj )
		birthDay = str(respObj.birthDate)
		respondentDataCol = [
			theSubmission.lastUpdate,
			respName,
			birthDay,
			aquaireObj.barTitle,
			aquaireObj.version,
			aquaireObj.versionDate,
			theSubmission.reviewedBy,
			theSubmission.reviewDate,
			theSubmission.okForExport,
			]
		respondentQuestIDCol = [
			'Last updated',
			"Respondent's name",
			"Respondent's birthday",
			'Questionnaire name',
			'Questionnaire version',
			'Questionnaire version date',
			'Reviewed by',
			'Review date',
			'Ok for export?',
			 ]
		submissionResponseTable = []
		# put global flags and descriptions up front
		sessAnalysis = SubmissionAnalysis.objects.filter(
			submissionID = theSubmission)
		for aSessAnalysis in sessAnalysis:
			aGlobalFlag = aSessAnalysis.testResultFlag
			aGlobalFlagPriority = aSessAnalysis.testResultFlagPriority
			aGlobalFlagDescription = aSessAnalysis.testResultDescription
			submissionResponseTable.append([aGlobalFlag,"Priority: "+aGlobalFlagPriority,aGlobalFlagDescription,"Global Flag",""])

		DebugOut('before responseQuestions')
		# get all possible questions and question tags
		[pageList, fieldList, theList, tagToText ] = ListQuestionsForQuestionnaire(aquaireObj)
		# get all response questions for this submission
		responseQuestions = Response.objects.filter(submissionID = theSubmission)
		DebugOut('number of entries in responseQuestions loop %s'%len(responseQuestions))		
		for aResponse in responseQuestions:
			theQuestionObj = aResponse.questionID
			thePageTag = aResponse.questionOnPageID.shortTag
			theQuestionTag = theQuestionObj.questionTag
			theQuestionText = strip_tags( theQuestionObj.questionText)
			responseType = theQuestionObj.responseType
			allRespForQuestionObj = ResponseSelection.objects.filter(responseID=aResponse) # for multiple choices for a question
			DebugOut('theQuestionTag: %s' %theQuestionTag)
			DebugOut('number of entries in allRespForQuestionObj loop %s'%len(allRespForQuestionObj))
			responseList = []
			numResponses = len(allRespForQuestionObj) # number of responses for a single question
			if numResponses == 1: # keyword and keyvalue
				responseRaw = allRespForQuestionObj[0].responseText
				responseList.append(responseRaw)
			elif numResponses > 1: #  list of tags
				for aRespToQuestion in allRespForQuestionObj:
					responseRaw = aRespToQuestion.responseText
					DebugOut('responseRaw: %s' %responseRaw) # responseRaw is the responseChoice text
					# also append to a loop in case of multiple sub responses
					# translate tag to text
					responseList.append(responseRaw)
			else:
				DebugOut('No value for question tag %s, therefore "None"' %theQuestionTag)
				responseRaw = 'None'
				responseList.append(responseRaw)
			# convert from list to a string.
			if len(allRespForQuestionObj) == 0:
				responseText = 'None'
			else:
				responseText = ', '.join(responseList) # collect multiple responses for a question into a string
			DebugOut('Creating record for question tag %s' %theQuestionTag)
			DebugOut('responseText: %s' %responseText)
			submissionResponseTable.append([theQuestionTag,theQuestionText,responseText,responseType,thePageTag])

		submissionResponseTableCols = [
			'Question tag',
			'Question text',
			'Response text',
			'Response type',
			"On Page",
			]
		fieldNameCol = respondentQuestIDCol + submissionResponseTableCols
	else:
		submissionResponseTable = '' # false
		submissionResponseTableCols = ''
		respondentQuestIDCol = ''
		respondentDataCol = ''
		
			
	currentContext = {
		'submissionResponseTable' : submissionResponseTable,
		'theProject' : theProject,
		'submissionResponseTableCols' : submissionResponseTableCols,
		'respondentDataCol' : respondentDataCol,
		'respondentQuestIDCol' : respondentQuestIDCol,
		'submitTableCols' : submitTableCols,
		'submitTable' : submitTable,
		'back_to_intro' : 'Return to the Home Page',
		'url_base' : url_base,
		}
	DebugOut('responseViewer:  exiting')
	return render(request, 'working_pages/responseViewer.html', currentContext)
	
def savePtResponse(request):
	"""This function moves Session data to the database"""
# 	The respondent response is assumed to be in Session data
	DebugOut('savePtResponse: Enter')
	# must have the following data
	errmsg = []
	if respondentIDDict in request.session:
		respIDDict = request.session[respondentIDDict]
	else:
		# return to respondent id page
		errmsg.append('savePtResponse:  Pt data is missing.')
	
	if allResultsDict not in request.session:
		errmsg.append('savePtResponse:  no questionnaire results data.')

	# process respondent identity, insert into database "Respondent".
	if "lastName" in respIDDict:
		lastName = respIDDict['lastName'].title() # capitalize each word
		respIDDict['lastName'] = lastName # save capitalized form
	else: # if no respondent name, return to splash screen
		errmsg.append('savePtResponse:  Pt lastName is missing.')

	if "middleName" in respIDDict:
		middleName = respIDDict['middleName'].title() # capitalize each word
		respIDDict['middleName'] = middleName # save capitalized form
	else: # if no respondent name, return to splash screen
		pass # not required

	if "firstName" in respIDDict:
		firstName = respIDDict['firstName'].title() # capitalize each word
		respIDDict['firstName'] = firstName # save capitalized form
	else: # if no respondent name, return to splash screen
		errmsg.append('savePtResponse:  Pt firstName is missing.')	

	if "birthDate" in respIDDict:
		birthDate = respIDDict['birthDate']
	else: # if no respondent bd, return to splash screen
		errmsg.append('Debug:  Pt birthdate is missing.')
	current_date = timezone.now()
	DebugOut('Before calculate_ptAge_now( birthDate)')
# 	DebugOut('birthdate converted to string %s' %str(birthDate))
#	pt_currentAge = calculate_ptAge_now( birthDate)
#	pt_currentAge = calculate_ptAge_now( datetime.strptime(str(birthDate), '%Y-%m-%d'))
	pt_currentAge = ''
	DebugOut('After calculate_ptAge_now( birthDate)')
	
	# create a unique id
	ptUniqueID = uniquePTID(firstName, middleName, lastName, birthDate),
	if errmsg != []:
		DebugOut('syserrmsg:  exiting with message: %s'%errmsg)
		return render(request, 'system_error.html', { 'syserrmsg': errmsg})
		
	# create a record of the respondent, if it doesn't already exist
	try:
		therespondentID = Respondent.objects.get(
			ptUniqueID = ptUniqueID,
			)
		DebugOut("savePtResponse:  found respondent data")
	except Respondent.DoesNotExist:
		DebugOut("savePtResponse:  Respondent doesn't already exist, so create it.")
		therespondentID = Respondent.objects.create(
			lastName = lastName,
			middleName = middleName,
			firstName = firstName,
			birthDate = birthDate,
			ptUniqueID = ptUniqueID,
			)
	DebugOut('respIDDict: %s' %str(respIDDict))
	# update optional fields
	if 'contactPhone' in respIDDict:
		therespondentID.contactPhone = respIDDict['contactPhone']
		DebugOut("Saved contactPhone to respIDDict")

	if 'contactEmail' in respIDDict:
		therespondentID.contactEmail = respIDDict['contactEmail']

	if 'externalID' in respIDDict:
		therespondentID.externalID = respIDDict['externalID']

	if 'externalIDAuthority' in respIDDict:
		therespondentID.externalIDAuthority = respIDDict['externalIDAuthority']

	therespondentID.save()
	DebugOut("savePtResponse:  updated respondent data")

	# retrieve the current questionnaire object
	[theProject, quaire] = getSessionQuestionnaireProject(request)
	
	DebugOut('before creating a submission record')
	try:
		#create a submission record
		theSubmit = Submission(
			questionnaireID = quaire, # objects
			respondentID = therespondentID, # objects
			completedYN = True,
			okForExport = False, # not yet reviewed
			)
		theSubmit.save()
	except:
		DebugOut('error saving Submission object.')
		return render(request, 'system_error.html', { 'syserrmsg': errmsg})
	DebugOut('after creating a submission record')
	
	# Save analysis global flags, if any exist in this session
	if 'pageGlobalFlags' in request.session:
		allGlobalFlagsInSession = request.session['pageGlobalFlags']
		for aGlobalFlag in allGlobalFlagsInSession:
			# get further information about the flag from the PageAnalysis table
			testResultFlagInfo = PageAnalysis.objects.filter(
				testResultFlag = aGlobalFlag,
				)
			# select the first record since all descriptions and priorities should be the same for the same global flag!
			flagInfo = testResultFlagInfo[0]
			testResultFlagPriority = flagInfo.testResultFlagPriority
			testResultFlagDescription = flagInfo.testResultFlagDescription
			sessAnalysis = SubmissionAnalysis(
				submissionID = theSubmit,
				testResultFlag = aGlobalFlag,
				testResultFlagPriority = testResultFlagPriority,
				testResultDescription = testResultFlagDescription,
				)
			sessAnalysis.save()

	# Retrieve a list of questionnaire results from Session data
	sessionResultList = request.session[allResultsList]
	# request.session[allResultsList] structure: 
	#	[questionResponse, questionText,questionRecNum,responseChoiceRecNum,pageShortTag,pageRecNum, uniqueQuestionLabel, questionTag]
	for aline in sessionResultList: # save each line to the database
		DebugOut('aline: %s' %aline)
		qResponse = aline[0] # user response to the question
		questionRecNum = aline[2]
		responseChoiceRecNum = aline[3]
		aPageTag = aline[4]
		uniqueTagWithEncoding = aline[6]
		qQuestionTag = aline[7]
		pageObj = Page.objects.get(id=int(aline[5]))
		theQuestionObj = Question.objects.get(id=int(questionRecNum))
		qQuestionTag = theQuestionObj.questionTag
		if qResponse == '':
			pass
			DebugOut('syserrmsg: Error null value for question response %s' %qQuestionTag)
			
		aResp = Response.objects.create(
			questionID = theQuestionObj,
			questionOnPageID = pageObj,
			submissionID = theSubmit,
			)
		if type(qResponse) == list: # oops, sub values!
			for aSubResponse in qResponse: # save multiple responses
				DebugOut('savePtResponse: list response: %s'%aSubResponse)
				aRSObj = ResponseSelection.objects.create(
					responseID = aResp,
# 					responseChoiceID = 
					responseText = aSubResponse, # This is ResponseChoice.choiceTag
					)
		else: # a single response
			aRSObj = ResponseSelection.objects.create(
				responseID = aResp,
# 				responseChoiceID = 
				responseText = qResponse, # This is User response
				)
	DebugOut('savePtResponse: Exit')
	return errmsg

def savecsvDecoder(request):
	"""Dumps file decoding tags found in the csv-type file of all submissions.

	Args:
		argument_one: This is of some type a and does x.
		arg....:...

	Returns:
		http response 	

	Raises:
		none.
	"""
	DebugOut('savecsvDecoder: Enter')
	# Create the HttpResponse object with the appropriate plain text header.
	response = HttpResponse(content_type='text/plain')
	now = str(timezone.now())
	outdecodeFileName = "Questionnaire tag decoder %s.txt" %now[:26] # cut off time zone
	contentDispo = 'attachment; filename=' + '"' + outdecodeFileName + '"'
	response['Content-Disposition'] = contentDispo
 	
	# get all Submissions and corresponding questionnaires
	allSubmissions = Submission.objects.all().order_by('-lastUpdate')
	theQIDs = []
	for aSubmission in allSubmissions:
		theQIDs.append(aSubmission.questionnaireID.id)
	# make a queryset of all questionnaires referenced by the submissions
	allQObjs = retrieveBulk( Questionnaire, theQIDs )
	
	for aQ in allQObjs: # for each questionnaire
		response.write('**********Questionnaire_separator'+os.linesep)
		# Questionnaire identification
		response.write('**********Questionnaire_identification'+os.linesep)
		response.write('Questionnaire short name: %s%s' %(aQ.shortTag,os.linesep))
		response.write('Questionnaire description: %s%s' %(aQ.description,os.linesep))
		response.write('Questionnaire version: %s%s' %(aQ.version,os.linesep))
		response.write('Questionnaire version date: %s%s' %(aQ.versionDate,os.linesep))
		response.write('Questionnaire last update: %s%s' %(aQ.lastUpdate,os.linesep))
		response.write('Questionnaire primary key: %s%s' %(aQ.id,os.linesep))
		# Project identification
		response.write('**********Project_identification'+os.linesep)
		theProject = getProjectObjForQuestionnaire(aQ)
		if theProject: # exists
			response.write('Project short name: %s%s' %(theProject.shortTag,os.linesep))
			response.write('Project name: %s%s' %(theProject.name,os.linesep))
			response.write('Project last update: %s%s' %(theProject.lastUpdate,os.linesep))
			response.write('Project primary key: %s%s' %(theProject.id,os.linesep))
		else:
			response.write('Project short name: %s%s' %('(None)',os.linesep))
			response.write('Project name: %s%s' %('(None)',os.linesep))
			response.write('Project last update: %s%s' %('(None)',os.linesep))
			response.write('Project primary key: %s%s' %('(None)',os.linesep))
		response.write('*********Field_decoding'+os.linesep)
		response.write('**********Field count : Field tag : Field text'+os.linesep)
		[pageList, fieldList, theList, tagToText ] = ListQuestionsForQuestionnaire(aQ)
		# decode all the fields
		fieldCount = 1
		for aField in fieldList:
			response.write(fieldCount) # field count
			fieldCount+=1
			[questionRecNum,responseChoiceRecNum] = decodeQuestionResponseLabel(aField)
			if questionRecNum: # use question tag
				qRec = int(questionRecNum)
				aFieldName = Question.objects.get(id=qRec).questionTag
			if responseChoiceRecNum: # use ResponseChoice tag. Overrides the question tag
				rcRec = int(responseChoiceRecNum)
				aFieldName = ResponseChoice.objects.get(id=rcRec).choiceTag
			response.write(' : ')
			response.write(strip_tags(aFieldName)) # field tag
			response.write(' : ')
			try:
				textValue = strip_tags(tagToText[aField]).replace("\r"," ").replace("\n"," ")
			except KeyError:
				textValue = 'Text not found'
				DebugOut('Text not found for tag: %s' %aField)
			response.write(textValue)
			response.write(os.linesep)			
			
	DebugOut('savecsvDecoder: exit')
	return response
	
def savepdf(request):
	"""Dumps a pdf-type file of all pages in the default questinnaire.
	Args:
		http request

	Returns:
		http response 	

	Raises:
		none.
	"""
	DebugOut('savepdf: Enter')
	# Create the HttpResponse object with the appropriate PDF header.
	response = HttpResponse(content_type='application/pdf')
	now = str(timezone.now())
	outpdfFileName = "Questionnaire Pages %s.pdf" %now[:16] # cut off time zone & seconds fraction
	contentDispo = 'attachment; filename=' + '"' + outpdfFileName + '"'
	response['Content-Disposition'] = contentDispo
	# Create the PDF object, using the response object as its "file."
	pdfObj = canvas.Canvas(response)
	# Draw things on the PDF. Here's where the PDF generation happens.
	# See the ReportLab documentation for the full list of functionality.
	pdfObj.drawString(100, 500, "Hello world.")
	# Close the PDF object cleanly, and we're done.
	pdfObj.showPage()
	pdfObj.save()
	DebugOut('savepdf: Exit')
	return response
	
@login_required()
def dumpSubmissionDataForProject(request):
	"""Dumps a csv-type file for all submissions pointing to questionnaires in a project.
	"""
	theProject = getSessionProject(request)
	if not theProject:
		# fall back to user default
		theUser = request.user
		theProject = getAssociatedProjectForUser(theUser)
	if not theProject:
		# Redirect if still no project
		redirectURL = registrationURL_base + 'selectProjectDefault/'
		DebugOut('No project, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)
	# output csv
	DebugOut('Output csv file for Proejct %s'%theProject.shortTag)
	result = savecsv(request, forProject=theProject)
	return result

def toCSV(aListOfStrings):
	# Simple as possible.
	commaString = ','.join(aListOfStrings)
	commaString = commaString+'/n'
	return commaString
	
def savecsv(request, forProject=None):
	"""Dumps a csv-type file of all submissions.

	This is a one line or more descriptive summary.
	Blah Blah Blah.

	Args:
		argument_one: This is of some type a and does x.
		arg....:...

	Returns:
		http response 	

	Raises:
		none.
	"""
	DebugOut('savecsv: Enter')
	errMsg = []
	# Create the HttpResponse object with the appropriate CSV header.
	response = HttpResponse(content_type='text/csv')
	now = str(timezone.now())
	outcsvFileName = "Questionnaire Responses %s.csv" %now[:16] # cut off time zone & seconds fraction
	contentDispo = 'attachment; filename=' + '"' + outcsvFileName + '"'
	response['Content-Disposition'] = contentDispo
	
	# dump the header text for respondent ID
	writer = csv.writer(response)
	
	# check if there are Submissions
	iCountSubmissions = Submission.objects.all().count()
	DebugOut('iCountSubmissions %s'%iCountSubmissions)
	if iCountSubmissions == 0:
		errMsg = 'Zero submissions available. No export submissions file created.'
		DebugOut(errMsg)
		return render(request, 'system_error.html', { 'syserrmsg': [errMsg]})
	# get all global flags
	allGFlagRecs = SubmissionAnalysis.objects.all()
	for aRec in allGFlagRecs:
		DebugOut('aRec %s' %str(aRec))
	# Make a list of unique flags. May be null
	globalFlagNames = list(set([aFlagRec.testResultFlag for aFlagRec in allGFlagRecs]))
	globalFlagNames.sort()
	DebugOut('globalFlagNames %s' %globalFlagNames)
	
	# Find if the scope is to a project. Get the questionnaires
	if forProject:
		theProject = forProject
		projectTag = theProject.shortTag
		allProjectsRaw = Project.objects.filter(shortTag=projectTag).order_by('-lastUpdate') # get "inactive" projects as well
	else:
		allProjectsRaw = Project.objects.all().order_by('-lastUpdate') # get "inactive" projects as well
	# remove Projects that have the wrong attribute
	allIDs = [] # collect the record numbers into a list
	for aProject in allProjectsRaw:
		# get the corresponding Attributes
		aProjectAttributes = getProjectAttributes(aProject)
		if 'Display' in aProjectAttributes:
			allIDs.append(aProject.id)
		elif 'DoNotDisplay' not in aProjectAttributes:
			allIDs.append(aProject.id)
	allProjects = retrieveBulk( Project, allIDs )
	
	# get all questionnaires for all projects
	allQuestionnaireids = []
	for aProject in allProjects:
		pqObjs = ProjectQuestionnaire.objects.filter(projectID=aProject)
		questRecList = [pqObj.questionnaireID.id for pqObj in pqObjs]
		allQuestionnaireids.extend(questRecList)
	uniqueQuestRecList = list(set(questRecList)) # make unique. Might be sharing!
	allQuestionnaires = retrieveBulk( Questionnaire, uniqueQuestRecList ).order_by('-lastUpdate','shortTag') 
	if len(allQuestionnaires) == 0:
		if forProject:
			allerrMsg = ['No Questionnaires available for this project: %s.'%theProject.shortTag]
		else:
			allerrMsg = ['No Questionnaires available']
		allerrMsg.append('No export submissions file created.')
		DebugOut(allerrMsg)
		urlPrefix = request.get_host()+settings.WSGI_URL_PREFIX
		return render(request, 'InfoScreenExit.html', { 'errMsg': allerrMsg, 'wsgiPrefix':urlPrefix})
	
	# Loop through Questionnaires, Pages, Questions, ResponseChoices in a standard way
	icountExports = 0 # count the exported submissions
	for aQuestionnaire in allQuestionnaires:
		DebugOut('Top of Questionnaire loop')
		submissionsForQuestionnaire = Submission.objects.filter(questionnaireID=aQuestionnaire)
		# A requirement is to maintain the same order for the same questionnaire, for each Submission
		# Start with getting the pages in canonical order
		allPages = allPagesInDefaultOrder(aQuestionnaire)
		DebugOut( 'Pages in Questionnaire "%s":  "%s"'%(aQuestionnaire.shortTag,len(allPages)))
		DebugOut( 'Number of Submissions "%s" in Questionnaire "%s"'%(submissionsForQuestionnaire.count(),aQuestionnaire.shortTag))
		oldHeaderCopy = [] # save the old header here
		DebugOut('Submissions loop')
		for aSubmission in submissionsForQuestionnaire:
			DebugOut('Top of submissions loop')
			aRow = [] # add respondent ID, questionnaire ID, question responses
			colm_headers = [] # save the new header here
			icountExports+=1
			# Dump the Submission record
			aRow.append(aSubmission.lastUpdate)
			colm_headers.append('lastUpdate')
			aRow.append(aSubmission.reviewedBy)
			colm_headers.append('reviewedBy')
			aRow.append(aSubmission.reviewDate)
			colm_headers.append('reviewDate')
			aRow.append(aSubmission.okForExport)
			colm_headers.append('okForExport')
			# dump questionnaire data
			# dump Respondent data
			responderObj = aSubmission.respondentID
			DebugOut('Unique patient id: %s' %responderObj.ptUniqueID)
			# Respondent fields
			respFields = ['lastName', 'middleName', 'firstName', 'birthDate', 'contactPhone', 'contactEmail', 'externalID', 'externalIDAuthority']
			for respField in respFields: # process respondent identifiction
				try:
					theItem = unicode(getattr(responderObj, respField)).encode('utf-8')
					aRow.append(theItem)
					#DebugOut('respField field: %s value: %s' %(respField,theItem))
					colm_headers.append(respField)
				except AttributeError:
					DebugOut('syserrmsg: respField field: %s not found in database.' %(respField))
				except:
					DebugOut('syserrmsg: respField field: %s error in db retrieval' %(respField))
			# process questionnaire name and version
			aquaireObj = aSubmission.questionnaireID
			# Project shortTag
			projectShortTag = getProjectObjForQuestionnaire(aquaireObj).shortTag
			aRow.append(projectShortTag)
			colm_headers.append('Project')
			# Questionnaire fields ************************** BEGIN
			aRow.append(aquaireObj.shortTag)
			colm_headers.append('Questionnaire')
			aRow.append(aquaireObj.version)
			colm_headers.append('version')
			aRow.append(aquaireObj.versionDate)
			colm_headers.append('versionDate')
			aRow.append(aquaireObj.language)
			colm_headers.append('language')
			# Questionnaire fields ************************** END
			# retrieve any global flags for this submission *** BEGIN
			# sort the flags so that the order is the same for different submissions
			theFlagInfo = SubmissionAnalysis.objects.order_by(
				'testResultFlag','testResultFlagPriority').filter(
				submissionID = aSubmission,
				)
			allFlagsThisSubmit = [aGlobalFlag.testResultFlag for aGlobalFlag in theFlagInfo]
			DebugOut('allFlagsThisSubmit: %s' %allFlagsThisSubmit)
			for aFlag in globalFlagNames:
				colm_headers.append(aFlag)
				if aFlag in allFlagsThisSubmit:
					aRow.append("Yes")
				else:
					aRow.append("No")
			# retrieve any global flags for this submission *** END
			
			# retrieve all Response objects belonging to this Submission
			allResponses = Response.objects.filter(submissionID=aSubmission)
			DebugOut('Response count: %s'%allResponses.count())
			fieldCount = 1
			for aPage in allPages:
				DebugOut('top of Page loop: %s'%aPage.shortTag)
				allQuestionsOnPage = getPageQuestions( aPage)
				for aQuestion in allQuestionsOnPage:
					DebugOut('top of Question loop')
					questionid = aQuestion.id
					# Select the response (if any)
					questionTag = aQuestion.questionTag
					DebugOut('Question tag: %s'%questionTag)
					responsesPerQuestion = allResponses.filter(questionID=aQuestion) # select only one if multiple.
						# "responsesPerQuestion" a Response queryset
					DebugOut('Number of responses for this question: %s'%responsesPerQuestion.count())
					if responsesPerQuestion:
						if responsesPerQuestion.count() >1: # more than one response to a question. Choose one.
							# Question appears more than once in a Questionnaire
							# Note the error condition
							DebugOut('syserrmsg:  Question "%s" appears more than once in "%s"'%(questionTag,aQuestionnaire.shortTag))
							DebugOut('syserrmsg:  Arbitrarily select one question for output into the csv')
						theResponse = responsesPerQuestion[0] # choose arbitrarily
						responseSelections = ResponseSelection.objects.filter(responseID=theResponse) # Question asked
						responseValues = [rpq.responseText for rpq in responseSelections] # Gather all responses
						DebugOut('responseValues: %s'%responseValues)
					elif responsesPerQuestion.count() == 0: # No response, but add header info at top of column
						# provide for strange case of Question asked, but no responses
						responseValues = []
						DebugOut('No response to Question %s'%questionTag)
# 						aRow.append('')
# 						colm_headers.append(questionTag+'_'+str(fieldCount)) # choice text is the tag
# 						fieldCount+=1
# 						break # go to next question
					# now consult the Questionnaire design for a list of all responses
					responseChoices = ResponseChoice.objects.order_by('choiceSequence').filter(questionID=aQuestion) # may be none
					allResponsechoices = [arc.choiceText for arc in responseChoices]
					
					# responseValues is from the User, allResponsechoices is from the Questionnaire design
					DebugOut('responseValues "%s", allResponsechoices "%s"'%(responseValues,allResponsechoices))
					if len(responseValues) > 1 and len(allResponsechoices) == 0:
						DebugOut('syserrmsg:  multiple choices for a non-muliple choice question!! Question: "%s"'%questionTag)
					elif len(responseValues) > len(allResponsechoices) > 0:
						DebugOut('syserrmsg:  more responses than choices!!')
					
					if len(allResponsechoices) > 0 and len(responseValues) > 0:
						theValue = 'Multiple Choice Question' # a list
					elif len(allResponsechoices) > 0 and len(responseValues) == 0:
						theValue = 'No Choice Selected' # a list
					elif len(responseValues) == 1:
						# one value
						theValue = smart_str(responseValues[0])
					else:
						DebugOut('Question result: '+questionTag+'_'+str(fieldCount)+' Null result')
						theValue = ''
					DebugOut('Question result: '+questionTag+'_'+str(fieldCount)+'   The Value: ' +str(theValue))
					aRow.append(theValue)
					colm_headers.append(questionTag+'_'+str(fieldCount)) # choice text is the tag
					fieldCount+=1

					if responseChoices: # examine a list of all possible responses per question
						# Question is multiple choice
						# top of a list. Name of a list. Values are placed in the following loop
						# multiple choice per record. Perhaps none selected.
						for aResponseChoice in responseChoices:
							DebugOut('top of ResponseChoice per Question loop')
							# create the unique record which might be a response, if there is any response.
							choiceText = aResponseChoice.choiceText
							choiceTag = aResponseChoice.choiceTag
							DebugOut('choiceText: "%s", choiceTag: "%s"'%(choiceText, choiceTag))
# 							DebugOut('choiceText: "%s", responseValues: "%s"'%(choiceText, responseValues))
# 							DebugOut('choiceText type: "%s", responseValues type: "%s"'%(type(choiceText), type(responseValues)))
# 							if len(responseValues) >0:
# 								DebugOut('element type: "%s"'%type(responseValues[0]))
							if choiceText in responseValues: # check for this response
								aRow.append(choiceText)
								colm_headers.append(choiceTag+'_'+str(fieldCount)) # choice text is the tag
								DebugOut('choiceText: "%s" added to row string.'%(choiceText))
							else:
								aRow.append('')
								DebugOut('choiceText: "%s" NOT added to row string.'%(choiceText))
								colm_headers.append(choiceTag+'_'+str(fieldCount)) # choice text is the tag
							fieldCount+=1
			DebugOut('End of responses')			
			DebugOut('Row %s' %aRow)
			if oldHeaderCopy != colm_headers:
				writer.writerow(colm_headers)
				oldHeaderCopy = list(colm_headers) # Save the new header if different
			colm_headers = list([]) # annihilate the current list			
			writer.writerow(aRow) # append the submission to the csv file
			DebugOut('After writing a row')
	if icountExports == 0:
		if forProject:
			allerrMsg = ['No Submissions available for this project: %s.'%theProject.shortTag]
		else:
			allerrMsg = ['No Submissions available']
		allerrMsg.append('No export submissions file created.')
		DebugOut(allerrMsg)
		urlPrefix = request.get_host()+settings.WSGI_URL_PREFIX
		return render(request, 'InfoScreenExit.html', { 'errMsg': allerrMsg, 'wsgiPrefix':urlPrefix})
	DebugOut('savecsv: Exit')
	return response

def displayAndEditQuestion(request):
	# select a question to add to the page.

	# find all existing question shortTag's
	try:
		allQuestions=Question.objects.all().order_by('questionTag')
	except:
		return render(request, 'system_error.html', {'syserrmsg': ['Debug:  Question data is missing.']})	
	allQuestionTags = [allQuestions.questionTag for allQuestions in allQuestions] # list comprehension
	
	# select a default question tag to start.
	if 'currentQuestionTag' in request.session: # first look in sessions data
		currentQuestionTag = request.session['currentQuestionTag']
	else: # if not in sessions data, then use last tag
		currentQuestionTag = allQuestionTags[-1]
		request.session['currentQuestionTag'] = currentQuestionTag

	try: # try to retrieve the question
		theQuestion=Question.objects.get(questionTag=currentQuestionTag)
	except Question.DoesNotExist: # done everything, so bail
		return render(request, 'system_error.html', {'syserrmsg': ['Debug:  Most recent question data is missing.']})	

	pageBaseURL = settings.WSGI_URL_PREFIX + 'multiquest/' 

	oldQuestionTag = currentQuestionTag # check for a change on the other side of this if statement
	if request.method == 'POST':
		theForm = QuestionForm( request.POST)
		if 'submitButton' in request.POST:
			if request.POST['submitButton'] == 'Discard Question Edits': # Return to previous page
				return HttpResponseRedirect(pageBaseURL+'intro/') # previous screen url
		if theForm.is_valid():
			currentQuestionTag = theForm.cleaned_data['questionTag'] # may be overridden by text box
			if 'questionTag' in request.POST:
				currentQuestionTag = request.POST['questionTag']
				request.session['currentQuestionTag'] = currentQuestionTag
				
			if 'submitButton' in request.POST:
				if request.POST['submitButton'] == 'Save Question Edits':
					theQuestion.questionTag = currentQuestionTag
					theQuestion.questionText = theForm.cleaned_data['questionText']
					theQuestion.description = theForm.cleaned_data['description']
					theQuestion.responseType = theForm.cleaned_data['responseType']
					theQuestion.lastUpdate = timezone.now()
					theQuestion.save()
					responseMsg = 'Question "%s" edited and saved.' %currentQuestionTag
					request.session['currentQuestionTag'] = currentQuestionTag
				elif request.POST['submitButton'] == 'Delete Current Question': # Return to previous page
					Question.objects.filter(shortTag=currentQuestionTag).delete()
				return HttpResponseRedirect(pageBaseURL+'intro/') # previous screen url
	else:
		initialValues ={'questionTag' : currentQuestionTag,
			'questionText' : theQuestion.questionText,
			'description' : theQuestion.description,
			'responseType' : theQuestion.responseType,
			'lastUpdate' : theQuestion.lastUpdate,
			}
		theForm = QuestionForm(initial=initialValues)
	if currentQuestionTag != oldQuestionTag:
		try: # try to retrieve the question
			theQuestion=Question.objects.get(questionTag=currentQuestionTag)
		except Question.DoesNotExist: # done everything, so bail
			return render(request, 'system_error.html', {'syserrmsg': ['Debug:  Most recent question data is missing.']})	
		
				
	currentContext = { 'theForm' : theForm,
		'questionTag' : currentQuestionTag,
		'allQuestionTags' : allQuestionTags,
		'lastUpdate' : theQuestion.lastUpdate,
		'back_to_intro' : 'Return to the Introduction Page',
		'url_base' : url_base,
		}
	return render(request, 'working_pages/displayAndEditQuestion.html', currentContext)

def createPageQuestionLink(request):
	DebugOut( 'createPageQuestionLink: Enter.')
	# Create a link from a page to one or more questions.
	
	# find all existing page shortTag's
	try:
		allP=Page.objects.all()
	except:
		return render(request, 'system_error.html', {'syserrmsg': ['Debug:  Page data is missing.']})
	allPageTags = [aPage.shortTag for aPage in allP]

	pageBaseURL = settings.WSGI_URL_PREFIX + 'multiquest/' 
	
	# find all existing question shortTag's
	try:
		allQuestions=Question.objects.all()
	except:
		return render(request, 'system_error.html', {'syserrmsg': ['Debug:  Question data is missing.']})	
	allQuestionTags = [aQuestion.questionTag for aQuestion in allQuestions]

	# Find all existing Page/Question links
	pqLinks = PageQuestion.objects.all()
	pqList = []
	for pq in pqLinks:
		pqList.append([ pq.pageID.shortTag, pq.questionID.questionTag, pq.questionID.questionText ])
	
	# select a default page tag to start.
	if 'currentPageTag' in request.session: # first look in sessions data
		currentPageTag = request.session['currentPageTag']
	else: # if not in sessions data, then use last tag
		currentPageTag = allPageTags[-1]
		request.session['currentPageTag'] = currentPageTag

	if 'currentQuestionTag' in request.session: # first look in sessions data
		currentQuestionTag = request.session['currentQuestionTag']
	else: # if not in sessions data, then use last tag
		currentQuestionTag = allQuestionTags[-1]
		request.session['currentQuestionTag'] = currentQuestionTag

	try: # try to retrieve the page
		thePage=Page.objects.get(shortTag=currentPageTag)
	except Page.DoesNotExist: # so set to a legal value
		theMess = 'System error: Page data is missing for tag: %s. Select a different page.' %currentPageTag
		DebugOut(theMess)
		errmsg.append(theMess)

	try: # try to retrieve the question
		theQuestion=Question.objects.get(questionTag=currentQuestionTag)
	except Question.DoesNotExist: # done everything, so bail
		theMess = 'System error: Question data is missing for tag: %s. Select a different question.' %currentQuestionTag
		DebugOut(theMess)
		errmsg.append(theMess)

	errmsg = []
	newPage = False
	newQuestion = False
	if request.method == 'POST':
		theForm = PageQuestionLinkForm( request.POST)
		if 'pageSelection' in request.POST:
			currentPageTag = request.POST['pageSelection']
			request.session['currentPageTag'] = currentPageTag
			newPage = True
		elif 'submitButton' in request.POST:
			if request.POST['submitButton'] == 'Return to Introduction': # Return to Intro
				DebugOut( 'button: Return to introduction.') # Save the cleaned data
				return HttpResponseRedirect(settings.WSGI_URL_PREFIX + 'multiquest/'+'intro/') # previous screen url
			elif request.POST['submitButton'] == 'Save Question to Page': # Attach question to page
				DebugOut( 'button: Save Question to Page.') # Save the cleaned data
				if theForm.is_valid(): # have valid data from page
					DebugOut( 'Form is valid. Saving data.') # Save the cleaned data
					qs = theForm.cleaned_data # save only this page data for redisplay of the page
					DebugOut('thePage: %s' %str(thePage))
					DebugOut('theQuestion: %s' %str(theQuestion))
					try:
						pageQuest = PageQuestion(pageID=thePage, questionID=theQuestion, questionSequence=qs)
						pageQuest.save()
					except:
						errmsg.append('Select a page and question to be added to the page.')
				else:
					DebugOut( 'Form is not valid. Not saving data.') # Save the cleaned data
		elif 'questionSelection' in request.POST:
			currentQuestionTag = request.POST['questionSelection']
			request.session['currentQuestionTag'] = currentQuestionTag
			DebugOut('The new current question is: %s' %currentQuestionTag)
			newQuestion = True
	else: # not a POST
		theForm = PageQuestionLinkForm()

	if newPage:
		try: # try to retrieve the page
			thePage=Page.objects.get(shortTag=currentPageTag)
		except Page.DoesNotExist: # so set to a legal value
			theMess = 'System error: Page data is missing for tag: %s. Select a different page.' %currentPageTag
			DebugOut(theMess)
			errmsg.append(theMess)
	if newQuestion:	
		try: # try to retrieve the question
			theQuestion=Question.objects.get(questionTag=currentQuestionTag)
		except Question.DoesNotExist: # done everything, so bail
			theMess = 'System error: Question data is missing for tag: %s. Select a different question.' %currentQuestionTag
			DebugOut(theMess)
			errmsg.append(theMess)

	try:
		thePageQuestionLinks=PageQuestion.objects.filter(pageID=thePage)
		# Extract all questions for thePage
		questionsForThisPage = [aQuestion.questionID.questionText for aQuestion in thePageQuestionLinks]
	except PageQuestion.DoesNotExist:
		theMess = 'page/question link not found for page "%s"' %thePage
		DebugOut(theMess)
		questionsForThisPage = []
	except:
		theMess = 'Error: page/question link not found for page "%s"' %thePage
		DebugOut(theMess)
		questionsForThisPage = []

	DebugOut('errmsg: %s' %str(errmsg))
	DebugOut( 'createPageQuestionLink: Exit.')

	currentContext = { 'theForm' : theForm,
		'errmsg' : errmsg,
		'pqList' : pqList,
		'currentPageTag' : currentPageTag,
		'currentQuestionTag' : currentQuestionTag,
		'allQuestionTags' : allQuestionTags,
		'allPageTags' : allPageTags,
		'questionsForThisPage' : questionsForThisPage,
		'back_to_intro' : 'Return to the Introduction Page',
		'url_base' : url_base,
		}
		
	return render(request, 'working_pages/createPageQuestionLink.html', currentContext)

def setPageToPageTransitionGlobalFlags(request):
	# determine page transition depending upon the existence of a global flag
	DebugOut('setPageToPageTransitionGlobalFlags:  entering')

	# select a default Questionnaire and Project tag to start.
	[workingProject, workingQuestionnaire] = getSessionQuestionnaireProject(request)
	if not workingQuestionnaire:
		errMsg = ['The questionnaire has not been selected']
		return render(request, 'system_error.html', { 'syserrmsg': errMsg})

	# Retrieve the Questionnaire Tag
	workingQuestionnaireTag=workingQuestionnaire.shortTag
	
	# Retrieve the Project tag
	workingProjectTag=workingProject.shortTag # notice the entire object is stored!

	# find all existing page shortTag's for this questionnaire
	allPageObjs = getAllPageObjsForQuestionnaire(workingQuestionnaire)
	allPageTags = getAllPageTags(workingQuestionnaire)
	DebugOut('allPageTags: %s' %allPageTags)
	
	# select a default page tag to start. This is the 'from' page.
	currentPageSessionTag = 'currentPageTag_admin'
	[workingPageTag, theWorkingPage] = selectCurrentPage(request, currentPageSessionTag, allPageObjs)
	
	errMsgs = []
	
	# got all starting data
	DebugOut('Default values:')
	DebugOut('workingQuestionnaireTag: %s' %workingQuestionnaireTag)
	DebugOut('workingPageTag: %s' %workingPageTag)
		
	pageBaseURL = settings.WSGI_URL_PREFIX + 'multiquest/' + workingProjectTag+'/'+workingQuestionnaireTag+'/'
	#request.session['pageBaseURL'] = pageBaseURL # not sure if this is needed

	if 'globalFlagSelect' in request.session:
		globalFlagSelect = request.session['globalFlagSelect']
	else:
		globalFlagSelect = ''

	if 'nextPageGlobalFlag' in request.session:
		nextPageGlobalFlag = request.session['nextPageGlobalFlag']
	else:
		nextPageGlobalFlag = ''
	
	flagAndConditionMsg = '' # msg to user "Global flag is, and test condition is"
	
	nextPAndConditionMsg = '' # message that the test condition was saved to the database
	needMsg = ''
	if request.method == 'POST':
		DebugOut('setPageToPageTransitionGlobalFlags:  After POST')
		DebugOut('request.POST %s' %str(request.POST))
		if 'submitButton' in request.POST:
			DebugOut('Submit button hit')
			if request.POST['submitButton'] == 'Return to the administration page': # Return to previous page
				return HttpResponseRedirect(settings.WSGI_URL_PREFIX + 'multiquest/'+'intro/') # previous screen url
			else: # clicked on a page button - change working page
				workingPageTag = request.POST['submitButton']
				try:
					theWorkingPage=Page.objects.get(shortTag=workingPageTag)
					DebugOut('The new working page: %s' %workingPageTag)
				except Page.DoesNotExist:
					return render(request, 'system_error.html', {'syserrmsg': ['Debug:  Page does not exist: %s' %workingPageTag]})
				request.session[currentPageSessionTag] = theWorkingPage.id
		elif 'globalFlagSelectButton' in request.POST: # select a global flag
			globalFlagSelect = request.POST['globalFlagSelectButton']
			request.session['globalFlagSelect'] = globalFlagSelect
			DebugOut('The new global flag selected: %s' %globalFlagSelect)
		elif 'nextPageGlobalFlagButton' in request.POST:
			# select a NEXT page if the global flag exists at runtime
			nextPageGlobalFlag = request.POST['nextPageGlobalFlagButton']
			request.session['nextPageGlobalFlag'] = nextPageGlobalFlag
			DebugOut('The new global flag "next page" selection: %s' %nextPageGlobalFlag)
		elif 'deleteSelection' in request.POST: # delete the selected record
			# delete the selected line from the condition table
			lineSelect = int(request.POST['deleteSelection']) - 1 # line selected
			[transitionGlobalFlags, success] = getGlobalFlagTransitions(workingQuestionnaire)
			# record structure is:
				# record number, global flag name, next page short tag, global flag priority
			recSelect = transitionGlobalFlags[lineSelect][0]
			deleteTestConditonFromQuestionnairePage(recSelect)
		elif 'saveToDBButton' in request.POST:
			if globalFlagSelect and nextPageGlobalFlag:
				recordType = 'globalFlag'
				saveTestConditonToQuestionnairePage(globalFlagSelect,
					nextPageGlobalFlag, theWorkingPage, workingQuestionnaire, recordType)
				flagAndConditionMsg = 'The global flag "%s" and the next page "%s" were saved' %(globalFlagSelect, nextPageGlobalFlag)
			needMsg = []
			if not globalFlagSelect:
				needMsg.append('Please select a global flag')
			if not nextPageGlobalFlag:
				needMsg.append('Please select a "next page" transition when the global flag, "%s" is present.' %globalFlagSelect)
	else: # a 'GET'
		# obtain any prior setting for 'next page'
		DebugOut('"GET" posted - restore data if any')
	
	# Retrieve all global flags
	allGlobalFlags = listAllGlobalFlags(workingQuestionnaire)
	
	DebugOut('allGlobalFlags: %s' %allGlobalFlags)

	if 'nextPageGlobalFlag' in request.session:
		nextPageGlobalFlag = request.session['nextPageGlobalFlag']
	else:
		nextPageGlobalFlag = ''
		
#	pgNext = retrieveDefaultNextPage(workingQuestionnaireTag, workingPageTag) # delete this line after confimation
	pageToPageRecs = getPageToPageObjs(workingQuestionnaire)
	pgNext = (pageToPageRecs[theWorkingPage]).shortTag
	
	# test retrieve
	barTitle=workingQuestionnaire.barTitle
	DebugOut('barTitle: %s' %barTitle)
	
	if allGlobalFlags == ['']:
		globalFlagExist = False
	else:
		globalFlagExist = True
	
	[transitionGlobalFlags, success] = getGlobalFlagTransitions(workingQuestionnaire)
	if not success:
		DebugOut('Unsuccessful retrieval of global flag info.')
		transitionGlobalFlags = ''
	
	DebugOut('globalFlagSelect: %s' %globalFlagSelect)

	DebugOut('allGlobalFlags: %s' %allGlobalFlags)
	DebugOut('globalFlagSelect: %s' %globalFlagSelect)
	DebugOut('nextPageGlobalFlag: %s' %nextPageGlobalFlag)
	DebugOut('globalFlagExist: %s' %globalFlagExist)
	
	currentContext = { 
		'workingPageTag' : workingPageTag,
		'pgNext' : pgNext,
		'allPageTags' : allPageTags,
		'globalFlagExist' : globalFlagExist,
		'allGlobalFlags' : allGlobalFlags,
		'globalFlagSelect' : globalFlagSelect,
		'nextPageGlobalFlag' : nextPageGlobalFlag,
		'transitionGlobalFlags' : transitionGlobalFlags,
		'nextPAndConditionMsg' : nextPAndConditionMsg,
		'flagAndConditionMsg' : flagAndConditionMsg,
		'barTitle' : barTitle,
		'errMsgs' : errMsgs,
		'needMsg' : needMsg,
		'workingQuestionnaireTag' : workingQuestionnaireTag,
		}
	DebugOut('setPageToPageTransitionGlobalFlags:  exiting')
	return render(request, 'working_pages/setPageToPageTransitionGlobalFlags.html', currentContext)

def setGlobalFlags(request):
	# Set global flags based upon response to questions.
	DebugOut('setGlobalFlags:  entering')
	
	# select a default Questionnaire and Project tag to start.
	[workingProject, workingQuestionnaire] = getSessionQuestionnaireProject(request)
	if not workingQuestionnaire:
		errMsg = ['The questionnaire has not been selected']
		return render(request, 'system_error.html', { 'syserrmsg': errMsg})
	# refresh

	# Retrieve the Questionnaire Tag
	workingQuestionnaireTag=workingQuestionnaire.shortTag
	barTitle=workingQuestionnaire.barTitle
	
	# find all existing pages with questions for this questionnaire
	allPageObjs = findAllPageObjWQuestions(workingQuestionnaire)
	allPageTags = [anObj.shortTag for anObj in allPageObjs]
	
	if not allPageTags: # no tags
		return render(request, 'system_error.html', {'syserrmsg' :["No pages have questions for this questionnaire %s"%workingQuestionnaireTag]})

	# select a default page tag to start. This is the 'from' page.
	if 'setGlobalFlags_pageid' in request.session:
		[theWorkingPageid, workingPageTag] = request.session['setGlobalFlags_pageid']
		theWorkingPage = Page.objects.get(id=theWorkingPageid)
	else:
		theWorkingPage = allPageObjs[0] # Select a default starting page (no prior selection)
		workingPageTag = theWorkingPage.shortTag
		request.session['setGlobalFlags_pageid'] = [theWorkingPage.id, workingPageTag]

	# retrieve the questions on this page
	DebugOut('theWorkingPage before getPageQuestions: %s' %theWorkingPage)
	thePageQuestions=getPageQuestions(theWorkingPage)
	DebugOut('thePageQuestions after getPageQuestions: %s' %thePageQuestions)
	
	
	if 'globalFlagSelect' in request.session: # Global flag has already been entered or selected
		DebugOut('globalFlagSelect exists')
		globalFlagExists = True
		theGlobalFlag = request.session['globalFlagSelect']
	else:
		DebugOut('globalFlagSelect does not exist in session data')
		theGlobalFlag = ''
		globalFlagExists = False

	if 'globalFlagSelectPriority' in request.session:
		theGlobalFlagPriority = request.session['globalFlagSelectPriority']
	else:
		theGlobalFlagPriority = ''
	
	if 'globalFlagSelectDescription' in request.session:
		theGlobalFlagDescription = request.session['globalFlagSelectDescription']
	else:
		theGlobalFlagDescription = ''

	if 'globalFlagEntered' in request.session: # display previous entry for the global flag form
		theForm = setGlobalFlagForm(request.session['globalFlagEntered'])
		# three values in form:
		globalFlagExists = True
	else: # display a pristine form
		theForm = setGlobalFlagForm()

	if 'testCondition_exists' in request.session: # a test condition has already been entered
		testCondition = request.session['testCondition_exists']
		[theQForm, qustionTagToRecordNum,choiceTagToRecordNum] = UserDynamicFormCreation( thePageQuestions, testCondition, useQuestionTag=True)
		# theQForm collects responses to questions which become the testCondition
	else:
		[theQForm, qustionTagToRecordNum,choiceTagToRecordNum] = UserDynamicFormCreation( thePageQuestions, [''], useQuestionTag=True)
		testCondition = ''
	
	flagAndConditionMsg = False
	errMsgs = ''
	if request.method == 'POST':
		DebugOut('request.POST: %s' %request.POST)
		if 'currentPageButton' in request.POST:
			# Select the CURRENT page for calculation
			workingPageTag = request.POST['currentPageButton']
			DebugOut('The new working page: %s' %workingPageTag)
			[theWorkingPage, success] = getPageObj(workingQuestionnaire, workingPageTag)
			# should never fail!?
			if success:
				request.session['setGlobalFlags_pageid'] = [theWorkingPage.id, theWorkingPage.shortTag]
				thePageQuestions=getPageQuestions(theWorkingPage)
				[theQForm, qustionTagToRecordNum,choiceTagToRecordNum] = UserDynamicFormCreation( thePageQuestions, [''], useQuestionTag=True)
			else:
				errMsgs = 'Page "%s" not found.' %workingPageTag
		elif 'SubmitResponsesButton' in request.POST: # write to database
			DebugOut('SubmitResponsesButton: enter')
			# question responses have been entered
			[theQForm, qustionTagToRecordNum,choiceTagToRecordNum] = UserDynamicFormCreation( thePageQuestions, request.POST, useQuestionTag=True)
			if theQForm.is_valid():
				DebugOut('SubmitResponsesButton: theQForm.is_valid')
				# collect question responses which become the test condition
				testCondition = theQForm.cleaned_data
				request.session['testCondition_exists'] = testCondition
				DebugOut('testCondition: %s' %testCondition)
				DebugOut('globalFlagExists: %s' %globalFlagExists)
				[theQForm, qustionTagToRecordNum,choiceTagToRecordNum] = UserDynamicFormCreation( thePageQuestions, testCondition, useQuestionTag=True)
				if globalFlagExists:
					DebugOut('SubmitResponsesButton: globalFlagExists')
					createGlobalFlagRecord(workingQuestionnaire, theWorkingPage, testCondition, theGlobalFlag, theGlobalFlagPriority, theGlobalFlagDescription)
					flagAndConditionMsg = True
					DebugOut('Saved tag %s with test condition %s' %(theGlobalFlag,testCondition))
			else:
				[theQForm, qustionTagToRecordNum,choiceTagToRecordNum] = UserDynamicFormCreation( thePageQuestions, request.POST, useQuestionTag=True)
		elif 'analysisAlternatives' in request.POST: # write to database
			# Set flag when any button is "yes"
			# no need to check theQForm.
			# verify existence of global flag
			DebugOut('Save analy flag')
			[theQForm, qustionTagToRecordNum,choiceTagToRecordNum] = UserDynamicFormCreation( thePageQuestions, [''], useQuestionTag=True)
			testCondition = testCondChoices[request.POST['analysisAlternatives']] # get button text indicating condition
			if globalFlagExists:
				createGlobalFlagRecord(workingQuestionnaire, theWorkingPage, testCondition, theGlobalFlag, theGlobalFlagPriority, theGlobalFlagDescription)
				flagAndConditionMsg = True
				DebugOut('Saved tag %s with test condition %s' %(theGlobalFlag,testCondition))
		elif 'deleteSelection' in request.POST: # delete the selected record
			# delete the selected line from the global flag list
			delTag = request.POST['deleteSelection']
			globalFlagExists = False
			DebugOut('delTag: %s' %delTag)
			recSelect = int(delTag[4:]) # extract list number (not the same as the record number)
			DebugOut('recSelect: %s' %recSelect)
			allGlobalFlagsRecordList = request.session['allGlobalFlagsRecordList']
			DebugOut('allGlobalFlagsRecordList %s' %allGlobalFlagsRecordList)
			recNum = allGlobalFlagsRecordList[recSelect][4] # record to delete
			DebugOut('recNum: %s' %recNum)
			deleteGlobalFlagRecord(workingQuestionnaire, recNum)
			[theQForm, qustionTagToRecordNum,choiceTagToRecordNum] = UserDynamicFormCreation( thePageQuestions, [''], useQuestionTag=True)
		elif 'globalFlagEnteredButton' in request.POST:
			# A new global flag name entered
			DebugOut('globalFlagEnteredButton: enter')
			# collect name for for global flag
			theForm = setGlobalFlagForm(request.POST)
			if theForm.is_valid():
				DebugOut('theForm.cleaned_data: %s' %theForm.cleaned_data)
				theGlobalFlag = theForm.cleaned_data['testResultFlag']
				theGlobalFlagPriority = theForm.cleaned_data['testResultFlagPriority']
				theGlobalFlagDescription = theForm.cleaned_data['testResultFlagDescription']
				# save forms output to session data
				request.session['globalFlagEntered'] = theForm.cleaned_data
				# save variables to session data
				globalFlagExists = True
				request.session['globalFlagSelect'] = theGlobalFlag
				request.session['globalFlagSelectPriority'] = theGlobalFlagPriority
				request.session['globalFlagSelectDescription'] = theGlobalFlagDescription
			[theQForm, qustionTagToRecordNum,choiceTagToRecordNum] = UserDynamicFormCreation( thePageQuestions, [''], useQuestionTag=True)
			DebugOut('globalFlagEnteredButton: exit')
		elif 'globalFlagSelectButton' in request.POST:
			# A different global flag is selected from the displayed list of previously existing global flags
			# save variables to session data
			theGlobalFlag = request.POST['globalFlagSelectButton']
			[theGlobalFlagPriority, theGlobalFlagDescription, success] = getGlobalFlagPriority(workingQuestionnaire, theGlobalFlag) # get the priority
			DebugOut('Global flag selected: %s' %theGlobalFlag)
			globalFlagExists = True
			request.session['globalFlagSelect'] = theGlobalFlag
			request.session['globalFlagSelectPriority'] = theGlobalFlagPriority
			request.session['globalFlagSelectDescription'] = theGlobalFlagDescription
			[theQForm, qustionTagToRecordNum,choiceTagToRecordNum] = UserDynamicFormCreation( thePageQuestions, [''], useQuestionTag=True)
			DebugOut('The global flag selected: %s' %theGlobalFlag)
		elif 'submitButton' in request.POST:
			# return to the admin page
			return HttpResponseRedirect(settings.WSGI_URL_PREFIX + 'multiquest/'+'intro/') # previous screen url			
	else: # a 'GET'
		# obtain any prior setting for 'next page'
		pass
		DebugOut('"GET" posted - restore data if any')


	# Retrieve all global flags
	allGlobalFlags = listAllGlobalFlags(workingQuestionnaire)
	DebugOut('allGlobalFlags:  %s' %allGlobalFlags)
	
	if 'globalFlagSelect' in request.session: # Global flag has already been entered or selected
		DebugOut('globalFlagSelect exists')
		globalFlagExists = True
		theGlobalFlag = request.session['globalFlagSelect']
	else:
		DebugOut('globalFlagSelect does not exist in session data')
		theGlobalFlag = ''
		globalFlagExists = False

	if 'globalFlagSelectPriority' in request.session:
		theGlobalFlagPriority = request.session['globalFlagSelectPriority']
	else:
		theGlobalFlagPriority = ''
	
	if 'globalFlagSelectDescription' in request.session:
		theGlobalFlagDescription = request.session['globalFlagSelectDescription']
	else:
		theGlobalFlagDescription = ''

	# retrieve the questions on the page (theWorkingPage may have changed)
	DebugOut('theWorkingPage now: %s' %theWorkingPage)
	DebugOut('theWorkingPage type: %s' %type(theWorkingPage))
	thePageQuestions=getPageQuestions(theWorkingPage)
	DebugOut('thePageQuestions after getPageQuestions #2: %s' %thePageQuestions)

	otherAnalysisOption = allYesNoTypeQuestions( thePageQuestions )
	
	# List all global flags set by all pages
	allGlobalFlagsRecordList = listGlobalFlagsInfo(workingQuestionnaire)
	request.session['allGlobalFlagsRecordList']=allGlobalFlagsRecordList

	# build a similar list just for this page
	allGlobalFlagsRecordDict = getGlobalFlagRecord(workingQuestionnaire)
	testConditionTransitionList = []
	for item in allGlobalFlagsRecordDict:
		ptag = Page.objects.get(id=item['pageID']).shortTag
		if ptag == workingPageTag:
			testConditionTransitionList.append([item['testCondition'],item['testResultFlag'],item['testResultFlagPriority']])
	if len(testConditionTransitionList) == 0:
		testConditionTransitionList = ''
	
		
	currentContext = {
		'theQForm' : theQForm,
		'theForm' : theForm,
		'globalFlagExists' : globalFlagExists,
		'allGlobalFlags' : allGlobalFlags,
		'allGlobalFlagsRecordList' : allGlobalFlagsRecordList,
		'theGlobalFlag' : theGlobalFlag,
		'theGlobalFlagPriority' : theGlobalFlagPriority,
		'flagAndConditionMsg' : flagAndConditionMsg,
		'workingQuestionnaireTag' : workingQuestionnaireTag,
		'workingPageTag' : workingPageTag,
		'allPageTags' : allPageTags,
		'testConditionTransitionList' : testConditionTransitionList,
		'otherAnalysisOption' : otherAnalysisOption,
		'allYesButton' : allYesButton,
		'anyYesButton' : anyYesButton,
		'allNoButton' : allNoButton,
		'anyNoButton' : anyNoButton,
		'anySelectedButton' : anySelectedButton,
		'noneSelectedButton' : noneSelectedButton,
		'barTitle' : barTitle,
		'errMsgs' : errMsgs,
		}
	DebugOut('setGlobalFlags:  exiting')
	return render(request, 'working_pages/setGlobalFlags.html', currentContext)
	
def allYesNoTypeQuestions( thePageQuestions ):
	# check if all questions are of the "yes/no" variety
	otherAnalysisOption = False
	questTypeList = []
	for aQuest in thePageQuestions:
		respTyp = aQuest.responseType
		if 'SingleChoiceField' == respTyp: # special handling
			# Special handling for 'SingleChoiceField' - check the choices
			theResponseChoice = ResponseChoice.objects.filter(questionID=aQuest)
			responseList = [aResp.choiceTag for aResp in theResponseChoice]
			DebugOut('allYesNoTypeQuestions: responseList %s' %responseList)
			if responseList.sort() == ['Yes','No'].sort():
				# responses delivered will be only yes no, so "acts like" yes/no question type
				respTyp = 'YesNoField'
		questTypeList.append(respTyp)
	DebugOut('Question type list:  %s' %questTypeList)
	# Find if the question response data fields are all of one type.
	# The supported homogeneous data types are YesNoField and MultipleChoiceField.
	if len(questTypeList) >1:
		theResponseType =list(set(questTypeList)) # should be one element if all one response type
		if len(theResponseType) >1:
			otherAnalysisOption = "DoNotDisplay" # forget it. Question responses must be of homogeneous type.
		elif len(theResponseType) == 1:
			if theResponseType[0] == 'YesNoField':
				otherAnalysisOption = 'YesNoField'
				# allow, all_yes, any_yes, all_no, any_no
				# store this value - bleed00
			elif theResponseType[0] == 'MultipleChoiceField':
				otherAnalysisOption = 'MultipleChoiceField'
				# allow, all_slected, some_selected, none_selected
				# store this value - bleed00
		# forget the other options. Not yet implemented
	elif len(questTypeList) == 1:
		if questTypeList[0] == 'MultipleChoiceField':
			otherAnalysisOption = 'MultipleChoiceField'
		else:
			# must have more than one question to display for 
			otherAnalysisOption = "DoNotDisplay"
	else:
		otherAnalysisOption = "DoNotDisplay" # no question types
		
	return otherAnalysisOption


def deleteGlobalFlag(workingQuestionnaire, theGlobalFlagToDelete):
	# Delete the global flag from PageAnalysis
	PageAnalysis.objects.filter(
		questionnaireID = workingQuestionnaire,
		testResultFlag = theGlobalFlagToDelete,
		).delete()
	return True
	
	
@login_required()
def setPageToPageTransitionCalculated(request):
	# Set "next page" transition based upon response to questions.
	DebugOut('setPageToPageTransitionCalculated:  entering')

	# select a default Questionnaire and Project tag to start.
	[workingProject, workingQuestionnaire] = getSessionQuestionnaireProject(request)
	if not workingProject:
		# select a project.
		errMsg = ['The Project has not been selected']
		redirectURL = registrationURL_base + 'selectProjectDefault/'
		DebugOut('No project, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)
	if not workingQuestionnaire:
		errMsg = ['The questionnaire has not been selected']
		redirectURL = registrationURL_base + 'selectQuestionnaireDefault/'
		DebugOut('No questionnaire selected, so redirect to: %s' %redirectURL)
		return HttpResponseRedirect(redirectURL)

	errMsgs = [] # messages to the user! Caution.

	# Retrieve the Questionnaire Tag
	workingQuestionnaireTag=workingQuestionnaire.shortTag
	
	# Retrieve the Project tag
	workingProjectTag=workingProject.shortTag
	# find all existing page shortTag's for this questionnaire
	allPageTags = getAllPageTags(workingQuestionnaire)
	DebugOut('allPageTags (only pages with questions): %s' %allPageTags)
	
	# find all existing pages with questions for this questionnaire
	allPageWQs = findAllPagesWQuestions(workingQuestionnaire)
	# allPageTagsQs:  list of tags for pages with questions attached.
	allPageTagsQs = [aPage.shortTag for aPage in allPageWQs]
	
	# for Session data - tracking current page
	currentPageSessionTag = 'currentPageTag_admin'
	
	# select a default page tag to start. This is the 'from' page.
	[workingPageTag, theWorkingPage] = selectCurrentPage(request, currentPageSessionTag, allPageWQs)
	DebugOut('workingPageTag: %s' %workingPageTag)
	
	# got all starting data
	DebugOut('Default values:')
	DebugOut('workingQuestionnaireTag: %s' %workingQuestionnaireTag)
	DebugOut('workingPageTag: %s' %workingPageTag)
		
	# Define session values tags for later use
	pageBaseURL = url_base + workingProjectTag+'/'+workingQuestionnaireTag+'/'
	
	testCondition = '' # test condition then proceed to the indicated next page

	nextPAndConditionMsg = '' # message that the test condition was saved to the database
	
	# Do not automatically display the questions
	theQForm = ''
	
	pgNextCalc = ''
	recordType = 'calculated'	# this function creates, edits and deletes 
								# records of this type in QuestionnairePage
	
	if request.method == 'POST':
		DebugOut('setPageToPageTransitionCalculated:  After POST')
		DebugOut('request.POST %s' %str(request.POST))
		if 'returnToHome' in request.POST:
			DebugOut('returnToHome button hit')
			redirectURL = registrationURL_base + 'userLanding/'
			return HttpResponseRedirect(redirectURL) # previous screen url
		elif 'currentPage' in request.POST:
			# Selected a new current working page
			workingPageTag = request.POST['currentPage']
			[theWorkingPage, success]=getPageObj(workingQuestionnaire, workingPageTag)
			if not success:
				return render(request, 'system_error.html', {'syserrmsg': ['Debug:  Page does not exist: %s' %workingPageTag]})
			request.session[currentPageSessionTag] = theWorkingPage.id
			DebugOut('The new working page: %s' %workingPageTag)
		elif 'nextPageButton' in request.POST:
			# select the NEXT page for calculation
			newNextPageTag = request.POST['nextPageButton']
			[newNextPageObj, success]=getPageObj(workingQuestionnaire, newNextPageTag)
			request.session['setPageTransPageNextCalc'] = newNextPageObj.id
			DebugOut('The new calculated next page: %s' %newNextPageObj.shortTag)
		elif 'Save responses to questions' in request.POST:
			DebugOut('In Save responses to questions')
			# display questions, accept responses, save to db
			# retrieve the questions on the page
			thePageQuestions=getPageQuestions(theWorkingPage)
			if len(thePageQuestions) == 0:
				emsg = 'No questions can be found for the page "%s"' % workingPageTag
				errMsgs.append(emsg)
				DebugOut(emsg)
			else:
				DebugOut('Display questions and gather responses.')
			# display questions, prepare for data entry
			theQForm = UserDynamicFormCreation( thePageQuestions, request.POST, useQuestionTag=True)
			if 'setPageTransPageNextCalc' in request.session:
				newNextPageid = request.session['setPageTransPageNextCalc']
				try:
					newNextPageObj = Page.objects.get(id=newNextPageid)
				except:
					newNextPageObj = None
					errMsgs.append('next page not retrieved. Select the desired "next page" for the transition first.')
			else:
				DebugOut('next page not defined.')
				errMsgs.append('next page not defined. Select the desired "next page" for the transition first.')
				newNextPageObj = None
			if theQForm.is_valid() and newNextPageObj:
				DebugOut('Question response data is valid')
				# tag for 'next page'
				questionResponsesWithTags = theQForm.cleaned_data
				testCondition = questionResponsesWithTags # uses tags from database when available. Unique tag per page
				saveTestConditonToQuestionnairePage(testCondition,
					newNextPageObj, theWorkingPage, workingQuestionnaire, recordType)
				nextPAndConditionMsg = 'The test conditon "%s" for transition to the next page "%s" was saved' %(testCondition, newNextPageObj.shortTag)
				theQForm = UserDynamicFormCreation( thePageQuestions, questionResponsesWithTags, useQuestionTag=True)
				DebugOut('testCondition: %s' %testCondition)
			DebugOut('workingQuestionnaireTag: %s' %workingQuestionnaireTag)
			DebugOut('workingPageTag: %s' %workingPageTag)
		elif 'deleteSelection' in request.POST: # delete the selected record
			# delete the selected line from the condition table
			lineSelect = int(request.POST['deleteSelection']) # line selected
			testConditionTransitionList = getTestConditionFromQuestionnairePage(workingQuestionnaire, theWorkingPage)
			# record structure is:
			# record number, test condition, next page short tag, next page object
			DebugOut('lineSelect:  %s' %lineSelect)
			DebugOut('Length of list %s' %len(testConditionTransitionList))
			DebugOut('Length of record in list %s' %len(testConditionTransitionList[0]))
			DebugOut('The line:  %s' %testConditionTransitionList[lineSelect])
			recSelect = int(testConditionTransitionList[lineSelect][0])
			deleteTestConditonFromQuestionnairePage(recSelect)
	else: # a 'GET'
		# obtain any prior setting for 'next page'
		DebugOut('"GET" posted - restore data if any')
	
	# retrieve the questions on the page, theWorkingPage may have changed
	thePageQuestions=getPageQuestions(theWorkingPage)
	pageQuestionsExist = len(thePageQuestions) != 0
	pluralQuestions = len(thePageQuestions) > 1
	if theQForm == '' and len(thePageQuestions) != 0:
		theQForm = UserDynamicFormCreation( thePageQuestions, [''], useQuestionTag=True)
	
	# find existing test conditions for this page
	testConditionTransitionList = getTestConditionFromQuestionnairePage(workingQuestionnaire, theWorkingPage)
	# record structure is:
	# record number, test condition, next page short tag

	DebugOut('testConditionTransitionList: %s' %testConditionTransitionList)
	
	# retrieve "nextPage" if set
	if 'setPageTransPageNextCalc' in request.session:
		newNextPageid = request.session['setPageTransPageNextCalc']
		try:
			newNextPageObj = Page.objects.get(id=newNextPageid)
			newNextPageTag = newNextPageObj.shortTag
		except:
			newNextPageTag = ''
	else:
		newNextPageTag = ''
	defaultNextPageObj = getNextPageFromDB(workingQuestionnaire, theWorkingPage)
	if defaultNextPageObj:
		defaultNextPageTag = defaultNextPageObj.shortTag
	else:
		defaultNextPageTag = ''
	readyToSubmit = newNextPageTag and workingPageTag and testCondition
	
	# get all page transition based upon calculation (testCondition)
	[calculatedTransitionList, success] = getTestConditionTransitions(workingQuestionnaire)
	if not success:
		calculatedTransitionList = '' # flag indicating "do not display"	

	currentContext = {
		'theQForm' : theQForm,
		'workingProject' : workingProject,
		'workingQuestionnaire' : workingQuestionnaire,
		'workingPageTag' : workingPageTag,
		'newNextPageTag' : newNextPageTag,
		'defaultNextPageTag' : defaultNextPageTag,
		'readyToSubmit' : readyToSubmit,
		'pgNextCalc' : pgNextCalc,
		'allPageTagsQs' : allPageTagsQs, # only pages with questions
		'allPageTags' : allPageTags, # with or without questions
		'nextPAndConditionMsg' : nextPAndConditionMsg,
		'pageQuestionsExist' : pageQuestionsExist,
		'pluralQuestions' : pluralQuestions,
		'testConditionTransitionList' : testConditionTransitionList,
		'calculatedTransitionList' : calculatedTransitionList,
		'errMsgs' : errMsgs,
		}
	currentContext.update(csrf(request))
	DebugOut('setPageToPageTransitionCalculated:  exiting')
	return render(request, 'working_pages/setPageToPageTransitionCalculated.html', currentContext)

def selectCurrentPage(request, currentPageSessionTag, allPageObjs):
	# select a default page tag to start. This is the 'from' page.
	if currentPageSessionTag in request.session: # first look in sessions data
		workingPageID = request.session[currentPageSessionTag]
		try:
			workingPageObj = allPageObjs.get(id=workingPageID)
		except:
			workingPageObj = allPageObjs.latest('lastUpdate') # use last updated object
			request.session[currentPageSessionTag] = workingPageObj.id
		workingPageTag = workingPageObj.shortTag
	else: # if not in sessions data, then use last page
		workingPageObj = allPageObjs.latest('lastUpdate') # use last updated object
		workingPageTag = workingPageObj.shortTag
		request.session[currentPageSessionTag] = workingPageObj.id
	DebugOut('Current page session tag %s: has the value: %s' %(currentPageSessionTag, workingPageTag))
	return [workingPageTag, workingPageObj]
	
def getQuestionnairePageInfo(pageObj, questionnaireObj):
	# retrieves the testCondition and calculated condition
	# required to transition to page nextPage.
	# Needed:  QuestionnairePage
	# separate the different types of records
	# there are three different "next pages":  next_page_default, calculated, globalFlag directed
	
	# only one default
	try:
		nextPageDefault = QuestionnairePage.objects.get(
			pageID = pageObj,
			questionnaireID = questionnaireObj,
			recordType = 'next_page_default'
			).nextPage # should be only one!!
	except QuestionnairePage.DoesNotExist:
		nextPageDefault = '' # no default

	# perhaps more than one global flag
	try:
		testGlobalFlagObj = QuestionnairePage.objects.filter(
			pageID = pageObj
			).filter(
			questionnaireID = questionnaireObj
			).filter(
			recordType = 'globalFlag'
			)
		testGlobalFlagDict = {}
		for item in testGlobalFlagObj:
			testGlobalFlagDict.update({item.testCondition : item.nextPage})
	except QuestionnairePage.DoesNotExist: # bleed1 *** what's behavior when no flag? Not an exception!
		testGlobalFlagDict = {}

	# may be more than one condition directing to the "next page"
	try:
		testConditionvsNextPageObj = QuestionnairePage.objects.filter(
			pageID = pageObj
			).filter(
			questionnaireID = questionnaireObj
			).filter(
			recordType = 'calculated'
			)
		testConditionvsNextPageDict = {}
		for item in testConditionvsNextPageObj:
			testConditionvsNextPageDict.update({item.testCondition : item.nextPage})
	except QuestionnairePage.DoesNotExist:
		testConditionvsNextPageDict = {}

	return [nextPageDefault, testGlobalFlagDict, testConditionvsNextPageDict ]

def createPageList(allPages):

	pageListCols = [
		'Select',
		'Page tag',
		'Page type',
		'Description',
		'Explanation',
		'Prologue',
		'Epilogue',
		]
	ii = 1
	pageList = []
	for aPage in allPages:
		aRow = [
			'R_'+str(ii),
			aPage.shortTag,
			aPage.pageType,
			aPage.description,
			aPage.explanation,
			aPage.prologue,
			aPage.epilogue,
			]
		pageList.append(aRow)
		ii = ii + 1
		
	return [pageList, pageListCols]

def editSummaryAndAnalysisPage(request):
	DebugOut('editSummaryAndAnalysisPage: Entering')
	
	#*** select a default project tag and questionnaire tag to start. May have been reset by user
	[theProject, theQuestionnaire] = getSessionQuestionnaireProject(request)
	if not theQuestionnaire:
		errMsg = ['The questionnaire has not been selected']
		return render(request, 'system_error.html', { 'syserrmsg': errMsg})

	if errMsg:
		DebugOut('taking system error exit')
		DebugOut(str(errMsg))
		return render(request, 'system_error.html', { 'syserrmsg': errMsg})
	errMsg = []
	try:
		allQuestionnaires = Questionnaire.objects.all().order_by('shortTag')
	except:
		DebugOut('List Questionnaires:  query to database failed.')
		errMsg.append('List Questionnaires:  query to database failed.')

	if errMsg != []:
		DebugOut(str(errMsg))
		return render(request, 'system_error.html', { 'syserrmsg': errMsg})

	questTags = [aQuest.shortTag for aQuest in allQuestionnaires] # list comprehension
		
	workingQuestionnaireTag = theQuestionnaire.shortTag

	# find all existing Summary pages
	try:
		allSummaryPages=Page.objects.filter(pageType = 'questionnaireSummary').order_by('shortTag')
	except:
		return render(request, 'system_error.html', {'syserrmsg': ['Debug:  Page data is missing.']})
	allPageTags = [aPage.shortTag for aPage in allSummaryPages]
	
	theForm = editSummaryAndAnalysisForm()

	currentContext = {
		'theForm' : theForm,
		'questTags' : questTags,
		'workingQuestionnaireTag' : workingQuestionnaireTag,
		'allPageTags' : allPageTags,
		'back_to_intro' : 'Return to the Introduction Page',
		'url_base' : url_base,
		'errMsg' : errMsg,
		}

	DebugOut('editSummaryAndAnalysisPage: Exit')
	return render(request, workingPageTemplateRoot + 'editSummaryAndAnalysisPage.html',
		currentContext)
		
def displayAndEditPage(request):
	# edit a page

	pageBaseURL = settings.WSGI_URL_PREFIX + 'multiquest/' 

	# find all existing page shortTag's
	try:
		allP=Page.objects.all()
	except:
		return render(request, 'system_error.html', {'syserrmsg': ['Debug:  Page data is missing.']})
	allTags = [aPage.shortTag for aPage in allP]
	
	# select a default page tag to start.
	if 'currentPageTag' in request.session: # first look in sessions data
		currentPageTag = request.session['currentPageTag']
	else: # if not in sessions data, then use last tag
		currentPageTag = allTags[-1]
		request.session['currentPageTag'] = currentPageTag

	# try to retrieve the page
	try:
		thePage=Page.objects.filter(shortTag=currentPageTag).latest('lastUpdate')
	except Page.DoesNotExist: # so set to a legal value
		return render(request, 'system_error.html', {'syserrmsg': ['Debug:  Most recent page data is missing.']})

	
	if request.method == 'POST':
		theForm = PageForm( request.POST)
		if request.POST['submitButton'] == 'Discard Page Edits': # Return to previous page
			return HttpResponseRedirect(pageBaseURL+'intro/') # previous screen url
		if theForm.is_valid():
			if request.POST['submitButton'] in allTags: # click on page button - change pages
				currentPageTag = request.POST['submitButton']
				try:
					thePage=Page.objects.get(shortTag=currentPageTag)
				except Page.DoesNotExist: # so set to a legal value
					return render(request, 'system_error.html', {'syserrmsg': ['Debug:  Most recent page data is missing.']})
				initialValues ={'shortTag' : currentPageTag,
					'description' : thePage.description,
					'explanation' : thePage.explanation,
					'prologue' : thePage.prologue,
					'epilogue' : thePage.epilogue,
					'lastUpdate' : thePage.lastUpdate,
					}
				theForm = PageForm(initial=initialValues)
			elif request.POST['submitButton'] == 'Save Page Edits':
				if theForm.cleaned_data['shortTag'] != currentPageTag:
					currentPageTag = theForm.cleaned_data['shortTag']
					try:
						thePage=Page.objects.get(shortTag=currentPageTag)
					except Page.DoesNotExist: # so create the page
						thePage=Page(shortTag=currentPageTag)
				thePage.shortTag = currentPageTag
				thePage.description = theForm.cleaned_data['description']
				thePage.explanation = theForm.cleaned_data['explanation']
				thePage.prologue = theForm.cleaned_data['prologue']
				thePage.epilogue = theForm.cleaned_data['epilogue']
				thePage.lastUpdate = timezone.now()
				thePage.save()
				responseMsg = 'Page "%s" edited and saved.' %currentPageTag
				request.session['currentPageTag'] = currentPageTag
				return HttpResponseRedirect(pageBaseURL+'intro/') # previous screen url
			elif request.POST['submitButton'] == 'Delete Current Page': # Return to previous page
				Page.objects.filter(shortTag=currentPageTag).delete()
				return HttpResponseRedirect(pageBaseURL+'intro/') # previous screen url
	else:
		initialValues ={'shortTag' : currentPageTag,
			'description' : thePage.description,
			'explanation' : thePage.explanation,
			'prologue' : thePage.prologue,
			'epilogue' : thePage.epilogue,
			'lastUpdate' : thePage.lastUpdate,
			}
		theForm = PageForm(initial=initialValues)
				
	currentContext = { 'theForm' : theForm,
		'shortTag' : currentPageTag,
		'allTags' : allTags,
		'lastUpdate' : thePage.lastUpdate,
		'back_to_intro' : 'Return to the Introduction Page',
		'url_base' : url_base,
		}
	return render(request, 'working_pages/displayAndEditPage.html', currentContext)

def QuestContinue(request, whichProject, whichQuest, whichPage):

	DebugOut( 'In QuestContinue. whichProject: %s whichQuest: %s whichPage: %s' %(whichProject, whichQuest, whichPage))
	errMess = []
	# Standard verification w.r.t. project and questionnaire
	[theProject, theQuestionnaire, errMess] = verifyQuestionnaireProject(request, whichProject, whichQuest)
	if errMess != []:
		return render(request, 'system_error.html', {'syserrmsg': errMess})
	urlprefix = settings.WSGI_URL_PREFIX # backward compatibility! for Explanations

	pageBaseURL = settings.WSGI_URL_PREFIX + 'multiquest/' + whichProject+'/'+whichQuest+'/'
	request.session['pageBaseURL'] = pageBaseURL
	
	if whichPage == 'completion':
		return HttpResponseRedirect( pageBaseURL+'completion')

	# Standard page object retrieval
	[thePageObj, success] = getPageObj(theQuestionnaire, whichPage)
	if not success:
		errMsg=['Could not find a page transition for %s'%whichPage]
		return render(request, 'system_error.html', {'syserrmsg': errMess})
		
	thisPageTag = whichPage
	
	# Indicate if this is a start page for special logic.
	startPage = False
	firstPage = getStartPageObj(theQuestionnaire)
	if firstPage == thePageObj:
		startPage = True
	
# *** rework the following errors
# 	if not request.session.test_cookie_worked(): # check for cookie function and therefore session existence
# 		DebugOut('QuestContinue: Please enable cookies in your browser.')
# 		return render(request, 'system_error.html', {'syserrmsg': ['Please enable cookies in your browser.']})

	if 'constantPageDataDict' in request.session:
		constantPageDataDict = request.session['constantPageDataDict']
	else:
		return render(request, 'system_error.html', {'syserrmsg': ['Debug:  header and footer page data is missing.']})

#	pull questions from the database
	theQuestionsOnThePage = getPageQuestions( thePageObj)
	if len(theQuestionsOnThePage) == 0:
		errMsg = '#1No questions can be found for the page! None in the database. %s' % thisPageTag
		# continue - display the Page fields
		
# got everything - GO

# Determine if there is an image
	imageFileName = thePageObj.imageFileName # false if no image
	
# Determine the page type
	pageType = thePageObj.pageType
	DebugOut('pageType: %s' %pageType)
	if pageType == 'hasTemplateAndFunction':
		# This type of page has a template and function - both of the same name
		# and the last part of the url.
		pass # *** later?
		

	prologue = SubstituteWords( thePageObj.prologue ) # replace keywords with current values
	epilogue = SubstituteWords( thePageObj.epilogue )
		
#	special logic for 'sendQuestions' page type
	useQuestionsFromSessionTag = 'useQuestionsFromSessionTag_' + thisPageTag
	useAlternateQuestions = useQuestionsFromSessionTag in request.session and pageType != 'sendQuestions'
	if useQuestionsFromSessionTag in request.session:
		previousPageQuestionResults = request.session[useQuestionsFromSessionTag]
		DebugOut("previousPageQuestionResults")
		DebugOut(str(previousPageQuestionResults))
		haveQuestions = True
	else:
		haveQuestions = False

	if useAlternateQuestions and haveQuestions and thisPageTag == 'H7a':
		DebugOut('YES sendQuestions entry questions:')
		# get previous questions from Session data
		# flatten the dictionary
		tagListFromPrev = convertFormsDataToDict(previousPageQuestionResults)
		DebugOut('Tags from previous questions: %s' %tagListFromPrev)
		# set up for page 'H7a'
		# build question follow up table
		qFollow = [ 
			['Birth control pills' , 'pHxHormUseBCAgeStart'],
			['Birth control pills' , 'pHxHormUseBCAgeEnd'],
			['Estrogen replacement', 'pHxHormUseEstrogenAgeStart'],
			['Estrogen replacement', 'pHxHormUseEstrogenAgeEnd'],
			['Progesterone replacement', 'pHxHormUseProgesteroneAgeStart'],
			['Progesterone replacement' , 'pHxHormUseProgesteroneAgeEnd'],
			['Tamoxifen', 'pHxHormUseTamoxifenAgeStart'],
			['Tamoxifen' , 'pHxHormUseTamoxifenAgeEnd'],
			['Raloxifene', 'pHxHormUseRaloxifeneAgeStart'],
			['Raloxifene' , 'pHxHormUseRaloxifeneAgeEnd'],
			['Arimidex', 'pHxHormUseArimidexAgeStart'],
			['Arimidex' , 'pHxHormUseArimidexAgeEnd'],
			]
		followQTags = [] # make a list of followOn question tags
		for prevTag in tagListFromPrev.keys():
			for followOn in qFollow:
				if prevTag in followOn:
					followQTags.append(followOn[1])
		if followQTags != []:	
			DebugOut('Selected tags for followOn questions: %s' %followQTags)
			# retrieve these questions from the database
			# construct the query using the "Q object" (see page 104) in pdf from Django site
			# and:  https://docs.djangoproject.com/en/1.5/topics/db/queries/#complex-lookups-with-q
		
			qtSum = Q(questionID__questionTag=followQTags[0])
			for aQuestTag in followQTags:
				qtSum = qtSum | Q(questionID__questionTag=aQuestTag) # Sum the queries as "or"'s
			qtAll = qtSum & Q(pageID=thePageObj) # make sure the question belong to this Page!
			replacePQ = PageQuestion.objects.order_by('questionSequence').filter( qtAll)
			replacePageQuestions = [aPQ.questionID for aPQ in replacePQ]
			# Kludge:  append the record number to get a unique page tag.
			for aQuestion in replacePageQuestions:
				theQID = str(aQuestion.id) # will not be used as an integer (not used)
				theQTag = aQuestion.questionTag + '_' + theQID # Kludge:  append Question record to tag.
				aQuestion.questionTag = theQTag # Don't save this object!!
		else:
			theQuestionsOnThePage = ""
		if not theQuestionsOnThePage: # no questions available, continue to next page
		# *** change to go to next page when 'sendQuestions' page type
			next_pageObj = pageCalc(request,theQuestionnaire, thePageObj )
			if next_pageObj:
				next_page = next_pageObj.shortTag
			else:
				next_page = ''
			errMsg = '#2No questions can be found for this page (%s), so go to the next page (%s)!' % (thisPageTag,next_page)
			DebugOut( errMsg)
			if next_page != '':
				return HttpResponseRedirect(pageBaseURL+next_page) # next screen url
			else: # assume at the end of the questionnaire
				DebugOut( 'NEXT button clicked. Completion? this_page: %s, next_page: %s' %(thisPageTag,next_page))
				return HttpResponseRedirect( pageBaseURL+'completion/')

		theQuestionsOnThePage = replacePageQuestions # replace with the selected questions
		# *** delete this Session data after use! Just before exiting to a new page
		# del request.session[useQuestionsFromSessionTag]
		DebugOut('YES sendQuestions generated (pruned):')
		DebugOut(theQuestionsOnThePage)
	else:
		DebugOut('NO sendQuestions')
		# else use questions from database

	if theQuestionsOnThePage:
		DebugOut('QuestContinue: Questions are: \n%s' %theQuestionsOnThePage)
	else:
		DebugOut('#3No questions can be found for this page (%s).' % (thisPageTag))
		

	# Define session values tags for later use
	pageSessionTag = 'HavePageResults_' + thisPageTag # concoct a name unique to this page for forms results straight from form

	errmsg = '' # to display on the page
	
	if request.method == 'POST':
		DebugOut( 'after POST')
		[theForm, qustionTagToRecordNum,choiceTagToRecordNum] = UserDynamicFormCreation( theQuestionsOnThePage, request.POST, useQuestionTag=True)
		if useAlternateQuestions:
			# questions already responded to in Form. Delete communication for "sendQuestions" page
			del request.session[useQuestionsFromSessionTag] # delete questions data
		if theForm.is_valid(): # have valid data from page
			DebugOut( 'Form is valid. Saving data.') # Save the cleaned data
			questionResponsesWithTags = theForm.cleaned_data
			DebugOut('The cleaned data with question tags is:')
			DebugOut(str(questionResponsesWithTags))
			# save this page data for redisplay of the page at Questionnaire Summary
			request.session[pageSessionTag] = questionResponsesWithTags
			savePageData(request, questionResponsesWithTags, thePageObj, theQuestionsOnThePage, qustionTagToRecordNum,choiceTagToRecordNum) # save for recap at the end of session
			if request.POST['submitButton'] == 'Next':
				UpdateLast_URL_Next(request, thisPageTag) # ignore 'back to' output
				saveGlobalFlagsToSessionData(request, theQuestionnaire, thePageObj, questionResponsesWithTags)
				next_pageObj = pageCalc(request,theQuestionnaire, thePageObj, questionResults=questionResponsesWithTags )
				if next_pageObj:
					next_page = next_pageObj.shortTag
					pageTypeNextPage = next_pageObj.pageType
				else:
					next_page = ''
					pageTypeNextPage = ''
				if next_page != '':
					if pageType == 'sendQuestions': # save data for next page
						useQuestionsFromSessionTag = 'useQuestionsFromSessionTag_' + next_page
						nextPageQuestions = followOnQuestions(thisPageTag, questionResponsesWithTags)
						request.session[useQuestionsFromSessionTag] = questionResponsesWithTags
					if pageTypeNextPage == 'questionnaireSummary': # append to the url
						next_pagePageType = next_page + '/' + pageTypeNextPage
						DebugOut('PageType appended to next_page url:  %s' %next_pagePageType)
						return HttpResponseRedirect(pageBaseURL+next_pagePageType) # next screen url
					DebugOut( 'NEXT button clicked. thisPageTag: %s, next_page: %s' %(thisPageTag,next_page))
					return HttpResponseRedirect(pageBaseURL+next_page) # next screen url
				else: # assume at the end of the questionnaire
					DebugOut( 'NEXT button clicked. Completion? thisPageTag: %s, next_page: %s' %(thisPageTag,next_page))
					return HttpResponseRedirect( pageBaseURL+'completion')
			else: # assume button pressed is 'Back'
				back_to = UpdateLast_URL_Back(request, thisPageTag)
				DebugOut( 'not NEXT button clicked. thisPageTag: %s, back_to: %s' %(thisPageTag,back_to))
				return HttpResponseRedirect(pageBaseURL+back_to) # previous screen url				
		elif request.POST['submitButton'] == 'Back': # save no data since it is not valid
			DebugOut( 'BACK button clicked')
			back_to = UpdateLast_URL_Back(request, thisPageTag)
			DebugOut('next page %s' %back_to)
			return HttpResponseRedirect(pageBaseURL+back_to) # previous screen url
	else: # not a POST
		DebugOut('Not a POST')
		# Recover session values for this page, if any
		if pageSessionTag in request.session:
			# fill fields with previously entered data from this session - if any
			DebugOut('Page data is in session tag, so fill the form with previous data. Page: %s' %thisPageTag)
			# this data has been 'cleaned'
			[theForm, qustionTagToRecordNum,choiceTagToRecordNum]  = UserDynamicFormCreation( theQuestionsOnThePage, request.session[pageSessionTag], useQuestionTag=True)
			# so retrieve the data
			DebugOut('session data dump start:')
			DebugOut('Session: %s' %request.session[pageSessionTag])
			DebugOut('session data dump end')
			DebugOut('bound?: %s' %theForm.is_bound)
		else: # no valid data from prior visit to this page
			DebugOut('No page data in session tag: %s' %thisPageTag)
			[theForm, qustionTagToRecordNum,choiceTagToRecordNum]  = UserDynamicFormCreation( theQuestionsOnThePage, [''], useQuestionTag=True)

	computerT = computertype(request) # identify computer type
	dynamicPageDetails = pagePerComputer(computerT)
	fontSize = dynamicPageDetails['fontSize']
	fontSizeTextBox = dynamicPageDetails['fontSizeTextBox']
	debugOn = settings.DEBUG
	contextDict = {
		'explanation' : SubstituteWords( thePageObj.explanation ),
		'theForm' : theForm,
		'prologue' : prologue,
		'epilogue' : epilogue, 
		'errmsg' : errmsg,
		'computerT' : computerT,
		'field_border' : '1',	# border width - zero is ok.
		'field_style' : 'as_p',
		'fontSize' : fontSize,
		'fontSizeTextBox' : fontSizeTextBox,
		'haveImage' : imageFileName,
		'thisPageTag' : thisPageTag,
		'thisPageRecNum' : thePageObj.id,
		'debugOn' : debugOn,
		#'haveImage' : imageCalc(thisPageTag),
		}
	currentContext = constantPageDataDict.copy()
	currentContext.update(contextDict)
	if startPage: # no back button on the start page
		currentContext.update({'back_not_enabled' : True})
	UpdateLast_URL_Next(request, thisPageTag)
	DebugOut( 'rendering page %s' %thisPageTag)
	currentContext.update(csrf(request))
	DebugOut( 'QuestContinue: exit')
	return render(request, 'generic_page.html', currentContext)
	
def savePageData(request, cleanedData, thePageObj, thePageQuestions, qustionTagToRecordNum,choiceTagToRecordNum ):
	# Use this function to save question responses to Session Data
	DebugOut('savePageData:  enter')
	# cleanedData is a dictionary
	# always use this function to update allResultsDict and allResultsList
	#DebugOut('Cleaned data as input is:')
	#DebugOut(str(cleanedData))
	#DebugOut('Input questions are: ')
	#DebugOut(str(thePageQuestions))
	# Questions are associated with a sequential number. This number is incremented throughout the session
	if 'questionSequenceNumber' in request.session:
		seqNumber = request.session['questionSequenceNumber']
	else: # initialize
		seqNumber = 0
		request.session['questionSequenceNumber'] = seqNumber
	
	# create a version of the cleaned data with a tag unique with respect to the entire questionnaire
	cleanedDataUniqueTag = {}
	for uniqueQuestionLabel, questionResponseValue in cleanedData.iteritems():
		if uniqueQuestionLabel in qustionTagToRecordNum:
			questionRecNum = qustionTagToRecordNum[uniqueQuestionLabel]
			aQuest = Question.objects.get(id=questionRecNum)
		else:
			DebugOut('syserrmsg:  A question label without a corresponding record.')
			return
		if uniqueQuestionLabel in choiceTagToRecordNum:
			responseChoiceRecNum = choiceTagToRecordNum[uniqueQuestionLabel]
		else:
			responseChoiceRecNum = None # no problem
		# find values for output
		questionRecNumStr = str(questionRecNum)
		responseChoiceRecNumStr = str(responseChoiceRecNum)
		uniqueTag = encodeQuestionResponseLabel(questionRecNum,responseChoiceRecNum) # with encoded record numbers
		seqNumber+=1
		
		if type(questionResponseValue) == list:
			multipleResponses = []
			for aResponse in questionResponseValue:
				if '_' in aResponse:
					[questionRecNumLoop,responseChoiceRecNumLoop] = decodeQuestionResponseLabel(aResponse)
					try:
						loopResponse = ResponseChoice.objects.get(id=int(responseChoiceRecNumLoop)).choiceText
						DebugOut('Should be a unique id with encoding "%s"'%aResponse)
					except:
						DebugOut('savePageData: failed inside loop: aResponse: "%s"'%aResponse)
						loopResponse = 'Fail'
				else:
					loopResponse = aResponse # make a guess:  actual choiceText
				multipleResponses.append(loopResponse)
			questionResponseValue = multipleResponses
		# Prepare a record in Session Data
		aLine = [
			questionResponseValue,	# 0
			aQuest.questionText,	# 1
			questionRecNumStr,		# 2
			responseChoiceRecNumStr,# 3
			thePageObj.shortTag,	# 4
			thePageObj.id,			# 5
			uniqueTag,				# 6 # with encoded record numbers
			aQuest.questionTag,		# 7
			seqNumber,				# 8
			]
		#DebugOut('savePageData: uniqueTag: "%s"'%uniqueTag)
		#DebugOut('aLine %s' %aLine)
		cleanedDataUniqueTag.update({uniqueTag:aLine})
	request.session['questionSequenceNumber'] = seqNumber
	
	if allResultsDict in request.session: # add to the previous responses
		# *** warning, duplicate uniqueQuestionLabels are trashed
		request.session[allResultsDict].update(cleanedDataUniqueTag)
		#DebugOut('Session dict data updated in savePageData')
	else:
		request.session[allResultsDict] = cleanedDataUniqueTag
		#DebugOut('Session dictionary data initialized in savePageData')

# 	DebugOut('Dump the data dictionary after updating') # for Debug
# 	for keyname,keyvalue in request.session[allResultsDict].iteritems():
# 		DebugOut('keyname %s,keyvalue %s' %(keyname,keyvalue))
# 	DebugOut('Dump the data dictionary end')
	
	# also save page data as a list with unique tags. Duplicates have been removed.
	allSessionResultsList = []
	for uniqueQuestionLabel, lineInfo in request.session[allResultsDict].iteritems():
		allSessionResultsList.append(lineInfo)
	
	allSessionResultsListSorted = sorted( allSessionResultsList, key=itemgetter(8))
	
	allSessionResultsListOut = []
	for aLine in allSessionResultsListSorted:
		allSessionResultsListOut.append(aLine[:8]) # strip the sequence number
#		DebugOut('Sorted question response: %s'%aLine[:8])
	
	request.session[allResultsList] = allSessionResultsListOut # destroy previous list - this list is complete with no dups
	DebugOut('Session list data updated in savePageData')

	DebugOut('savePageData:  exiting')
	return True

def followOnQuestions(this_page, cleaned_data):
	# Query database for follow-on questions for this page

	return cleaned_data

def convertDictDataToList(theDictData): #convert dict data to list
	DebugOut('entering convertDictDataToList')
	listOut = []
	for itemValue in theDictData:
		if type(itemValue) == list: # go another level
			for itemList2ndLevel in itemValue:
				listOut.append([itemList2ndLevel , True])
		else:
			listOut.append([item.html_name , itemValue])
	listOut.sort() # make sure changing the order of the questions has no effect on the list order
	DebugOut(str(listOut))
	DebugOut('Exiting convertDictDataToList')
	return listOut

def convertFormsDataToDict(theCleanedData):
	"""flatten the incoming dictionary, which prepares items for saving to Session data
	"""
	DebugOut('entering convertFormsDataToDict')
	dictOut = {}
	for itemKey in theCleanedData.keys():
		itemValue = theCleanedData[itemKey]
		if type(itemValue) == list: # go to another level
			for itemKey2 in itemValue:
				dictOut.update({itemKey2 : True}) # Assume Boolean!!
		else:
			dictOut.update({itemKey : itemValue})
	DebugOut(str(dictOut))
	DebugOut('Exiting convertFormsDataToDict')
	return dictOut

def encodeQuestionResponseLabel(questionRecNum,responseChoiceRecNum):
	""" Encodes Question and QuestionResponse record numbers into a special label.
	"""
	if responseChoiceRecNum:
		rcRec = str(responseChoiceRecNum)
	else:
		rcRec = ''
	uniqueQuestionLabel = 'Question_'+str(questionRecNum)+'_'+rcRec
	return uniqueQuestionLabel

def decodeQuestionResponseLabel(uniqueQuestionLabel):
	""" Decodes special label set by encodeQuestionResponseLabel
	"""
	msgOut = []
	if '_' not in uniqueQuestionLabel:
		# wrong format
		DebugOut('decodeQuestionResponseLabel:  wrong format: "%s"'%uniqueQuestionLabel)
		return ['','']
	labelParts = uniqueQuestionLabel.split('_')
	try:
		part1 = labelParts[1]
		try:
			questionRecNum = int(part1)
		except ValueError:
			questionRecNum = 'ValueXError'
	except IndexError:
		questionRecNum = 'xxx'
		msgOut.append('decodeQuestionResponseLabel:  Index of part 1 out of range')
	try:
		part2 = labelParts[2]
		if part2:
			try:
				responseChoiceRecNum = int(part2)
			except ValueError:
				responseChoiceRecNum = 'ValueYError'
		else:
			responseChoiceRecNum = ''
	except IndexError:
		responseChoiceRecNum = ''
		msgOut.append('decodeQuestionResponseLabel:  Index of part 2 out of range')
	for aMess in msgOut:
		DebugOut(aMess)
	return [questionRecNum,responseChoiceRecNum]

def MakeUniqueKeyToTagDict(thePageQuestions):
	"""Create dictionary for converting from Unique key to Question.shortTag
	Some functions:  saveGlobalFlagsToSessionData, 
	require the original Question.shortTag to be associated with the
	question response.
	"""
	UtoTdict = {}
	for aQuestion in thePageQuestions:
		theQRecNum = str(aQuestion.id)
		theQLabel = encodeQuestionResponseLabel(theQRecNum,'')
		theQTag = aQuestion.questionTag
		UtoTdict.update({theQLabel:theQTag})
		choiceCount = ResponseChoice.objects.filter(questionID=aQuestion).count()
		if choiceCount > 0:
			# multiple choice question.
			theResponses = ResponseChoice.objects.filter(questionID=aQuestion)
			for aResponse in theResponses:
				theChoiceRecNum = str(aResponse.id)
				choiceText = aResponse.choiceText
				choiceType = aResponse.choiceType
				choiceTag = aResponse.choiceTag
				theQResponseLabel = encodeQuestionResponseLabel(theQRecNum,theChoiceRecNum)
				UtoTdict.update({theQResponseLabel:choiceText})
	return UtoTdict

def replaceUniqueKeysWithDBQuestionTags(questionResponses, thePageQuestions):
	"""Replaces the Unique key with local keys. The result, limited to the page, is unique and not null
	Note:  keep this logic the same is as in UserDynamicFormCreation
	Args:
		questionResponses:  dictionary of question responses:  key word, key value
		thePageQuestions:  query set or list of pages
	Returns:
		questionResponsesWithTags:  unique key names in dictionary questionResponses,
			with new key names from the question record
	"""
	DebugOut('replaceUniqueKeysWithDBQuestionTags:  enter')
	UtoTdict = MakeUniqueKeyToTagDict(thePageQuestions)
	
	questionResponsesWithTags = {}
	ii = 1
	tagKeyList = [] # accumulate the encountered tags
	for uniquekey, keyValue in questionResponses.iteritems():
		# Change the unique key.
		DebugOut('uniquekey: "%s",keyValue: "%s"'%(uniquekey, keyValue))
		DebugOut('Data type of keyValue "%s"'%type(keyValue))
		tagKey = UtoTdict[uniquekey]
		if tagKey == '':
			tagKey = 'QuestionTag_' + str(ii)
		if tagKey in tagKeyList: # if already in the list
			tagKey = tagKey + "_" + str(ii) # force the tag to be unique
		tagKeyList.append(tagKey)
		questionResponsesWithTags.update({tagKey:keyValue})
		ii+=1
	DebugOut('replaceUniqueKeysWithDBQuestionTags:  exit')
	return questionResponsesWithTags
	
def UserDynamicFormCreation( thePageQuestions, formData, useQuestionTag=False):
	"""Create a form for a set of Questions in a query set.
	
	Args:
		allQuestions: a query set containing questions
		
	returns:
		aForm: a form with the questions and response choices  (if any)
	"""
	DebugOut('UserDynamicFormCreation:  enter')
	DebugOut('formData: %s'%formData)
	if formData == ['']:
		formData = None # "None" is acceptable input.
		DebugOut('UserDynamicFormCreation: no forms data input (ok)')
	else:
		DebugOut('UserDynamicFormCreation: has forms data input')

	multCount=0 # count 'MultipleChoiceField' to flag an error if there is more than one
				# at the moment, can handle only one "multiple choice' field.
				# This might make the best sense from the user interface point of view as well.
	questionList = [] # each element of the List is a dictionary
	ii = 0
	labelList = [] # accumulate a list of tags to make sure they are unique on the page
	qustionTagToRecordNum = {} # tag to record number translation for Question
	choiceTagToRecordNum = {} # tag to record number translation for ResponseChoice
	for aQuestion in thePageQuestions:
		ii+=1
		theQRecNum = str(aQuestion.id) # used as a label, so string is needed
		if useQuestionTag: # use short tag if it is non-null
			if aQuestion.questionTag: 
				theQLabel = aQuestion.questionTag
				if theQLabel in labelList:
					theQLabel = theQLabel+'_'+ str(ii)
			else: # tag is null. Invent a tag. Use the same logic as in replaceUniqueKeysWithDBQuestionTags
				theQLabel = 'QuestionTag_' + str(ii)
		else:
			theQLabel = encodeQuestionResponseLabel(theQRecNum,'') # creates a unique label
		labelList.append(theQLabel)
		qustionTagToRecordNum.update({theQLabel:aQuestion.id})
		# save to object with substitutions
		updatedQuestionText = SubstituteWords(aQuestion.questionText)
		questionList.append({
			'questionTag':aQuestion.questionTag,
			'responseType':aQuestion.responseType,
			'questionText':updatedQuestionText,
			'theQLabel':theQLabel,
			})
		# Note:  do not "save" aQuestion!!
		DebugOut('aQuestion record number: "%s"' %aQuestion.id)
		DebugOut('aQuestion.questionTag1: "%s"' %aQuestion.questionTag)
		DebugOut('aQuestion.responseType2: "%s"' %aQuestion.responseType)
		DebugOut('aQuestion.questionText3: "%s"' %smart_str(aQuestion.questionText))
		DebugOut('updatedQuestionText4: "%s"' %smart_str(updatedQuestionText))
		DebugOut('theQLabel5: "%s"' %theQLabel)
		# are there multiple responses??
		responseCount = ResponseChoice.objects.filter( questionID=aQuestion).count()
		if responseCount >0:
			# query for the multiple choices for a specific question tag
			theResponseChoices=ResponseChoice.objects.order_by('choiceSequence').filter( questionID=aQuestion)
			DebugOut('Choices follow:')
			multCount=multCount+1 # allowed only one multiple choice question per page, so count them
			choiceList = []
			for aChoice in theResponseChoices:
				ii+=1
				theChoiceTextTemp = aChoice.choiceText
				theChoiceText = SubstituteWords(theChoiceTextTemp)
				theChoiceRecNum = str(aChoice.id) # used as a label, so string is needed
# 				if useQuestionTag: # use short tag if it is non-null
# 					if aChoice.choiceTag: 
# 						theChoiceLabel = aChoice.choiceTag
# 						if theChoiceLabel in labelList:
# 							theChoiceLabel = theChoiceLabel+'_'+ str(ii)
# 					else: # tag is null. Invent a tag. Use the same logic as in replaceUniqueKeysWithDBQuestionTags
# 						theChoiceLabel = 'ChoiceTag_' + str(ii)
# 				else:
# 				theChoiceLabel = encodeQuestionResponseLabel(theQRecNum,theChoiceRecNum) # creates a unique label
				theChoiceLabel = theChoiceText # bigChange!
				labelList.append(theChoiceLabel)
				choiceTagToRecordNum.update({theChoiceLabel:aChoice.id})
				DebugOut('Choice tag: '+aChoice.choiceTag+' Choice Text: '+theChoiceText)
				DebugOut('Choice label: '+theChoiceLabel)
				choiceList.append( [theChoiceLabel , theChoiceText])
			DebugOut('End Choices')
	if multCount == 1:
		DebugOut('Choices end. Count: %s' %str(len(choiceList)))
		DebugOut('choiceList: %s' %choiceList)
		aForm = UserFormPoly(formData, questions=questionList, choices=choiceList)
	elif multCount > 1:
		DebugOut('Error: too many multichoice: %s. All questions will get the same choices (the last one).' %str(multCount))
#		aForm = '' # will crash at return
	elif multCount == 0:
		DebugOut('UserDynamicFormCreation:  No choiceList for this question (ok)')
		aForm = UserFormPoly(formData, questions=questionList)
	DebugOut('UserDynamicFormCreation:  exit')
	return [aForm, qustionTagToRecordNum,choiceTagToRecordNum]
	
def SubstituteWords( inputText ):
# 	DebugOut('SubstituteWords: enter')
# 	DebugOut('inputText %s' %inputText)
	explainURLprefix = settings.WSGI_URL_PREFIX + 'multiquest/explanations/' # backward compatibility! for Explanations ***

	outputText = inputText.replace('{{explainURLprefix}}', explainURLprefix) # returns input string if no replacement
# 	DebugOut('outputText %s' %outputText)
# 	DebugOut('SubstituteWords: exit')
	return outputText

def scrnrexpln(request, whichpage): #all explanations
	# click to an explanation screen, then back to the calling page
	DebugOut('scrnrexpln:  enter')
	computerT = computertype(request) # identify computer type
	dynamicPageDetails = pagePerComputer(computerT)
	fontSize = dynamicPageDetails['fontSize']
	fontSizeTextBox = dynamicPageDetails['fontSizeTextBox']
	if 'pageBaseURL' in request.session:
		DebugOut('in request session')
		pageBaseURL = request.session['pageBaseURL']
		back_to_temp = UpdateLast_URL_Back(request, whichpage)
		if back_to_temp:
			DebugOut('back_to_temp %s' %back_to_temp)
			back_to = pageBaseURL + back_to_temp
			DebugOut('back_to %s' %back_to)
		else: # no sensible "back to" page. Go back to questionnaire selection.
			back_to = questionnaireSelectionPage
			DebugOut('questionnaireSelectionPage %s' %questionnaireSelectionPage)
	else:
		back_to = questionnaireSelectionPage
		DebugOut('no request session, questionnaireSelectionPage %s' %questionnaireSelectionPage)
	
	if request.method == 'POST':
		if request.POST['submitButton'] == 'Back':
			DebugOut( 'BACK button clicked')
			DebugOut( 'Return destination is: %s' %back_to)
			return HttpResponseRedirect(back_to)
	
	DebugOut( 'In scrnrexpln. whichpage: %s, back_to: %s' %(whichpage,back_to))
	contextDict = {
		'back_to' : back_to,
		'fontSize' : fontSize,
		'fontSizeTextBox' : fontSizeTextBox,
		'imageloc' : settings.MEDIA_URL,
		}
	if whichpage == 'ashkenazijewishrelatives':
		return render(request, 'Explanations/ashkenazijewishrelatives.html', contextDict)
	if whichpage == 'brcatesting':
		return render(request, 'Explanations/brcatesting.html', contextDict)
	if whichpage == 'closebloodrelatives':
		return render(request, 'Explanations/closebloodrelatives.html', contextDict)
	if whichpage == 'moreonbreastca':
		return render(request, 'Explanations/moreonbreastca.html', contextDict)
	if whichpage == 'ovca':		
		return render(request, 'Explanations/ovca.html', contextDict )
	if whichpage == 'skininbreastca':
		return render(request, 'Explanations/skininbreastca.html', contextDict)
	# if none of the above, return to the general explanations page.
	DebugOut('scrnrexpln:  exit')
	return render(request, 'Explanations/explanations.html', contextDict)
	
def UpdateLast_URL_Next(request, this_page):
	"""Records current page tag.
	
	Purpose:  enable the "Back" button by recording sequence of visited page tags.
	
	Args:
		request
		this_page:  page shortTag

	Returns:
		None.
		
	Side effects:
		modifies request.session['last_url']
		
	Raises:
		None.
	"""
# 	DebugOut('UpdateLast_URL_Next: enter')
# 	DebugOut('this_page: %s'%this_page)
	if 'last_url' in request.session:
# 		DebugOut('Length: %s'%len(request.session['last_url']))
		if len(request.session['last_url']) > 0: # detect immediate duplicates
			if request.session['last_url'][-1] == this_page:
				request.session['last_url'].pop()	# assume the previous page is different from this page
		request.session['last_url'].append(this_page) # records this url visited.
	else:
		request.session['last_url'] = [this_page]
	
	request.session.modified = True	# save the session changes
# 	DebugOut('UpdateLast_URL_Next: exit')
	return True
	
def UpdateLast_URL_Back(request, this_page):
	# records this_page and returns previous page in stack
	#DebugOut('UpdateLast_URL_Back: enter')
	#DebugOut('this_page: %s'%this_page)
	if 'last_url' in request.session:
		#DebugOut('last_url in session')
		#DebugOut('print the url list. Length: %s'%len(request.session['last_url']))
		for aurl in request.session['last_url']:
			print 'url: %s' %aurl
		if len(request.session['last_url']) > 0: # detect immediate duplicates
			#DebugOut('immediate duplicate')
			if request.session['last_url'][-1] == this_page:
				#DebugOut('pop the last page: %s'%this_page)			
				request.session['last_url'].pop()	# assume the previous page is different from this page
		if len(request.session['last_url']) == 0:
			back_to = ''
			#DebugOut('back into the void')
			request.session['last_url'].append(this_page) # records this url visited.
		else: # List has 1 or more entries
			back_to = request.session['last_url'][-1]
			#DebugOut('normal back to: %s'%back_to)
	else:
		back_to = ''
		#DebugOut('back into the void 2')
		request.session['last_url'] = [this_page]
	
	request.session.modified = True	# save the session changes
	#DebugOut('UpdateLast_URL_Back: exit')
	
	return back_to
	
def dumpSessionData(request):
	DebugOut('dumpSessionData: enter')
		
	if request.method == 'POST':
		if 'flushSessionData' in request.POST:
			request.session.flush() # =========== flush Session data ========================

	sessionDataDump = []
	for kn, kv in request.session.items():
		lineOut = kn+':  '+unicode(kv)
		sessionDataDump.append(lineOut)
	if sessionDataDump == []:
		sessionDataDump = False # no session data

	contextDict = {
		'sessionDataDump' : sessionDataDump,
		'url_base' : url_base,
		'back_to_intro' : 'Return to the Introduction Page',
		}
	DebugOut('dumpSessionData: exit')
	return render(request, 'working_pages/sessionDataView.html',contextDict )

def questionnaireToGo(request, theProject, theQuestionnaire):
	"""Prepare the Session Data for questionnaire execution.
	Provide the url.
	Note:  see function "removeResponsesFromSessionData"
	Note:  see function "questionnaireEnvironmentPrep"
	Args:
		"request" input

	Returns:
		pageBaseURL - fully qualified url for prefix to page short tag

	Session Data:
		Sets session data:
			'pageBaseURL'
	
	Raises:
		None.
	"""
	errMsg = []
	pageBaseURL = questionnaireEnvironmentPrep( request, theProject, theQuestionnaire)
	
	# find the first page of the questionnaire and add to the URL
	# retrieve the "first page" from Questionnaire.
	firstPageObj = getStartPageObj(theQuestionnaire)
	if firstPageObj:
		firstPageInQuestTag = firstPageObj.shortTag
		urltogo = pageBaseURL + firstPageInQuestTag
	else:
		urltogo = pageBaseURL
		errMsg.append('Questionnaire "%s" has no defined start page.'%theQuestionnaire.shortTag)

	return urltogo # next screen url

def questionnaireEnvironmentPrep( request, theProject, theQuestionnaire):
	"""Prepare the Session Data for questionnaire execution.
	Note:  see function "removeResponsesFromSessionData"
	Note:  see function "questionnaireToGo"
	Args:
		"request" input

	Returns:
		pageBaseURL - fully qualified url for prefix to page short tag

	Session Data:
		Sets session data:
			'pageBaseURL'
	
	Raises:
		None.
	"""
	DebugOut('questionnaireEnvironmentPrep:  enter')
	# The following is where pages are identified by record from the url.
	setSessionQuestionnaireProject(request, theProject, theQuestionnaire)
	setSessionPageTagToRecord(request, theQuestionnaire)

	whichQuest = theQuestionnaire.shortTag
	spObj = getProjectObjForQuestionnaire(theQuestionnaire)
	if spObj:
		whichProject = spObj.shortTag
	else:
		whichProject = '' # will be an error condition
	pageBaseURL = settings.WSGI_URL_PREFIX + 'multiquest/' + whichProject+'/'+whichQuest+'/'
	# save this page as the default page to return to in case of error
	request.session['pageBaseURL'] = pageBaseURL
	# Store unchanging page data into Session data
	constantPageDataDict = {
		'barTitle' : theQuestionnaire.barTitle, 
		'pageTitle' : theQuestionnaire.pageTitle, 
		'pageSubTitle' : theQuestionnaire.pageSubTitle,
		'footerText' : theQuestionnaire.footerText,
		'version' : theQuestionnaire.version,
		'versionDate' : str(theQuestionnaire.versionDate),
		'imageloc' : settings.MEDIA_URL, 
		'pageBaseURL' : pageBaseURL,
		'urlprefix' : settings.WSGI_URL_PREFIX, # backward compatibility! for Explanations
		'debugMode' : settings.DEBUG } # refers to DEBUG in settings.
	# save constant portion of context
	request.session['constantPageDataDict'] = constantPageDataDict
	DebugOut('questionnaireEnvironmentPrep:  exit')
	return pageBaseURL
	
def splash(request, whichProject, whichQuest): #Select questionnaire, Check for cookie function. Start session.
	DebugOut('splash: enter')
	now = timezone.now()
	DebugOut('whichProject %s, whichQuest %s' %(whichProject,whichQuest))
	
	# Standard verification w.r.t. project and questionnaire
	[theProject, theQuestionnaire, errMess] = verifyQuestionnaireProject(request, whichProject, whichQuest)
	if errMess != []:
		DebugOut('test %s' %str(errMess))
		# last ditch effort.
		theProject = getProjectObj( whichProject) # query the database
		theQuestionnaire = getQuestionnaireObjFromTags(whichProject, whichQuest)
		if not theProject or not theQuestionnaire:
			return render(request, 'system_error.html', {'syserrmsg': errMess})
		else:
			pass
			# set up environment
			pageBaseURL = questionnaireEnvironmentPrep( request, theProject, theQuestionnaire)
			# continue without error
		
	this_page = "splash"
	
	# have sufficient information to display the page.	
	# Standard page object retrieval
	[thePageObj, success] = getPageObj(theQuestionnaire, this_page)
	if not success:
		errMsg=['Could not find a page transition for %s'%this_page]
		return render(request, 'system_error.html', {'syserrmsg': errMess})
	
	prologue = SubstituteWords( thePageObj.prologue )
	epilogue = SubstituteWords( thePageObj.epilogue )
	explanation = SubstituteWords( thePageObj.explanation )

	request.session.set_test_cookie() # Set test cookie to test in next POST
	pageBaseURL = request.session['pageBaseURL']
	constantPageDataDict = request.session['constantPageDataDict']

	computerT = computertype(request) # identify computer type
	dynamicPageDetails = pagePerComputer(computerT)
	fontSize = dynamicPageDetails['fontSize']
	fontSizeTextBox = dynamicPageDetails['fontSizeTextBox']

	
	now = timezone.now()
	# create context for current page
	contextDict = {'current_date' : now,
		'explanation' : explanation,
		'prologue' : prologue,
		'epilogue' : epilogue, 
		'field_style' : '', # no field display at all
		'fontSize' : fontSize,
		'fontSizeTextBox' : fontSizeTextBox,
		'back_not_enabled' : True
		}

	if request.method == 'POST':
# 		if not request.session.test_cookie_worked(): # check for cookie function
# 			currentContext = constantPageDataDict.copy()
# 			currentContext.update(contextDict)
# 			currentContext.update({'errmsg': 'Please enable cookies in your browser.'})
# 			return render(request, 'generic_page.html', currentContext)
		# add logic for 'Back' button - remove it?? ****
		UpdateLast_URL_Next(request, this_page) # ignore 'back to' output
		next_pageObj = pageCalc(request,theQuestionnaire, thePageObj)
		next_page = next_pageObj.shortTag
		theNextURL = pageBaseURL +next_page
		DebugOut('splash: theNextURL %s' %theNextURL)
		DebugOut('splash: exit to page %s' %next_page)
		return HttpResponseRedirect(theNextURL)

	currentContext = constantPageDataDict.copy()
	currentContext.update(contextDict)
	DebugOut('splash:  exit')
	return render(request, 'generic_page.html',currentContext )
	




