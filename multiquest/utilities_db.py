from multiquest.models import *
from multiquest.utilities import *
from django.utils.encoding import smart_text
from django.shortcuts import render_to_response, render, get_object_or_404
import pickle
from django.db.models import Q
from operator import itemgetter, attrgetter # used for sorting & selecting from a list
from collections import Counter



	# save the value of global flags saved to session data
# 	allGlobalFlags = listAllGlobalFlags(workingQuestionnaire)

def getAllUsers():
	"""Return User objects belonging to group "Student".
	Args:
		none
	Returns:
		User objects belonging to Student
	
	Database:
		Uses (not set): PageAnalysis

	Raises:
		None
	"""
	try:
		thisGroup = Group.objects.get(name="Student")
		allMembs=User.objects.filter(groups=thisGroup)
	except Group.DoesNotExist:
		allMembs = None
	return allMembs
	

def saveGlobalFlagsToSessionData(request, theQuestionnaire, thePageObj, questionResponses):
	"""Create a global flag when a testCondition attached to the page matches
	questionResponses
	Args:
		request:  HttpRequest request object
		theQuestionnaire:  Questionnaire object
		thePageObj:  page object
		questionResponses:  Form output for questions
	Returns:
		sessionDataCreated: True when global flag set in Session data
	
	Database:
		Uses (not set): PageAnalysis

	Raises:
		None
	"""
	# consult PageAnalysis. .
	# reads global flag and condition from PageAnalysis
	# writes global flag to Session data, if not already there
	DebugOut('saveGlobalFlagsToSessionData:  enter')
	DebugOut('page %s Questionnaire: %s' %(thePageObj.shortTag,theQuestionnaire.shortTag) )
	DebugOut('questionResponses "%s"' %questionResponses)
	DebugOut('questionResponses type "%s"' %type(questionResponses))

	pageAnalysisRecords = PageAnalysis.objects.filter( # allow for multiple results
		questionnaireID = theQuestionnaire,
		pageID=thePageObj,
		)
	DebugOut('successful query')
	if len(pageAnalysisRecords) == 0:
		DebugOut('No analysis records found for page "%s" therefore no global flag added to Session Data.'%thePageObj.shortTag)
		sessionDataCreated = False
		DebugOut('saveGlobalFlagsToSessionData:  exit')
		return sessionDataCreated # no session data to create! So exit
	# accumulate the test conditions and flags in a dictionary with test condition as key
	testCondDict = {}
	for apageAnalysisRecords in pageAnalysisRecords:
		theTC = apageAnalysisRecords.testCondition
		theTCResultFlag = apageAnalysisRecords.testResultFlag
		testCondDict.update({theTC : theTCResultFlag})
		DebugOut('Test conditon: "%s", Global Flag to set: %s' %(theTC,theTCResultFlag ))
		
	DebugOut('Obtained test condition and global flag')
		
	sessionDataCreated = False # pessimism
	if pageAnalysisRecords:
		# testCondition is retrieved as a string from PageAnalysis
		# questionResponses enters as a dictionary, so convert to string
		# sort first
		TCInput = str(sorted(questionResponses.items()))
		DebugOut('TCInput "%s"' %TCInput)
		if TCInput in testCondDict:
			DebugOut('testCondition1 is in PageAnalysis for this page "%s"' %TCInput)
			globalFlagName = testCondDict[TCInput]
			DebugOut('globalFlagName "%s"' %globalFlagName)
			if 'pageGlobalFlags' in request.session:
				if globalFlagName not in request.session['pageGlobalFlags']:
					request.session['pageGlobalFlags'].append(globalFlagName)
					sessionDataCreated = True
					DebugOut('Add Global flag to session data %s' %globalFlagName)
				else:
					DebugOut('Global flag already in session data')
					# else already included in the list. Do not duplicate
			else: # create first entry in list
				DebugOut('Global flag %s first entry in session data' %globalFlagName)
				request.session['pageGlobalFlags'] = [globalFlagName]
				sessionDataCreated = True
		elif 'anySelectedButton' in testCondDict:
			DebugOut('testCondition2 "%s"' %'anySelectedButton')
			globalFlagName = testCondDict[str('anySelectedButton')]
			DebugOut('globalFlagName "%s"' %globalFlagName)
			# Must be multiple choice question or the following will fail
			if questionResponses.values() == [[]]:
				DebugOut('anySelectedButton: null, therefore flag not set')
			else:
				DebugOut('anySelectedButton: not null, therefore flag is set')
				request.session['pageGlobalFlags'] = [globalFlagName]
				sessionDataCreated = True
		elif 'noneSelectedButton' in testCondDict:
			DebugOut('testCondition3 "%s"' %'noneSelectedButton')
			globalFlagName = testCondDict[str('noneSelectedButton')]
			DebugOut('globalFlagName "%s"' %globalFlagName)
			# Must be multiple choice question or the following will fail
			if questionResponses.values() == [[]]:
				DebugOut('noneSelectedButton: null, therefore flag is set')
				request.session['pageGlobalFlags'] = [globalFlagName]
				sessionDataCreated = True
			else:
				DebugOut('noneSelectedButton: not null, therefore flag is not set')
			
		elif 'anyYesButton' in testCondDict:
			DebugOut('testCondition4 "%s"' %'anyYesButton')
			globalFlagName = testCondDict[str('anyYesButton')]
			DebugOut('globalFlagName "%s"' %globalFlagName)
			DebugOut('questionResponses.values() %s' %questionResponses.values())
			# Find 'Yes" in the multiple responses.
			if 'Yes' in questionResponses.values():
				# set the global response
				DebugOut('anyYesButton: a "Yes" found, therefore flag is set')
				request.session['pageGlobalFlags'] = [globalFlagName]
				sessionDataCreated = True
		else: # test conditions not propitious for flag setting
			DebugOut('Test condition type does not match any known type (ok).') # ok
	else:
		DebugOut('Exists no PageAnalysis record for this page (ok)') # ok
		
	DebugOut('saveGlobalFlagsToSessionData:  exit')
	return sessionDataCreated

	return theQueryset
def getNextPageFromGlobalFlags(request, theQuestionnaire, pageObj):
	# returns "next page", if a flag is in session data.
	# Finds next page object from QuestionnairePage
	# Simple existence specifies the next page via QuestionnairePage
	DebugOut('getNextPageFromGlobalFlags:  enter')
	recordType = 'globalFlag'
	DebugOut('pageTag:  %s' %pageObj.shortTag)
	qpPoly = QuestionnairePage.objects.filter( # Might be multiple flags for a page. Priority determines
		questionnaireID = theQuestionnaire,
		pageID=pageObj,
		recordType = recordType,
		)
	if len(qpPoly) == 0: # no global flags, normal behavior
		# normal behavior.
		DebugOut('No global flag applies to this page transition. (Normal)')
		nextPageObj = Page()
		pageTransitionPresent = False
		return [nextPageObj, pageTransitionPresent]

	# make a list of global flags which this page responds to
	gFlagsThisPage = []
	for aQP in qpPoly:
		myGlobalFlagName = aQP.testCondition
		myGlobalFlagNameNextPage = aQP.nextPageID
		DebugOut('globalFlagName "%s" transitions to page "%s"' %(myGlobalFlagName,myGlobalFlagNameNextPage.shortTag))
		gFlagsThisPage.append([myGlobalFlagName,myGlobalFlagNameNextPage])

	DebugOut('Number of global flags (%s) apply to page "%s"' %(len(gFlagsThisPage),pageObj.shortTag))

	# Does the globalFlagName match any flag in session data? If so, transition to next page.	

	# retrieve all flags from session data
	if 'pageGlobalFlags' in request.session:
		DebugOut('Checking global flags in session data')
		allGlobalFlagsInSession = request.session['pageGlobalFlags']
		DebugOut('allGlobalFlagsInSession: %s' %allGlobalFlagsInSession)
		myFlagsAndPriority = []
		for myFlag in gFlagsThisPage:
			myFlagName = myFlag[0]
			myFlagNextPageObj = myFlag[1]
			DebugOut('myFlagName: %s' %myFlagName)
			DebugOut('myFlagNextPageobj: %s' %myFlagNextPageObj.shortTag)
			if myFlagName in allGlobalFlagsInSession:
				[myFlagPriority, myFlagDescription, success] = getGlobalFlagPriority(theQuestionnaire,myFlagName)
				# do nothing with myFlagDescription
				myFlagsAndPriority.append([myFlagName,myFlagNextPageObj,myFlagPriority])
				DebugOut('Got a hit for global flag "%s" (priority %s), the next page is %s' %(myFlagName,myFlagPriority,myFlagNextPageObj.shortTag))
		if len(myFlagsAndPriority) == 0:
			DebugOut('no hit for global flags in session data')
			nextPageObj = Page()
			pageTransitionPresent = False
		else: # got a hit! Select the highest priority flag
			DebugOut('got a hit! Select the highest priority flag')
			myFlagsAndPrioritySorted = sorted(myFlagsAndPriority,key=lambda aRec: aRec[2]) # sort on the priority column
			# take the first, the highest priority. Select first in sorted record (highest priority)
			highestPriorityFlag = myFlagsAndPrioritySorted[0][0] # 0 element is flag name
			nextPageObj = myFlagsAndPrioritySorted[0][1] # 1 element is next page object
			pageTransitionPresent = True
	else:
		# otherwise no global flags set into Session Data yet.
		DebugOut('no global flags set yet')
		nextPageObj = Page()
		pageTransitionPresent = False
			
	DebugOut('getNextPageFromGlobalFlags: exit')
	return [nextPageObj, pageTransitionPresent]

def getNextPageFromCalculation(theQuestionnaire, thePageObj, testConditionInput):
	# get the next page which matches the test condition
	DebugOut('getNextPageFromCalculation: enter')
	sortedResults=str(sorted(testConditionInput.items())) # get the list in standard order
	DebugOut('Test condition: %s' %sortedResults)
	DebugOut('Questionnaire record %s'%theQuestionnaire.id)
	DebugOut('Page record %s'%thePageObj.id)
	recordType = 'calculated'
	qpObjs = QuestionnairePage.objects.filter(
		questionnaireID = theQuestionnaire,
		pageID=thePageObj,
		recordType = recordType,
		)
	# extract multiple saved page conditions
	nextPageObj = None # pessimism
	for (ii, qp) in enumerate(qpObjs): # check for page condition match
		if sortedResults == qp.testCondition:
			DebugOut('Test condition (%s) matches: "%s"'%(ii+1,qp.testCondition))
			nextPageObj = qp.nextPageID # a match, so set the next page
			success = True
		else:
			DebugOut('Test condition does not match %s: "%s"'%(ii,qp.testCondition))
			pass
	if not nextPageObj:
		DebugOut('Found no match')
	DebugOut('getNextPageFromCalculation: exit')
	return nextPageObj


# ====================================================================================
# ====================================================================================
# Defines Session Data objects
# ====================================================================================
# ====================================================================================
def setSessionQuestionnaire(request, theQuestionnaire):
	"""Set Questionnaire record number into Session data.
	"""
	request.session['theQuestionnaire'] = theQuestionnaire.id

	return True

def getSessionQuestionnaire(request):
	"""Get Questionnaire object defined in Session data.
	"""
	if 'theQuestionnaire' in request.session:
		theQuestionnaireid = request.session['theQuestionnaire']
	else:
		return None
		
	try:
		theQuestionnaire = Questionnaire.objects.get(id=theQuestionnaireid)
	except Questionnaire.DoesNotExist:
		theQuestionnaire = None
	return theQuestionnaire

def setSessionProject(request, theProject):
	"""Set Project record number into Session data.
	"""
	request.session['theProject'] = theProject.id

	return True

def getSessionProject(request):
	"""Get Project object defined in Session data.
	"""
	if 'theProject' in request.session:
		theProjectid = request.session['theProject']
	else:
		return None
	try:
		theProject = Project.objects.get(id=theProjectid)
	except Project.DoesNotExist:
		theProject = None
	return theProject

def setProjectForQuestionnaire(theProject, theQuestionnaire):
	""" Sets the project associated with the Questionnaire in the ProjectQuestionnaire table.
	"""
	# delete prior associations.
	ProjectQuestionnaire.objects.filter(questionnaireID=theQuestionnaire).delete()
	# add the current record.
	ProjectQuestionnaire.objects.create(
		questionnaireID=theQuestionnaire,
		projectID=theProject,
		recordType='connection',
		questionnaireStatus='enabled',
		)
	return True
	
def setSessionQuestionnaireProject(request, theProject, theQuestionnaire):
	"""Set Questionnaire and Project defaults.
	Set non-null Questionnaire objects into Session data and set Project object defaults.
	"""
	request.session['theProject'] = theProject.id

	if theQuestionnaire: # has a non-null value
		request.session['theQuestionnaire'] = theQuestionnaire.id
		
	return True

def setSessionLimitViewProjectSetting(request, theSetting):
	"""Set flag value in Session data.
	Where applicable, this limits the user display to Questionnaires only in
	the default Project for the User.
	"""
	request.session['QuestionnaireViewLimitedToDefaultProject'] = theSetting
	return True
	
def getSessionLimitViewProjectSetting(request):
	"""Get flag value in Session data.
	Where applicable, this limits the user display to Questionnaires only in
	the default Project for the User.
		"None" indicates not set in Session Data.
	"""
	theSetting = request.session.get('QuestionnaireViewLimitedToDefaultProject',True)
	
	return theSetting

def removeResponsesFromSessionData(request):
	"""Remove questionnaire responses from Session Data.
	
	Purpose:  Preserve personal privacy between questionnaire executions
	Note:  see function "questionnaireEnvironmentPrep"
	Note:  see function "questionnaireToGo"
	Args:
		Questionnaire object
		Page Tag:  character string

	Returns:
		a Dict object. from page : to page	

	Raises:
		None.
	"""
	if 'currentRespondent' in request.session:
		del request.session['currentRespondent']
	if 'respondentIDInfo' in request.session:
		del request.session['respondentIDInfo']
	if 'questionnaireResultsList' in request.session:
		del request.session['questionnaireResultsList']
	if 'questionnaireResults' in request.session:
		del request.session['questionnaireResults']
	if 'summaryPageContext' in request.session:
		del request.session['summaryPageContext']
	if 'pageGlobalFlags' in request.session:
		del request.session['pageGlobalFlags']
	if 'pageTagToRecord' in request.session:
		del request.session['pageTagToRecord']
	if 'summaryPagehtml' in request.session:
		del request.session['summaryPagehtml']
	if 'last_url' in request.session:
		del request.session['last_url']
	if 'FselectProjectDefault' in request.session: # should be temporary to selectProjectDefault!
		del request.session['FselectProjectDefault']
		
	for kk in request.session.keys():
		if str(kk).startswith('HavePageResults_'):
			del request.session[kk]
	
	return
	

# ====================================================================================
# ====================================================================================
# Defines "editable" objects:  projects, questionnaires, pages, questions.
# may have submissions against, but there exists a page tag with a later last edit date
# project tags are unique, other records with same tag are earlier edits
# questionnaire tags are unique within a project
# page tags are unique within a questionnaire
# question tags are unique within a page
# ====================================================================================
# ====================================================================================
def getAllProjects():
	"""Return a QuerySet with all Projects.
	Project edits may create new records with the same tag, so that Project short tags
	may not be unique. For each unique short tag, return the latest version of the
	corresponding object.
	
	"Active" project is the record with the latest update with a given tag
	earlier records with the same tag are assumed to be earlier edits.

	Args:
		none.
	Returns:
		a QuerySet containing all Project objects
	Raises:
		No exceptions raised.
	"""
	allProjects = Project.objects.all().order_by('shortTag')
	# Edit this list according to the ProjectAttributes table
	allTags = [ap.shortTag for ap in allProjects] # collect the shortTags into a list
	# make a list of unique tags
	uniqueTags = list(set(allTags))
	# find the latest record belonging to each unique tag
	allRecs = []
	for aTag in uniqueTags:
		allRecs.append(Project.objects.filter(shortTag=aTag).latest('lastUpdate').id)
	# have all record numbers in allRecs. Now make a query set out of it.
	# Could have returned a list of record numbers, but prefer a queryset
	if len(allRecs) == 0: # no Projects, so return empty queryset
		allUniqueProjects = Project.objects.none() # initialize
	else:
		allUniqueProjects = retrieveBulk( Project, allRecs )
	return allUniqueProjects # a queryset

def getAllProjectsWithinScope(): # scope defined in ProjectAttribues table
	"""Return a QuerySet with all Projects within scope allowed by 
	the ProjectAttribues table. Does not determine if the project is the latest!
	
	"Active" project is the record with the latest update with a given tag
	earlier records with the same tag are assumed to be earlier edits.

	Args:
		none.
	Returns:
		a QuerySet containing all Project objects
	Raises:
		No exceptions raised.
	"""
	rawProjects= getAllProjects()
	allIDs = [] # collect the shortTags into a list
	for theProject in rawProjects:
		# get the corresponding Attributes
		theProjectAttributes = getProjectAttributes(theProject)
		if 'Display' in theProjectAttributes:
			allIDs.append(theProject.id)
		elif 'DoNotDisplay' not in theProjectAttributes:
			allIDs.append(theProject.id)
	allUniqueProjects = retrieveBulk( Project, allIDs )
	return allUniqueProjects
	
def getProjectAttributes(theProject):
	"""Return the list of Attributes associated with the Project

	Args:
		none.
	Returns:
		a List containing all Project attribute "keyName"'s
	Database:
		Reads ProjectAttributes
	Raises:
		No exceptions raised.
	"""
	allAttributeRecs = ProjectAttributes.objects.filter(projectID=theProject)
	allAttributes = [aRec.keyName for aRec in allAttributeRecs]
	return allAttributes

def getAllProjectTags():
	"""Return a list with all Project shortTags.

	returns a queryset

	Args:
		none.
	Returns:
		a list containing all Project shortTags
	Raises:
		No exceptions raised.
	"""
	allSobs = getAllProjects()
	tagList = []
	for anObj in allSobs:
		tagList.append(anObj.shortTag)
	return tagList
	
def getProjectObj( theProjectTag):
	# returns a Project object which has the specified short tag.
	try:
		theProject = Project.objects.filter(
			shortTag=theProjectTag,
			).latest('lastUpdate')
	except Project.DoesNotExist: # return None
		theProject = None
	return theProject

def getAllQuestionnareObjForProject(theProject):
	"""Returns a queryset of questionnaire objects for a given Project object.
	Include all questionnaires in the database.
	"""
	if theProject: # non null Project, require unique Questionnaire shortTags
		# retrieve from ProjectQuestionnaire
		pqObjs = ProjectQuestionnaire.objects.filter(projectID=theProject)
		questRecList = [pqObj.questionnaireID.id for pqObj in pqObjs]
	allQuestionnaires = retrieveBulk( Questionnaire, questRecList )
	return allQuestionnaires
	
def getQuestionnaireObjsForProject(theProject):
	"""Returns a queryset of questionnaire objects for a given Project object.
	Include questionnaires which have a null Project name.
	Companion to: getProjectObjForQuestionnaire.
	"""
	if theProject: # non null Project, require unique Questionnaire shortTags
		# retrieve from ProjectQuestionnaire
		pqObjs = ProjectQuestionnaire.objects.filter(projectID=theProject)
		questRecList = [pqObj.questionnaireID.id for pqObj in pqObjs] # build questionnaire record list
	if len(questRecList) == 0: # no records exist
		allActiveQuestionnaires = Questionnaire.objects.none() # initialize, but with zero content
	else:
		# build a queryset with all the records found
		allActiveQuestionnaires = retrieveBulk( Questionnaire, questRecList )
	return allActiveQuestionnaires

def getQuestionnaireTagsForProject(theProject):
	"""Returns a sorted list of questionnaire shortTags for a given Project object.
	Include questionnaires which have a null Project name.
	"""
	qsForProject = getQuestionnaireObjsForProject(theProject)
	# for each unique Questionnaire tag, find the questionnaire tag
	theTags = [aQuest.shortTag for aQuest in qsForProject] # don't test for uniqueness
	theTags.sort()
	return theTags

def getAllQuestionnaires():
	"""Returns a QuerySet with all questionnaires referenced by projects.
	
	Questionnaires with the same shortTag, but different Projects are
	returned as separate objects.
	
	Questionnaires belonging to a Project will have unique short tags.
	
	Questionnaires not belonging to a Project (Project = None) are not returned.

	Args:
		None
	
	Returns:
		Query object with all questionnaires 	
	
	Raises:
		No exceptions raised.
	"""
	DebugOut('getAllQuestionnaires:  enter')
	# list all of the Questionnaires
	# returns a queryset
	allProjects = getAllProjects()
	# find the list of questionnaires belonging to Projects
	# Allow for sharing of Questionnaires
	allQRecListWdups = []
	for aProject in allProjects:
		qsForProject = getQuestionnaireObjsForProject(aProject)
		recsPerProject = [aQuest.id for aQuest in qsForProject]
		allQRecListWdups.extend(recsPerProject)
	
	# find the list of questionnaires not having a Project
# 	qsForNone = getQuestionnaireObjsForProject(None)
# 	recsPerNone = [aQuest.id for aQuest in qsForNone]
# 	allQRecListWdups.extend(recsPerNone)
	# remove dups
	allQRecList = list(set(allQRecListWdups))
	# build a query with all the records found
	if len(allQRecList) == 0: # no Questionnaires, so return empty queryset
		allActiveQuestionnaires = Questionnaire.objects.none() # initialize
	else:
		allActiveQuestionnaires = retrieveBulk( Questionnaire, allQRecList )
	return allActiveQuestionnaires # a queryset

def getProjectObjForQuestionnaire(theQuestionnaire):
	"""Returns the Project object of a questionnaire.
	Companion to: getQuestionnaireObjsForProject.
	
	Warning, will return only a single project!  ****
	Error **** in the case where the same questionnaire may be shared among two projects
	Only one Project will be selected.
	Args:
		None
	
	Returns:
		Project "shortTag" as a string	
	
	Raises:
		No exceptions raised.
	"""
	# retrieve from ProjectQuestionnaire
	spfromDB = ProjectQuestionnaire.objects.filter(
		questionnaireID=theQuestionnaire,
		recordType = 'connection',
		)
	if spfromDB.count() == 1:
		# Unique, best situation. No problem
		theProject = spfromDB[0].projectID
	elif spfromDB.count() > 1:
		# not unique. Take the first one with a warning
		theProject = spfromDB[0].projectID
		for anSPRec in spfromDB:
			spObj = anSPRec.projectID
			spTag = spObj.shortTag
			spid = spObj.id
			DebugOut('Syserrmsg: getProjectTagForQuestionnaire: Project tag %s, record %s not unique.'%(spTag,spid))
	else:
		theProject = Project()
	return theProject

def	getProjectTagForQuestionnaire(theQuestionnaire):
	"""Returns the short name for the Project of a questionnaire.

	Args:
		None
	
	Returns:
		Project "shortTag" as a string	
	
	Raises:
		No exceptions raised.
	"""
	spfromDB = ProjectQuestionnaire.objects.filter(
		questionnaireID=theQuestionnaire,
		recordType = 'connection',
		)
	if spfromDB.count() == 1:
		# Unique, best situation.
		theProject = spfromDB[0].projectID
	else:
		# not unique. Take the first one with a warning
		theProject = spfromDB[0].projectID
		for anSPRec in spfromDB:
			spObj = anSPRec.projectID
			spTag = spObj.shortTag
			spid = spObj.id
			DebugOut('getProjectTagForQuestionnaire: Project tag %s, record %s not unique.'%(spTag,spid))
	if theProject: # not null
		theShortTag = theProject.shortTag
	else:
		theShortTag = ''
	return theShortTag

def duplicateQuestionnaire(theProject, theQuestionnaire, newShortTag):
	"""Duplicates the entire Questionnaire and all Pages and Questions
	No collisions are detected for the new Questionnaire shortTag
	"""
	DebugOut('duplicateQuestionnaire:  entering')
	DebugOut('theQuestionnaire:  %s'%theQuestionnaire.shortTag)
	DebugOut('newShortTag:  %s'%newShortTag)
	DebugOut('theProject:  %s'%theProject.shortTag)
	newQuestionnaire = duplicateQuestionnaireRecord(theProject, theQuestionnaire, newShortTag)
	
	DebugOut('newQuestionnaire:  %s'%newQuestionnaire.shortTag)
	# Retrieve the Page objects for the Questionnaire
	allPages = getAllPageObjsForQuestionnaire(newQuestionnaire)
	for aPage in allPages:
		DebugOut('Page:  %s'%aPage.shortTag)
		newPage = duplicatePageRecord(newQuestionnaire, aPage)
		pageQuestions = getPageQuestions( newPage)
		for aQuestion in pageQuestions:
			DebugOut('aQuestion:  %s'%aQuestion.questionTag)
			newQuestion = duplicateQuestionRecord(newPage, aQuestion)
			# do nothing with the Question object.
	DebugOut('duplicateQuestionnaire:  exiting')
	return newQuestionnaire

def deleteQuestionnaire(theQuestionnaire):
	"""Deletes the entire Questionnaire and all Pages and Questions referenced by it.
	
	No considerations are given to Submissions pointing to the Questionnaire.
	Args:
		theQuestionnaire:  Questionnaire object to be deleted.
	Database edits:
		All questionnaire objects:
		
	Returns:
	"""
	# get the pages belonging to this questionnaire.
	allPages = getAllPageObjsForQuestionnaire(theQuestionnaire)
	# find questions for each page and delete.
	for aPage in allPages:
		allQuestions=getPageQuestions( aPage)
		for aQuestion in allQuestions:
			aQuestion.delete()
		aPage.delete()
	# and last, the questionnaire
	theQuestionnaire.delete()
	return True

def duplicateQuestionnaireRecord(theProject, theQuestionnaire, newShortTag):
	"""Duplicates the Questionnaire record while maintaining foreign keys:
			to Project	- Creates the Questionnaire object "under" Project
			to Page
			to QuestionnaireAttributes
			to PageAnalysis.
	Assigns a new Questionnaire.shortTag:  newShortTag
	Args:
		theQuestionnaire:  object
		newShortTag:  string which will be theQuestionnaire.shortTag in the new
				Questionnaire
	Database edits:
		Questionnaire
		ProjectQuestionnaire
		PageAnalysis
		QuestionnaireAttributes
	Returns:
		Project "shortTag" as a string	
	
	Raises:
		No exceptions raised.
	"""
	oldQid = theQuestionnaire.id
	theQuestionnaire.id = None # will force a new record
	theQuestionnaire.shortTag = newShortTag # update
	theQuestionnaire.save()
	newQuestionnaire = theQuestionnaire
	oldQuestionnaire = Questionnaire.objects.get(id=oldQid) # restore
	# Create a connection to Project
	ProjectQuestionnaire.objects.create(
		questionnaireID=newQuestionnaire,
		projectID=theProject,
		recordType='connection',
		questionnaireStatus='enabled',
		)
	# Connect old pages to Questionnaire
	allQPRecs = QuestionnairePage.objects.filter(questionnaireID=oldQuestionnaire)
	for aRec in allQPRecs:
		# update and force a new record
		aRec.id=None
		aRec.questionnaireID=newQuestionnaire
		aRec.save()
	# Maintain connection to PageAnalysis
	allPARecs = PageAnalysis.objects.filter(questionnaireID=oldQuestionnaire)
	for aRec in allPARecs:
		# update and force a new record
		aRec.id=None
		aRec.questionnaireID=newQuestionnaire
		aRec.save()
	# Maintain connection to QuestionnaireAttributes
	allQARecs = QuestionnaireAttributes.objects.filter(questionnaireID=oldQuestionnaire)
	for aRec in allQARecs:
		# update and force a new record
		aRec.id=None
		aRec.questionnaireID=newQuestionnaire
		aRec.save()
	return newQuestionnaire
	
def saveQuestionnaireObj(theQuestionnaire):
	"""Save the questionnaire object. Assume this is not a "new" questionnaire, since
	in that case there would never be Submissions against it, and saving would be required.
	update the record if there are no Submissions
	
	Also creates new record when incoming theQuestionnaire.id==None
	"""
	DebugOut('saveQuestionnaireObj:  enter')
	# check Submissions
	countRecs = Submission.objects.filter(
		questionnaireID = theQuestionnaire
		).count()
	idforOld = theQuestionnaire.id
	if countRecs != 0 and idforOld: # there are Submission records point to this Questionnaire
		DebugOut('Submission records are against Questionnaire: "%s"' %theQuestionnaire.shortTag)
		# Require that this questionnaire exist in the database and that this is an update.
		# a submission does exist against the questionnaire.
		# force a duplication of the Questionnaire record upon "save"
		# save old id
		
		theQuestionnaire.id = None
		theQuestionnaire.save()
		# Copy QuestionnairePage records to point to new Questionnaire record
		# first retrieve for old questionnaire
		oldQuestionnaire = Questionnaire.objects.get(id=idforOld)
		qpObjs = QuestionnairePage.objects.filter(questionnaireID=oldQuestionnaire)
		# loop through each, updating the questionnaire object
		for aQP in qpObjs:
			aQP.questionnaireID=theQuestionnaire
			aQP.id=None # force a new record
			aQP.save()
	else:
		DebugOut('NO Submission records are against Questionnaire: "%s", therefore, save the object.' %theQuestionnaire.shortTag)
		theQuestionnaire.save() # No Submissions, so allow save to update record
	DebugOut('saveQuestionnaireObj:  exit')
	return theQuestionnaire

def getQuestionnaireObjFromTags( projectShortTag, questionnaireShortTag):
	"""Returns a Questionnaire object which has the specified project short tag,
	and questionnaire short tag.
	
	Project tag may not be ''
	"""
	errMsg = []
	theProject = getProjectObj( projectShortTag)
	# get all questionnaires with the short tag, belonging to the project
	if theProject:
		allPQRecs = ProjectQuestionnaire.objects.filter(
			questionnaireID__shortTag=questionnaireShortTag,
			projectID=theProject,
			)
	else:
		# There is no project with that shortTag name
		theQuestionnaire = None
		return theQuestionnaire
	if len(allPQRecs) == 0:
		# Project does not contain the named Questionnaire.
		theQuestionnaire = None
		return theQuestionnaire
	allIDs = [aRec.questionnaireID.id for aRec in allPQRecs]
	queryOR = Q(id=allIDs[0])
	for anID in allIDs[1:]:
		queryOR = queryOR | Q(id=anID)
	theQuestionnaire = Questionnaire.objects.filter(queryOR).latest('lastUpdate')
	if not theQuestionnaire: # no questionnaire with the given short tag
		theQuestionnaire = None
	return theQuestionnaire
	
def getQuestionnaireStatusValue(theProject, theQuestionnaire):
	"""Returns the status flag value for the questionnaire.
	Args:
		Questionnaire object: workingQuestionnaire.

	Returns:
		page count (integer)	

	Raises:
		None
	"""
	try:
		pqObj = ProjectQuestionnaire.objects.get(
			projectID=theProject,
			questionnaireID=theQuestionnaire,
			recordType='connection',
			)
		questionnaireStatus = pqObj.questionnaireStatus
	except ProjectQuestionnaire.DoesNotExist:
		questionnaireStatus = ''
	
	return questionnaireStatus

def setQuestionnaireStatusValue(theProject, theQuestionnaire, questionnaireStatus):
	"""Sets the status flag value for the questionnaire.
	If ProjectQuestionnaire does not exist, this function creates it.
	Args:
		Questionnaire object: workingQuestionnaire.

	Returns:
		True is properly set	

	Raises:
		None
	"""
	try:
		pqObj = ProjectQuestionnaire.objects.get(
			projectID=theProject,
			questionnaireID=theQuestionnaire,
			recordType='connection',
			)
		pqObj.questionnaireStatus = questionnaireStatus
		pqObj.save()
	except ProjectQuestionnaire.DoesNotExist:
		ProjectQuestionnaire.objects.create(
			projectID=theProject,
			questionnaireID=theQuestionnaire,
			recordType='connection',
			)	
	return True

def testForPages(workingQuestionnaire):
	"""output is True or False if pages are associated with
	the Questionnaire as found in the QuestionnairePage table

	Args:
		Questionnaire object: workingQuestionnaire.

	Returns:
		page count (integer)	

	Raises:
		None
	"""
	recordCount = QuestionnairePage.objects.filter(
		questionnaireID=workingQuestionnaire
		).filter(
		recordType = 'next_page_default').count()
	# Can't use recordCount as a count of pages, however...
	if recordCount > 0:
		pageTF = True
	else:
		pageTF = False
	return pageTF

def getAllPageObjsForQuestionnaire(workingQuestionnaire):
	"""output is a QuerySet of objects of type "Page" belonging to the questionnaire.
	Extract from the page transition table in QuestionnairePage.

	Args:
		Questionnaire object: workingQuestionnaire.

	Returns:
		QuerySet: of type Page 	

	Raises:
		None
	"""
	allQuestionnairePage = QuestionnairePage.objects.filter(
		questionnaireID=workingQuestionnaire
		).filter(
		recordType = 'next_page_default')
	# extract pages for this questionnaire.
	allPagesFromIDs = [item.pageID.id for item in allQuestionnairePage]
	allPagesToIDs = [item.nextPageID.id for item in allQuestionnairePage]
	# Concatenate and eliminate duplicates
	allPageIDs = list(set(allPagesFromIDs+allPagesToIDs))
	# have list of record IDs, turn into a QuerySet
	if allPageIDs:  # non null list
		allPageIDQuerySet = retrieveBulk( Page, allPageIDs )
	else:
		allPageIDQuerySet = Page.objects.none()
	
	return allPageIDQuerySet
	
def getAllQuestionObjsForQuestionnaire(workingQuestionnaire):
	"""Output is a QuerySet of objects of type "Question" belonging to the questionnaire.
	Extract from the page transition table in QuestionnairePage,
	and the PageQuestion table.

	Args:
		Questionnaire object: workingQuestionnaire.

	Returns:
		QuerySet: of type Question 	

	Raises:
		None
	"""
	allPages = getAllPageObjsForQuestionnaire(workingQuestionnaire)
	questionIDListWdups = []
	for aPage in allPages:
		pageQuestions = getPageQuestions( aPage)
		pqIDList = [pg.id for pg in pageQuestions]
		questionIDListWdups.extend(pqIDList)
	questionIDList = list(set(questionIDListWdups))
	if questionIDList:  # non null list
		allQuestionsInQuest = retrieveBulk( Question, questionIDList )
	else:
		allQuestionsInQuest = Page.objects.none()
	
	return allQuestionsInQuest
	
def getAllPageObjsInQuestionnaires():
	"""Output is a QuerySet of objects of type "Page" referenced by all questionnaires.

	Extract from the page transition table in QuestionnairePage.
	Go top down, start with unique Projects.

	Args:
		Questionnaire object: workingQuestionnaire.

	Returns:
		QuerySet: of type Page 	

	Raises:
		None
	"""
	allQuestionnaires = getAllQuestionnaires() # queryset result
	# find pages referenced by these questionnaires.
	morePageIDs = []
	for aQuest in allQuestionnaires:
		allPageObjsPerQuestionnaire = getAllPageObjsForQuestionnaire(aQuest)
		for aPage in allPageObjsPerQuestionnaire:
			morePageIDs.append(aPage.id)
	# Eliminate duplicates
	allPageIDs = list(set(morePageIDs))
	# have list of record IDs, turn into a QuerySet
	if allPageIDs:  # non null list
		allPageIDQuerySet = retrieveBulk( Page, allPageIDs )
	else:
		allPageIDQuerySet = Page.objects.none()
	
	return allPageIDQuerySet

def getAllPageObjsNotReferenced():
	"""Return a QuerySet of objects of type "Page" not belonging to any questionnaire,
	nor having any Response records pointing to it.
	
	This function displays a list

	Args:
		None

	Returns:
		return_value: QuerySet of objects of type "Page". 	

	Raises:
		None.
	"""
	# create a list of all Page objects.
	allPageObjs = Page.objects.all()
	listOfAllPageIDs = [thePage.id for thePage in allPageObjs]
	setOfAllPageIDs = set(listOfAllPageIDs)
	# create list of all Page objects referenced by all questionnaires
	allPageObjsInQuest = getAllPageObjsInQuestionnaires()
	listOfPageIDsInQuest = [thePage.id for thePage in allPageObjsInQuest]
	setOfPageIDsInQuest = set(listOfPageIDsInQuest)
	# create list of all Pages referenced by Responses - can't be edited anyway, so remove
	allResponseObjs = Response.objects.all()
	listOfAllPagesRefdBYResponses = [theResp.questionOnPageID.id for theResp in allResponseObjs]
	setOfAllPagesRefdBYResponses = set(listOfAllPagesRefdBYResponses)
	# list all the pages not in either list
	setOfPagesNotReferenced = setOfAllPageIDs - setOfPageIDsInQuest - setOfAllPagesRefdBYResponses
	listOfPagesNotReferenced = list(setOfPagesNotReferenced)
	
	# have list of record IDs, turn into a QuerySet
	if listOfPagesNotReferenced:  # non null list
		pagesNotRefd = retrieveBulk( Page, listOfPagesNotReferenced )
	else:
		pagesNotRefd = Page.objects.none()
	return pagesNotRefd

def getAllPageObjsEditable():
	"""Return a QuerySet of objects of type "Page" belonging to any questionnaire,
	or NOT belonging to a questionnaire. Pages excluded are referenced by a Submission
	for a "Questionnaire tag-Project tag", but superseded by a later 
	"Questionnaire tag-Project tag"
	
	This function displays a list

	Args:
		None

	Returns:
		return_value: QuerySet of objects of type "Page". 	

	Raises:
		None.
	"""
	allPagesInQuest = getAllPageObjsInQuestionnaires() # must be included
	allPagesNotInQuest = getAllPageObjsNotReferenced() # include also
	# sum the querysets, by extracting all id's
	idList = []
	for aPage in allPagesInQuest:
		idList.append(aPage.id)
	for aPage in allPagesNotInQuest:
		idList.append(aPage.id)
	# Now query for all to put them in a single queryset.
	# may not be so efficient!
	if idList:  # non null list
		allPageObjs = retrieveBulk( Page, idList )
	else:
		allPageObjs = Page.objects.none()
	
	return allPageObjs

def duplicatePageRecord(theQuestionnaire, thePage):
	"""Duplicates the Page record while maintaining foreign keys:
			to Questionnaire
			to PageAttributes
			to PageAnalysis.
	Args:
		thePage:  object
	Database edits:
		Page
		PageQuestion
		PageAnalysis
		PageAttributes
	Returns:
		duplicated Page object	
	
	Raises:
		No exceptions raised.
	"""
	oldPid = thePage.id
	thePage.id = None # will force a new record
	thePage.save()
	newPage = thePage
	oldPage = Page.objects.get(id=oldPid)
	# Maintain connection to Questionnaire
	# Page may appear in QuestionnairePage.pageID OR QuestionnairePage.nextPageID
	# Match the Questionnaire
	queryOR = Q(pageID=oldPage) | Q(nextPageID=oldPage)
	queryFull = Q(questionnaireID = theQuestionnaire) & queryOR
	allQPRecs = QuestionnairePage.objects.filter(queryFull)
	# eliminate duplicates:  not sure if there are any! *** CHECK THIS ANOTHER TIME
	for aRec in allQPRecs:
		# update and DO NOT force a new record. Already done by Questionnaire duplicate
		if aRec.pageID == oldPage:
			aRec.pageID=newPage
		if aRec.nextPageID == oldPage:
			aRec.nextPageID=newPage
		aRec.save()
	# Maintain connection to Question
	allPQRecs = PageQuestion.objects.filter(pageID=oldPage)
	for aRec in allPQRecs:
		# update and force a new record
		aRec.pageID=newPage
		aRec.id=None
		aRec.save()
	# Maintain connection to PageAnalysis
	allPARecs = PageAnalysis.objects.filter(
		pageID=oldPage,
		questionnaireID=theQuestionnaire)
	for aRec in allPARecs:
		# update and force a new record
		aRec.pageID=newPage
		aRec.id=None
		aRec.save()
	# PageAttributes update is not required since it matches on Page.pageType
	# not the Page object.
	return newPage

def duplicateQuestionRecord(thePage, theQuestion):
	"""Duplicates the Question record while maintaining foreign keys:
			to PageQuestion
	Args:
		theQuestion:  object	Note:  theQuestion is trampled on = newQuestion
		thePage:	object
	Database edits:
		Question
		PageQuestion
	Returns:
		duplicated Question object	
	
	Raises:
		No exceptions raised.
	"""
	oldPid = theQuestion.id
	theQuestion.id = None # will force a new record
	theQuestion.save()
	newQuestion = theQuestion
	oldQuestion = Question.objects.get(id=oldPid)
	# Maintain connection to Page
	# Question may appear in PageQuestion
	allPQRecs = PageQuestion.objects.filter(
		questionID=oldQuestion,
		pageID=thePage) # update the questions belonging to this page
	for aRec in allPQRecs:
		# update and DO NOT force a new record. Already done
		aRec.questionID=newQuestion
		aRec.save()
	# Maintain connection to ResponseChoice
	allPQRecs = ResponseChoice.objects.filter(questionID=oldQuestion)
	for aRec in allPQRecs:
		# update and force a new record
		aRec.questionID=newQuestion
		aRec.id=None
		aRec.save()
	# QuestionAttributes update is not required since it matches on Question.QuestionType
	# not the Question object.
	return newQuestion

def getAllQuestionObjsEditable():
	"""Return a QuerySet of objects of type "Question" belonging to any questionnaire,
	or NOT belonging to a questionnaire. Questions excluded are referenced by a Submission
	for a "Questionnaire tag-Project tag", but superseded by a later 
	"Questionnaire tag-Project tag"
	
	This function displays a list

	Args:
		None

	Returns:
		return_value: QuerySet of objects of type "Page". 	

	Raises:
		None.
	"""
	allPages = getAllPageObjsEditable()
	# Find all questions for all pages
	questionRecList = []
	for aPage in allPages:
		thisPageQuestions = PageQuestion.objects.filter(pageID=aPage)
		for aQuestion in thisPageQuestions:
			questionRecList.append(aQuestion.questionID.id)
	# remove redundancies in question record list
	questionRecList = list(set(questionRecList))
	
	# have list of record IDs, turn into a QuerySet
	if questionRecList:  # non null list
		allQuestions = retrieveBulk( Question, questionRecList )
	else:
		allQuestions = Question.objects.none()
	return allQuestions

def retrieveBulk( objClass, theRecordIDs ):
	"""Return a QuerySet of objects of type "objClass" retrieved from the
	database with specified record numbers.

	Warning:  not sure if output queryset is in same order as input record ids
	Args:
		objClass which is the name appearing in model.py
		theRecordIDs:  integer list of record numbers

	Returns:
		return_value: QuerySet of objects of type "objClass". 	

	Raises:
		None.
	"""
	# make the record ids unique
	# construct the query using the "Q object" (see page 104) in pdf from Django site
	# and:  https://docs.djangoproject.com/en/1.5/topics/db/queries/#complex-lookups-with-q
	if theRecordIDs:  # non null list
		queryOR = Q(id=theRecordIDs[0])
		for aRec in theRecordIDs[1:]:
			queryOR = queryOR | Q(id=aRec)
		qSet = objClass.objects.filter(queryOR)
	else:
		qSet = objClass.objects.none()
	return qSet

def changeListToQueryset(theList, theObject):
	""" Changes a list of objects to a query set by accessing the database
	"""
	# collect the record ids
	theIDs=[ar.id for ar in theList]
	theQuerySet = retrieveBulk( theObject, theIDs )
	return theQuerySet
	
def getResponseChoicesForAPage(thisPageObj):
	"""Return a QuerySet of objects of type "ResponseChoice" belonging to the questions on a page,
	"""
	thePageQuestions = getPageQuestions(thisPageObj)
	responseIDs = []
	for aQuestion in thePageQuestions:
		theResponses = ResponseChoice.objects.filter(questionID=aQuestion)
		for aResponse in theResponses:
			responseIDs.append(aResponse.id)
	theResponses = retrieveBulk(ResponseChoice, responseIDs)
	return theResponses

def updatePageQuestionSequence(thePage,theQuestion, seqText):
	"""Updates or creates a PageQuestion record for the Page, Question sequence.
	
	Database:
		update PageQuestion record for the Page/Question pair
		deletes additional records beyond 1
		create a record if not already present
	"""
	thePQs=PageQuestion.objects.filter(
		pageID=thePage,
		questionID=theQuestion,
		)
	# should be only one!!
	iCount = thePQs.count()
	if iCount == 0: # create the record
		PageQuestion.objects.create(
			pageID=thePage,
			questionID=theQuestion,
			questionSequence=seqText,
			)
	elif iCount == 1: # update the record
		DebugOut('updatePageQuestionSequence:  updating a record')
		thePQ = thePQs[0]
		thePQ.questionSequence=seqText
		thePQ.save()
	elif iCount > 1: # delete the additional ones!!
		DebugOut('updatePageQuestionSequence:  deleteing additional records for page %s, question %s'%(thePage.shortTag,theQuestion.questionTag))
		ii = 1
		for thePQ in thePQs:
			if ii == 1: # update the first one.
				thePQ.questionSequence=seqText
				thePQ.save()
			else: # delete the remaining
				thePQ.delete()
			ii+=1
	return
	
def getPageQuestions( pageObj):
	"""Return a List of objects of type "Question" belonging to a page,
	Args:
		Page Object

	Returns:
		theQuestionObjs: List of objects of type "Question". 	

	Raises:
		None.
	"""
	# retrieve questions from the PageQuestions model
	thePageQuestions=PageQuestion.objects.filter(pageID=pageObj).order_by('questionSequence')
	questionObjList = [aPQ.questionID for aPQ in thePageQuestions]
	return questionObjList

def getQuestionObj(thePage, questionTag):
	"""Return a question object assuming the question tag is unique"""
	optimism = True
	try:
		pqObjs = PageQuestion.objects.filter(pageID=thePage)
		haveAMatch = False # start by assuming no tag match
		for aPQrec in pqObjs:
			questionTagTest = aPQrec.questionID.questionTag
			if questionTagTest == questionTag:
				haveAMatch = True
				theQuestion = aPQrec.questionID
				questionSequence = aPQrec.questionSequence
		success = haveAMatch
	except:
		success = False
	questionObj = theQuestion # last one if multiple.
	return [questionObj, success]
	
def getDefaultLanguage(request):
	"""Get a language code defined for the website."""
	
	if settings.LANGUAGE_CODE == 'en-us': # in settings.py
		langName = 'English' # code used in database
	else:
		langName = 'English' # the default of defaults

	return langName


# ************** Page calculation
	
def getStartPageObj(theQuestionnaire):
	"""Retrieve the first page object for the Questionnaire
	
	Args:
		Questionnaire object

	Returns:
		page object for the first page of the questionnaire	
	Side effects:
		None.
	Raises:
		None.	
	"""
	try:
		qpObj = QuestionnairePage.objects.get(
			questionnaireID=theQuestionnaire,
			recordType = 'start_page',
			)
		firstPageObj = qpObj.pageID
	except QuestionnairePage.DoesNotExist:
		firstPageObj = None
	return firstPageObj

def setStartPageObj(theQuestionnaire, startPageObj):
	"""Set the first page object for the Questionnaire
	
	Args:
		Questionnaire object
		Page object
	Returns:
		True	
	Side effects:
		Sets start page in QuestionnairePage table
	Raises:
		None.	
	"""
	# first delete any other contender for start page
	QuestionnairePage.objects.filter(
		questionnaireID = theQuestionnaire,
		recordType = 'start_page',
		).delete()
	# create a new record for the start page
	QuestionnairePage.objects.create(
		questionnaireID = theQuestionnaire,
		pageID = startPageObj,
		nextPageID = startPageObj,
		recordType = 'start_page',
		)
	return True
	
# def getPageObjFromSD(request, pageTag): # not used
# 	"""Gets a Page object corresponding to tag. Use session data.
# 	
# 	Args:
# 		request
# 		Page Tag:  character string
# 		
# 	Assumptions:
# 		setSessionPageTagToRecord has been called to set up session data:
# 		pageTagToRecord
# 		recordToPageTag
# 
# 	Returns:
# 		a Page object. If not found with pageTag, then null	
# 
# 	Raises:
# 		None.
# 	"""
# 	success = True # optimism
# 	# Standard page object retrieval
# 	[pageTagToRecord,recordToPageTag] = getSessionPageTagToRecord(request)
# 	
# 	if pageTagToRecord:
# 		try:
# 			thePage = Page.objects.get(id=pageTagToRecord[pageTag])
# 		except KeyError:
# 			success = False
# 			thePage = Page()
# 	else:
# 		success = False
# 		thePage = Page()
# 	
# 	return [thePage, success]
	
def getPageToPageObjs(theQuestionnaire):
	"""Retrieves page transition matrix from QuestionnairePage.
	
	Args:
		Questionnaire object

	Returns:
		a Dictionary object. from page object : to page object

	Raises:
		None.
	"""
	try:
		thePageToPageMap=QuestionnairePage.objects.filter(
			questionnaireID=theQuestionnaire
		).filter(
			recordType='next_page_default' # select only defaults!!
		)
		pageToPage = {}
		for item in thePageToPageMap: # build a dictionary for page transitions
			pageToPage.update({item.pageID : item.nextPageID}) # from : to
	except QuestionnairePage.DoesNotExist:
		DebugOut('syserrmsg: No reference to pages can be found for the questionnaire! %s' % theQuestionnaire.shortTag)
		pageToPage = {}
	return pageToPage

def getPageToPageShortTags(theQuestionnaire):
	"""Retrieves page transition matrix from QuestionnairePage.
	
	Args:
		Questionnaire object

	Returns:
		a Dictionary object. from page shortTag : to page shortTag

	Raises:
		None.
	"""
	try:
		thePageToPageMap=QuestionnairePage.objects.filter(
			questionnaireID=theQuestionnaire
		).filter(
			recordType='next_page_default' # select only defaults!!
		)
		pageToPage = {}
		for item in thePageToPageMap: # build a dictionary for page transitions
			pageToPage.update({item.pageID.shortTag : item.nextPageID.shortTag}) # from : to
	except QuestionnairePage.DoesNotExist:
		DebugOut('syserrmsg: No reference to pages can be found for the questionnaire! %s' % theQuestionnaire.shortTag)
		pageToPage = {}
	return pageToPage

def allPagesInDefaultOrder(theQuestionnaire):
	"""Puts all of the pages in a questionnaire on a linear track.
	
	Args:
		Questionnaire object, page object

	Returns:
		a Page object List in default order
	
	Raises:
		None.
	"""
	ppObjs = getPageToPageObjs(theQuestionnaire) # get dictionary of page to next page objects
	pageToPageTieredList = transitionMatrixTo2DList(ppObjs) # make a tiered list
	pageToPageFlatList = flattenList(pageToPageTieredList) # flatten to a single level list
	pageToPageNoDups = removeDupsFromBeginning(pageToPageFlatList) # eliminate duplicates
	
	return pageToPageNoDups

def oneTrackPageToPage(theQuestionnaire):
	"""Puts all of the pages in a questionnaire on a linear track. Given "thisPage", this
	function returns the "nextPage" object.
	
	Args:
		Questionnaire object, page object

	Returns:
		a "next page" object dictionary
	
	Raises:
		None.
	"""
	pageToPageNoDups = allPagesInDefaultOrder(theQuestionnaire) # eliminate duplicates
	#DebugOut('pageToPageNoDups: %s' %pageToPageNoDups)
	pageToPageTrackNext = transitionListToMatrix([pageToPageNoDups]) # create "from" "to"
	pageToPageNoDupsRev = list(reversed(pageToPageNoDups))
	pageToPageTrackPrev = transitionListToMatrix([pageToPageNoDupsRev]) # reverse
	# dictionary
	return [pageToPageTrackNext, pageToPageTrackPrev]
	
def getPageToPageList(theQuestionnaire):
	"""Retrieves page transition List of shortTags from QuestionnairePage.
	
	Args:
		Questionnaire object

	Returns:
		a two dimensional list object. Each element is a list of page shortTags.

	Raises:
		None.
	"""
	ppObjs = getPageToPageObjs(theQuestionnaire)
	# investigate all the pages
	fromSet = set([])
	toSet = set([])
	for pFrom in ppObjs.iterkeys():
		fromSet.add(pFrom)
		toSet.add(ppObjs[pFrom])
	
	# find pages with no precedent.
	noPrecedent = fromSet - toSet
	# create a character string representation
	pageToPageList = []
	for anItem in noPrecedent:
		currObj = anItem # start at the beginning
		consecutiveFromTo = [currObj.shortTag]
		while True:
			try:
				toObj = ppObjs[currObj]
				consecutiveFromTo.append(toObj.shortTag)
				currObj = toObj
			except KeyError:
				break
		pageToPageList.append(consecutiveFromTo)
	return pageToPageList

def setSessionPageTagToRecord(request, theQuestionnaire):
	"""Saves page to record translation to Session Data.
	
	This page to record mapping depends upon the page transition table defined by the input
	Questionnaire.
	
	Purpose:  help with translating a url and mapping the page tag to a page record
	
	Args:
		request query
		Questionnaire object

	Returns:
		None.
		
	Side effects:
		Session data:  pageTagToRecord and recordToPageTag
		which are dictionary objects page short tag : to page record id

	Raises:
		None.
	"""
	[pageTagToRecord, recordToPageTag ] = getPageToRecordMapping(theQuestionnaire)
	request.session['pageTagToRecord'] = pageTagToRecord
	request.session['recordToPageTag'] = recordToPageTag
	return
	
	
	
def getPageToRecordMapping(theQuestionnaire):
	"""Gets a one-to-one page tag to record id mapping for a questionnaire.
	Assume Page tags are unique for a given questionnaire.
	
	This page to record mapping depends upon the page transition table defined by the input
	Questionnaire.
	
	Args:
		Questionnaire object
		Page Tag:  character string

	Side effects:
		none.

	Raises:
		None.
	
	Returns:
		Two dictionaries:  pageTagToRecord, recordToPageTag
	"""
	pageTagToRecord = {}
	recordToPageTag = {}
	allQPs = QuestionnairePage.objects.filter(
		questionnaireID=theQuestionnaire,
		recordType = 'next_page_default'
		)	# Collect all page records
	
	for aQP in allQPs: # include "From" and "To". Duplicates are eliminated from the dictionaries
		pageTagToRecord.update({aQP.pageID.shortTag : aQP.pageID.id})
		pageTagToRecord.update({aQP.nextPageID.shortTag : aQP.nextPageID.id})
		recordToPageTag.update({aQP.pageID.id : aQP.pageID.shortTag})
		recordToPageTag.update({aQP.nextPageID.id : aQP.nextPageID.shortTag})
	
	return [pageTagToRecord, recordToPageTag ]

def getNextPageFromDB(theQuestionnaire, currPageObj):
	"""Gets the next page object.
		
	Args:
		theQuestionnaire: object of type Questionnaire
		currPageObj:  object of type Page

	Side effects:
		none.

	Raises:
		None.
	Returns
		nextPageObj of type Page
	"""
	try:
		qpObj = QuestionnairePage.objects.get( # assume transition matrix is consistent
			questionnaireID=theQuestionnaire,
			pageID=currPageObj,
			recordType = 'next_page_default',
			)
		nextPageObj = qpObj.nextPageID
	except:
		if currPageObj:
			DebugOut('Next page not found for page %s'%currPageObj.shortTag)
		else:
			DebugOut('Next page not found')
		nextPageObj = None
		
	return nextPageObj
	
def getPageObj(theQuestionnaire, pageTag):
	"""Gets a Page object corresponding to the pageTag as defined in QuestionnairePage.
	
	This page object retrieval depends upon the page transition table defined by the input
	Questionnaire.
	
	Args:
		Questionnaire object
		Page Tag:  character string

	Returns:
		a Page object. If not found with pageTag, then empty page	

	Raises:
		None.
	"""
	# queries Page for the page in a Questionnaire with a specified tag.
	# Questionnaire ownership is respected
	# page tags are assumed to be unique per Questionnaire
	# queries QuestionnairePage and Page
	# this retrieval no longer depends upon the page tag being unique among Pages
	success = True # optimism
	allPages = getAllPageObjsForQuestionnaire(theQuestionnaire)
	pageMatch = allPages.filter(shortTag=pageTag)
	if pageMatch.count() == 0:
		# no matching shortTag
		pageObj = Page()
		success = False
	elif pageMatch.count() > 1:
		pageObj = pageMatch[0] # Short tag should be uniuqe
		DebugOut('Syserrmsg:  Multiple (%s) pages found for page tag "%s" in Questionnaire "%s"'%(pageMatch.count(),pageTag,theQuestionnaire.shortTag))
	else:
		pageObj = pageMatch[0] # Unique tag
	return [pageObj, success]

def updateObjFields(thisObj,cleanedData):
	"""Updates the page record with cleanedData. Does not save to database.
	
	Args:
		thisObj: the page object to be updated
		cleanedData: dictionary of input data
		
	returns:
		updatedPageObj: updated object
	"""
	DebugOut('updateObjFields:  entered')
	DebugOut('Object is: %s' %thisObj)
	isUpdated = False
	theModelFields = getModelFieldList(thisObj)
	for aFieldName in theModelFields:
		DebugOut('Trying field:  "%s"' %aFieldName)
		try:
			aFieldValue = str(getattr(thisObj, aFieldName))
			DebugOut('Found value "%s" for field name "%s"' %(aFieldValue,aFieldName))
			updateValue = cleanedData[aFieldName]
			DebugOut('for field name: "%s", old/new: %s -> %s' %(aFieldName,aFieldValue,str(updateValue)))
			if aFieldValue != updateValue:
				DebugOut('updateObjFields %s, for field name: %s, \nUpdating old: %s \nTo the New: %s' %(thisObj.shortTag,aFieldName,aFieldValue,str(updateValue)))
				setattr(thisObj, aFieldName, updateValue)
				isUpdated = True
		except:
			DebugOut('exception for field name: %s' %aFieldName)
			pass # some fields (which ones?) will not be attributes of the model
				# some will not be updated
	DebugOut('updateObjFields:  exit')
	return [thisObj, isUpdated]
	
def saveSharedPageObj(thePage):
	"""Save the Page object. All questionnaires pointing to this page are updated.
	update the record if there are no Response pointers, copy if there are.
	
	A new page record is created if any of the following point to this page:
		Response
		PageQuestion
		PageAttributes # does not need updating since no Foreign Key.
		PageAnalysis
		QuestionnairePage
	
	"""
	# check Responses
	countRecs = Response.objects.filter(
		questionOnPageID = thePage
		).count()
	if countRecs != 0: # there are Response records pointing to this Page
		# a Response refers to this page.
		# force a duplication of the Page record upon "save"
		# save old id
		idforOld = thePage.id
		thePage.id = None # will force a new record
		thePage.save()
		# Update records to point to new Page record
		# first retrieve for old Page.
		oldPage = Page.objects.get(id=idforOld)
		#
		# update QuestionnairePage records
		# first search "From" field
		qpObjs = QuestionnairePage.objects.filter(
			pageID=oldPage) # From
		# loop through each, updating the QuestionnairePage object "From"
		for aQP in qpObjs:
			aQP.pageID=thePage # From.
			aQP.id=None # force a new record
			aQP.save()
		# Now search "To" field
		qpObjs = QuestionnairePage.objects.filter(
			nextPageID=oldPage) # To
		# loop through each, updating the QuestionnairePage object "To"
		for aQP in qpObjs:
			aQP.nextPageID=thePage # To.
			aQP.id=None # force a new record
			aQP.save()
		#
		# update PageQuestion records
		pqObjs = PageQuestion.objects.filter(
			pageID=oldPage)
		# loop through each, updating the PageQuestion object
		for aQP in pqObjs:
			aQP.pageID=thePage # Update to new page
			aQP.id=None # force a new record
			aQP.save()
		#
		# update PageAnalysis records
		paObjs = PageAnalysis.objects.filter(
			questionnaireID,
			pageID=thePage)
		# loop through each, updating the PageQuestion object
		for aPA in paObjs:
			aPA.pageID=thePage # Update to new page
			aPA.id=None # force a new record
			aPA.save()
	else:
		thePage.save() # No Response pointers, so allow save to update record
	
	return thePage

def saveSharedQuestionObj(theQuestion):
	"""Save the Question object. All PageQuestions pointing to this Question are updated.
	update the record if there are no Response pointers, duplicate if there are.
	
	A new Question record is created if any of the following point to this Question:
		Response
		PageQuestion
		ResponseChoice
	
	"""
	# check Responses
	countRecs = Response.objects.filter(
		questionID = theQuestion
		).count()
	if countRecs != 0: # there are Response records pointing to this Question
		# a Response refers to this Question.
		# force a duplication of the Question record upon "save"
		# save old id
		idforOld = theQuestion.id
		theQuestion.id = None # will force a new record
		theQuestion.save()
		# Update records to point to new Question record
		# first retrieve for old Question.
		oldQuestion = Question.objects.get(id=idforOld)
		#
		# update PageQuestion records. Force a new record
		pqObjs = PageQuestion.objects.filter(
			questionID=theQuestion)
		# loop through each, updating the PageQuestion object
		for aPQ in pqObjs:
			aPQ.questionID=theQuestion # From.
			aPQ.id=None # force a new record
			aPQ.save()
		#
		# update ResponseChoice records. Force a new record
		rcObjs = ResponseChoice.objects.filter(
			questionID=theQuestion)
		# loop through each, updating the ResponseChoice object
		for aRC in rcObjs:
			aRC.questionID=theQuestion # From.
			aRC.id=None # force a new record
			aRC.save()
	else:
		theQuestion.save() # No Response pointers, so allow save to update record

	return theQuestion

def deletePageInQuestionnaire(theQuestionnaire, pageToDeleteObj):
	"""The page is deleted and QuestionnairePage is updated to repair the hole in the
	transition matrix
		
	Args:
		theQuestionnaire
		pageToDeleteObj - the page is inserted "after" this page in the transition matrix
	"""
	DebugOut('deletePageInQuestionnaire:  enter')
	errMsg = []
	# check to see if it is a start page
	startPage = False
	QPstartPage = QuestionnairePage.objects.filter(
		questionnaireID = theQuestionnaire,
		pageID =pageToDeleteObj,
		recordType = 'start_page',
		) # should be only one record retrieval!!
	if QPstartPage.count() > 0:
		startPage = True
		msg = "Can't delete the start page"
		DebugOut(msg)
		errMsg.append(msg)
	
	# search for the page to be deleted appearing in the "from" field in QuestionnairePage
	QPtoUpdate = QuestionnairePage.objects.filter(
		questionnaireID = theQuestionnaire,
		pageID =pageToDeleteObj,
		recordType = 'next_page_default',
		) # should be only one record retrieval!!
		
	if QPtoUpdate.count() >1:
		# screwed up transition matrix:  same page points to multiple locations
		# arbitrarily delete the most recent
		# then retrieve "toPage"
		errMsg.append('Error: page %s has more than one next page.'%pageToDeleteObj.shortTag)
		errMsg.append('To fix, go back to Home page and select "Reshuffle the page sequence" for further information.')
	elif QPtoUpdate.count() == 1:
		toPage = QPtoUpdate[0].nextPageID
		DebugOut('type(toPage): %s' %type(toPage))
		DebugOut('next page: %s' %toPage.shortTag)
	elif not startPage:
		# QPtoUpdate.count() == 0
		# pageToDeleteObj points to nothing, so it is at the end of the line
		# Makes it easy. Delete. The Cascade option will delete any QuestionnairePage
		# records which point to pageToDeleteObj in the "to" field.
		pageToDeleteObj.delete()		
	
	if errMsg:
		DebugOut('deletePageInQuestionnaire:  enter')
		return errMsg
		
	# check for pages pointing "to" pageToDeleteObj. May be more than one.
	QPToPage = QuestionnairePage.objects.filter(
		questionnaireID = theQuestionnaire,
		nextPageID =pageToDeleteObj,
		recordType = 'next_page_default',
		) # May be more than one.
	if QPToPage.count() > 0:
		# replace the "to" with "toPage" above which pageToDeleteObj points to
		for aQPrec in QPToPage:
			aQPrec.nextPageID = toPage # an error here. Must be Page instance.
			aQPrec.save()
		# pageToDeleteObj is now disassociated from the transition matrix
		pageToDeleteObj.delete()
	elif QPToPage.count() == 0:
		# This page has no precedent, therefore at the beginning of the line
		pageToDeleteObj.delete()
		# cascade option will take care of the rest
	DebugOut('deletePageInQuestionnaire:  exit')
	return errMsg

def createNewPageForQuestionnaireBefore(theQuestionnaire, beforePageObj, newShortTag):
	"""A new page object is created before "beforePageObj" with the indicated shortTag
		QuestionnairePage is updated
	Args:
		theQuestionnaire
		beforePageObj - the page is inserted "before" this page in the transition matrix
		newShortTag - the new page will have this shortTag
	"""
	newPageObj = Page.objects.create(shortTag=newShortTag)
	# now update QuestionnairePage
	# find beforePageObj in the "to" field
	QPtoUpdate = QuestionnairePage.objects.filter(
		questionnaireID = theQuestionnaire,
		nextPageID =beforePageObj,
		recordType = 'next_page_default',
		) # may be more than one record retrieval!! More than one page can point to a given "next" page
	if QPtoUpdate: # nonzero records
		for aQPrecord in QPtoUpdate:
			# replace the "to" with newPageObj
			aQPrecord.nextPageID = newPageObj
			# save the record
			aQPrecord.save()
			# create a new record with newPageObj in "to" and oldFrom in "from"
			newQP = QuestionnairePage.objects.create(
				questionnaireID = theQuestionnaire,
				nextPageID = beforePageObj,
				pageID = newPageObj,
				recordType = 'next_page_default',
				)
	else: # Assume that beforePageObj is at the beginning of the line,
		# so that newPageObj will be the new beginning of the line.
		newQP = QuestionnairePage.objects.create(
			questionnaireID = theQuestionnaire,
			pageID = newPageObj,
			nextPageID = beforePageObj,
			recordType = 'next_page_default',
			)
		
	return newPageObj

def createNewPageForQuestionnaireAfter(theQuestionnaire, afterPageObj, newShortTag):
	"""A new page object is created after "afterPageObj" with the indicated shortTag
		QuestionnairePage is updated
	Args:
		theQuestionnaire
		afterPageObj - the page is inserted "after" this page in the transition matrix
		newShortTag - the new page will have this shortTag
	"""
	newPageObj = Page.objects.create(shortTag=newShortTag)
	# now update QuestionnairePage
	# find afterPageObj in the "from" field
	try:
		QPtoUpdate = QuestionnairePage.objects.get(
			questionnaireID = theQuestionnaire,
			pageID =afterPageObj,
			recordType = 'next_page_default',
			) # should be only one record retrieval!!
		# retrieve the object in the "to" field. Call it "oldTo"
		oldTo = QPtoUpdate.nextPageID
		# replace the "to" with newPageObj
		QPtoUpdate.nextPageID = newPageObj
		# save the record
		QPtoUpdate.save()
		# create a new record with newPageObj in "from" and oldTo in "to"
		newQP = QuestionnairePage.objects.create(
			questionnaireID = theQuestionnaire,
			pageID =newPageObj,
			nextPageID = oldTo,
			recordType = 'next_page_default',
			)
	except: # Assume that afterPageObj is at the end of the line,
			# so that newPageObj will be the new end of the line.
		newQP = QuestionnairePage.objects.create(
			questionnaireID = theQuestionnaire,
			pageID =afterPageObj,
			nextPageID = newPageObj,
			recordType = 'next_page_default',
			)
		
	return newPageObj
	
def saveNewPageObj(theQuestionnaire, thePage):
	"""Save the Page object. New page only appears in theQuestionnaire.
	update the record if there are no Response pointers, copy if there are.
	
	A new page record is created if any of the following point to this page:
		PageQuestion
		PageAttributes # does not need updating since no Foreign Key.
		PageAnalysis
		QuestionnairePage
	
	"""
	# check Responses
	countRecs = Response.objects.filter(
		questionOnPageID = thePage
		).count()
	if countRecs != 0: # there are Response records pointing to this Page
		# a Response refers to this page.
		# force a duplication of the Page record upon "save"
		# save old id
		idforOld = thePage.id
		thePage.id = None # will force a new record
		thePage.save()
		# Update records to point to new Page record
		# first retrieve for old Page.
		oldPage = Page.objects.get(id=idforOld)
		#
		# update QuestionnairePage records
		# first search "From" field
		qpObjs = QuestionnairePage.objects.filter(questionnaireID=theQuestionnaire,
			pageID=oldPage) # From
		# loop through each, updating the QuestionnairePage object
		for aQP in qpObjs:
			aQP.pageID=thePage # From.
			aQP.id=None # force a new record
			aQP.save()
		# Now search "To" field
		qpObjs = QuestionnairePage.objects.filter(questionnaireID=theQuestionnaire,
			nextPageID=oldPage) # To
		# loop through each, updating the QuestionnairePage object
		for aQP in qpObjs:
			aQP.nextPageID=thePage # To.
			aQP.id=None # force a new record
			aQP.save()
		#
		# update PageQuestion records
		pqObjs = PageQuestion.objects.filter(
			pageID=oldPage)
		# loop through each, updating the PageQuestion object
		for aQP in pqObjs:
			aQP.pageID=thePage # Update to new page
			aQP.id=None # force a new record
			aQP.save()
		#
		# update PageAnalysis records
		paObjs = PageAnalysis.objects.filter(
			questionnaireID=theQuestionnaire,
			pageID=thePage)
		# loop through each, updating the PageQuestion object
		for aPA in paObjs:
			aPA.pageID=thePage # Update to new page
			aPA.id=None # force a new record
			aPA.save()
	else:
		thePage.save() # No Response pointers, so allow save to update record
	
	return thePage

def testQuestionnaire(theQuestionnaire):

	# test consistency of transition matrix (each"from" is unique)
	# test for uniqueness of page tags
	# test for start page
	# test for last page
	# test for overlap with other Questionnaires
	
	theDetails = []
	return theDetails
	
def consistencyCheckUniquePageTagsPerQuestionnaire():
	# perform a consistency check for the transition table (QuestionnairePage) for all questionnaires
	# verify all page tags are unique.
	# verify each "from" page goes to one and only one "to" page.
	#	The "from" page should appear only once in the "pageID" field per questionnaire.
	allQuaires = Questionnaire.objects.all()
	theQuestWDups = [] # questionnaires which have duplicate pages
	thePagesWDups = [] # list of page tags with dups
	for aQuaire in allQuaires:
		# list all page objects in the questionnaire.
		allPageObjs = getAllPageObjsForQuestionnaire(aQuaire) # outputs all unique page objects.
		allPageTags = [item.shortTag for item in allPageObjs]
		# verify no duplicate tags.
		allPageTagsUnique = list(set(allPageTags))
		if (len(allPageTagsUnique) != len(allPageTags)):
			# one or more duplicates exist for this questionnaire
			theQuestWDups = theQuestWDups.append(aQuaire.shortTag)
			thePagesWDups = thePagesWDups.extend(allPageTags)
	if theQuestWDups == []:
		success = True
	else:
		success = False

	return [theQuestWDups, thePagesWDups, success]

def consistencyCheckforTransitionMatrix():
	# Verify the consistency of the transition matrix for all questionnaires
	# verifies that there exists no duplicates in the "from" field for all records belonging
	# to a questionnaire.
	#	Each "from" must go to one and only one "to"
	#	Multiple "from" pages transitioning to a single "to" page is ok.
	# must first pass consistencyCheckUniquePageTagsPerQuestionnaire
	allQuaires = Questionnaire.objects.all()
	theQuestWDups = [] # questionnaires which have duplicate "from" pages
	thePagesWDups = [] # list of page tags with dups
	for aQuaire in allQuaires:
		qpRecs = QuestionnairePage.objects.filter(questionnaireID = aQuaire
			).filter(recordType = 'next_page_default')
		allFromTags = [aRec.pageID.shortTag for aRec in qpRecs] # list all "from" tags
		uniqueFromTags = list(set(allFromTags)) # # list all unique "from" tags
		if (len(allFromTags) != len(uniqueFromTags)):
			# one or more duplicates "from" tags exist for this questionnaire
			# therefore "to" is ambiguous - unless both "to"s are identical. Still an error condition
			theQuestWDups.append(aQuaire.shortTag)
			thePagesWDups.extend(allFromTags)
			
	if theQuestWDups == []:
		success = True
	else:
		success = False

	return [theQuestWDups, thePagesWDups, success]
	
def getPageToPage(theQuestionnaire):
	# retrieves page transition matrix and returns as a dictionary.
	# toPage = pageToPageMap['fromPage']
	DebugOut('getPageToPage:  enter')
	errMsg = []
	success = True # optimism
	whichQuest = theQuestionnaire.shortTag
	DebugOut('whichQuest %s' %whichQuest)
	try:
		thePageToPageMap=QuestionnairePage.objects.filter(
			questionnaireID=theQuestionnaire
		).filter(
			recordType='next_page_default' # select only defaults!!
		)
	except QuestionnairePage.DoesNotExist:
		errMsg.append('No reference to pages can be found for the questionnaire! %s' % whichQuest)
		success = False
		pageToPage = {}
	
	if len(thePageToPageMap) == 0:
		errMsg.append('No pages can be found for the questionnaire! %s' % whichQuest)
		success = False
		pageToPage = {}
	else:
		pageToPage = {}
		for item in thePageToPageMap:
			pageToPage.update({item.pageID.shortTag : item.nextPageID.shortTag})
	DebugOut('getPageToPage:  exit')
	return [pageToPage, success, errMsg]

def getDefaultPageTransitions( theQuestionnaire):
	# convert page transitions to a list to be displayed
	DebugOut('getDefaultPageTransitions:  enter')
	# Find existing page transition table, if any.
	try:
		thePageToPageMap=QuestionnairePage.objects.filter(
			questionnaireID=theQuestionnaire
		).filter(
			recordType='next_page_default' # select only defaults!!
		)
	except QuestionnairePage.DoesNotExist:
		DebugOut('No PT list found in QuestionnairePage')
		thePageToPageMap = ''
		return thePageToPageMap
	defaultPT = []
	if thePageToPageMap:
		DebugOut('Processing PT entries')
		for aLine in thePageToPageMap:
			fromPageTag = aLine.pageID.shortTag
			toPageTag = aLine.nextPageID.shortTag
			defaultPT.append([fromPageTag, toPageTag])
	else:
		DebugOut('PT entries were blank')
	DebugOut('getDefaultPageTransitions:  exit')
	return defaultPT	# Default page transitions
	
def savePTLToDB(theQuestionnaire, ptlLinesRaw):
	"""Replaces the existing page transitions in QuestionnairePage with the tiered list of
	strings in ptlLinesRaw.
	
	Replace the page transition table in QuestionnairePage.
	
	"ptlLinesRaw" is assumed to be entered by a user, so blanks are removed as cleanup.
	
	Args:
		Questionnaire object.
		ptlLinesRaw: a tiered list of page sequences (string with line feeds):  a list of character strings
	
	Database:
		The ptl list is inserted into the QuestionnairePage table

	Returns:
		None. 	

	Raises:
		None.
	"""
	DebugOut('savePTLToDB:  enter')
	[pageTagToRecord, recordToPageTag ] = getPageToRecordMapping(theQuestionnaire) # returns two dictionaries
	DebugOut('pageTagToRecord %s' %str(pageTagToRecord))
	allQuestionnaireTags = set(recordToPageTag.values()) # compare to tags already in the questionnaire
	ptlLines = convertCSVMultiLineTo2DList(ptlLinesRaw) # reformats to List of lists of tags & cleans up
	allInputTags = set(flattenList(ptlLines))
	# Calculate pages missing, and unknown pages added
	tagsAdded = list(allInputTags - allQuestionnaireTags)
	tagsMissing = list(allQuestionnaireTags - allInputTags)
	DebugOut('tagsAdded: %s, tagsMissing: %s' %(tagsAdded,tagsMissing))
	if tagsAdded or tagsMissing: # pages gained or pages lost
		DebugOut('savePTLToDB:  exit1')
		return [tagsMissing, tagsAdded] # no need to continue
	tagsMissing = []# list the records not found in the new QuestionnairePage table. Classify these as orphans
	ptlRecIDList = []
	for aLineList in ptlLines:
		DebugOut('aLineList after split: %s' %aLineList)
		objLine = []
		for aTag in aLineList:
			try:
				theRec = pageTagToRecord[aTag] # convert the tag to a record number
				objLine.append(theRec) # append the record number
			except KeyError:
				DebugOut('syserror:  should already have been found. Tag not found %s' %aTag)
				tagsMissing.append(aTag)
		ptlRecIDList.append(objLine)
	DebugOut('ptlRecIDList: %s' %str(ptlRecIDList))
	# have now a list of a list of record numbers in ptlRecIDList
	
	# all page tags were found, therefore save to database
	DebugOut('savePTLToDB:  all page tags were found') 
	# convert to a transition matrix style
														# input is a list of list of record numbers
	ptlFromTo = transitionListofList_To_FromToList(ptlRecIDList)	# output is a list of from/to list pairs
	DebugOut('ptlFromTo: %s' %str(ptlFromTo))
	# We are sure that all existing pages have a place in the new transition matrix,
	# and that there are no new pages added.
	# Save to QuestionnairePage table, deleting the previous.
	# delete existing records
	QuestionnairePage.objects.filter(
		questionnaireID=theQuestionnaire,
		recordType = 'next_page_default'
		).delete()
# 	# Create a new transition matrix
	for aFromTo in ptlFromTo:
		pageFrom = Page.objects.get(id=aFromTo[0])
		pageTo = Page.objects.get(id=aFromTo[1])
		DebugOut('pageFrom: %s, pageTo: %s' %(pageFrom.shortTag,pageTo.shortTag))
		QuestionnairePage.objects.create(
			questionnaireID=theQuestionnaire,
			pageID = pageFrom,
			nextPageID = pageTo,
			recordType = 'next_page_default',
			)
	tagsAdded = []
	DebugOut('savePTLToDB:  exit2')
	return [tagsMissing, tagsAdded]
	
def retrieveDefaultNextPage(workingQuestionnaireTag, workingPageTag):
	# retrieve the next page
	# use QuestionnairePage query
	try:
		pqList=QuestionnairePage.objects.filter(
			questionnaireID__shortTag=workingQuestionnaireTag,
			pageID__shortTag=workingPageTag,
			recordType='next_page_default',
			)
		
		if pqList:
			pgNext = pqList[0].nextPageID.shortTag # should be only one page
		else:
			DebugOut('syserrormsg:  retrieveDefaultNextPage: No default next page found for Questionnaire "%s" and Page "%s".' %(workingQuestionnaireTag,workingPageTag))
			pgNext = ''
		if len(pqList) > 1:
			DebugOut('syserrormsg:  retrieveDefaultNextPage: pqList contains more than one record')
	except:
		pgNext = ''
		DebugOut('syserrormsg:  retrieveDefaultNextPage: query to QuestionnairePage failed')
	return pgNext
	
def listAllGlobalFlags(workingQuestionnaire):
	# retrieve all possible global flags referenced by any page in a questionnaire
	allPageAnalysisObj = PageAnalysis.objects.filter(
		questionnaireID=workingQuestionnaire)
	allGlobalFlagsDups = [item.testResultFlag for item in allPageAnalysisObj]
	allGlobalFlags = list(set(allGlobalFlagsDups))
	allGlobalFlags.sort()
	# Need to output priority of the global flag
	# ****************************************************************
	return allGlobalFlags

def listGlobalFlagsInfo(workingQuestionnaire):
	# List information for all global flags set by all pages
	allGlobalFlagsRecordDict = getGlobalFlagRecord(workingQuestionnaire)
	# convert to a list
	allGlobalFlagsRecordList = []
	for item in allGlobalFlagsRecordDict:
		# item list structure:  'pageID','testCondition','testResultFlag', 'testResultFlagPriority', 'id'
		ptag = Page.objects.get(id=item['pageID']).shortTag
		allGlobalFlagsRecordList.append([ptag,item['testCondition'],item['testResultFlag'],item['testResultFlagPriority'],item['id']])
	return allGlobalFlagsRecordList

def getTestConditionTransitions(workingQuestionnaire):
	# Retrieve all QuestionnairePage records of type "calculated" owned by questionnaire.
	# output record (list) format:
	# [ record id, page tag, test condition, next page tag]
	DebugOut('getTestConditionTransitions:  enter')

	try:
		qpGlobalFlags = QuestionnairePage.objects.filter(
			questionnaireID = workingQuestionnaire,
			recordType = 'calculated',
			)
		success = True
	except:
		DebugOut('Could not retrieve from QuesionnairePage')
		success = False

	calculatedTransitionList = []
	for aGFlagRec in qpGlobalFlags:
		recID = aGFlagRec.id
		theCondition = aGFlagRec.testCondition
		fromPage = aGFlagRec.pageID.shortTag
		toPage = aGFlagRec.nextPageID.shortTag
		calculatedTransitionList.append([recID,fromPage,theCondition,toPage])

	DebugOut('getTestConditionTransitions:  exit')
	return [calculatedTransitionList, success]

def getGlobalFlagTransitions(workingQuestionnaire):
	# Retrieve all QuestionnairePage records of type "globalFlag" owned by questionnaire.
	# output record (list) format:
	# [ record id, global flag name, page tag, next page tag, global flag priority]
	DebugOut('getGlobalFlagTransitions:  enter')

	try:
		qpGlobalFlags = QuestionnairePage.objects.filter(
			questionnaireID = workingQuestionnaire,
			recordType = 'globalFlag',
			)
		success = True
	except:
		DebugOut('Could not retrieve from QuesionnairePage')
		success = False

	globalFlagTransitionList = []
	for aGFlagRec in qpGlobalFlags:
		recID = aGFlagRec.id
		gFlagName = aGFlagRec.testCondition
		DebugOut('Global Flag name:  %s' %gFlagName)
		fromPage = aGFlagRec.pageID.shortTag
		toPage = aGFlagRec.nextPageID.shortTag
		[gFlagPriority, gFlagDescription, successforThisFlag] = getGlobalFlagPriority(workingQuestionnaire,gFlagName)
		if not successforThisFlag:
			DebugOut('No priority found for flag %s' %gFlagName)
		else:
			DebugOut('Global Flag priority:  %s' %gFlagPriority)
		globalFlagTransitionList.append([recID,gFlagName,fromPage,toPage,gFlagPriority,gFlagDescription])
	
	DebugOut('getGlobalFlagTransitions:  exit')
	return [globalFlagTransitionList, success]

def getGlobalFlagRecord(workingQuestionnaire):
	"""Retrieve all PageAnalysis records owned by questionnaire."""
	# May be zero records
	DebugOut('getGlobalFlagRecord:  enter')
	pageAnalObjs = PageAnalysis.objects.filter(
		questionnaireID = workingQuestionnaire,
		)
	if len(pageAnalObjs) == 0:
		DebugOut('Zero records retrieved from the database. Normal')
		pageAnalysisDict = {}
	else:
		pageAnalysisDict = pageAnalObjs.values('pageID','testCondition','testResultFlag', 'testResultFlagPriority','id')
	DebugOut('getGlobalFlagRecord:  exit')
	return pageAnalysisDict

def deleteGlobalFlagRecord(workingQuestionnaire, recNum):
	# Delete a single PageAnalysis records owned by questionnaire.
	DebugOut('deleteGlobalFlagRecord:  enter')
	try:
		PageAnalysis.objects.get(id=recNum).delete()
		DebugOut('Deleted existing PageAnalysis record %s' %recNum)
	except: # so create it.
		DebugOut('Failed to delete record %s' %recNum)
		return False
	DebugOut('deleteGlobalFlagRecord:  exit')
	return True

# getPageConditionsToSetGlobalFlag is unused as of Tuesday, November 19, 2013
def getPageConditionsToSetGlobalFlag(workingQuestionnaire, workingPage):
	# Retrieve all PageAnalysis records owned by questionnaire.
	DebugOut('getPageConditionsToSetGlobalFlag:  enter')
	try:
		globalFlagSetConditionsObj = PageAnalysis.objects.filter(
			questionnaireID = workingQuestionnaire,
			pageID = workingPage,
			)
		DebugOut('Retrieved existing PageAnalysis record')
	except PageAnalysis.DoesNotExist: # so create it.
		DebugOut('Could not retrieve from the database')
	pageAnalysisDict = globalFlagSetConditionsObj.values('testCondition','testResultFlag')
	DebugOut('getPageConditionsToSetGlobalFlag:  exit')
	return pageAnalysisDict

def createGlobalFlagRecord(workingQuestionnaire, theWorkingPage, testCondition, globalAnalFlag, theGlobalFlagPriority, theGlobalFlagDescription):
	# save the condition and the global flag to PageAnalysis
	# Don't duplicate the record
	# get the test condition in a standard form which is independent of question order
	testConditionSorted = str(sorted(testCondition.items()))
	DebugOut('createGlobalFlagRecord:  enter')
	try: # try to find the identical record
		pageAnalObj = PageAnalysis.objects.get(
			questionnaireID = workingQuestionnaire,
			pageID = theWorkingPage,
			testCondition = testConditionSorted,
			testResultFlag = globalAnalFlag,
			testResultFlagPriority = theGlobalFlagPriority,
			testResultFlagDescription = theGlobalFlagDescription,
			)
		# pageAnalObj.save() # don't save - identical
		DebugOut('Did not update existing identical PageAnalysis record')
	except PageAnalysis.DoesNotExist: # Does not exist, so create it.
		DebugOut('Create the PageAnalysis record')
		pageAnalObj = PageAnalysis.objects.create(
			questionnaireID = workingQuestionnaire,
			pageID = theWorkingPage,
			testCondition = testConditionSorted,
			testResultFlag = globalAnalFlag,
			testResultFlagPriority = theGlobalFlagPriority,
			testResultFlagDescription = theGlobalFlagDescription,
			)
		DebugOut('Saved analysis condition to the database')
	except:
		DebugOut('syserrmsg:  Read or write to PageAnalysis failed!')
	DebugOut('createGlobalFlagRecord:  exit')
	return True

def getGlobalFlagPriority(workingQuestionnaire, theGlobalFlag):
	# Get priority for flag
	DebugOut('getGlobalFlagPriority:  enter')
	resWithFlag = PageAnalysis.objects.filter(
		questionnaireID = workingQuestionnaire,
		testResultFlag = theGlobalFlag,
		)
	# Select the first entry since all the flags should be the same
	if len(resWithFlag) == 0:
		flagPriority = '' # no priority specified
		flagDescription = ''
		success = False
		DebugOut('No global flag found for %s' %theGlobalFlag)
	else:
		flagPriority = resWithFlag[0].testResultFlagPriority
		flagDescription = resWithFlag[0].testResultFlagDescription # may be blank
		success = True
	DebugOut('getGlobalFlagPriority:  exit')
	return [flagPriority, flagDescription, success]


def getTestConditionFromQuestionnairePage(questionnaireObj, pageObj):
	# retrieve the testCondition required to transition to page nextPage.
	# Needed:  QuestionnairePage
	# first test for prior existence of the test flag
	# there are three different "next pages":  next_page_default, question response directed, globalFlag directed
	# this is "question response directed"
	# can be multiple conditions per page
	recordType = 'calculated'
	qp = QuestionnairePage.objects.filter(
		pageID = pageObj
		).filter(
		questionnaireID = questionnaireObj
		).filter(
		recordType = recordType
		)

	testConditionTransitionList=[
		[
		item.id,
		item.testCondition,
		item.nextPageID.shortTag,
		] for item in qp]

	return testConditionTransitionList

def deleteTestConditonFromQuestionnairePage(recSelect):
	# deletes the testCondition required to transition to page nextPage
	# deletes the record in QuestionnairePage
	QuestionnairePage.objects.filter(id=recSelect).delete()
	return True
	
def saveTestConditonToQuestionnairePage(testConditionInput, nextPageObj, pageObj, questionnaireObj, recordType):
	# saves the testCondition required to transition to page nextPageTag
	# Writes global flag (as "testCondition") and next page to QuestionnairePage
	# first test for prior existence of the test flag in QuestionnairePage
	# Do not duplicate a record! Multiples will break getNextPageFromGlobalFlags
	# there are three different "next pages":  next_page_default, question response directed, globalFlag directed
	
	if recordType == 'calculated':
		# prepare the testCondition in a standard format
		testCondition = str(sorted(testConditionInput.items()))
	else:
		testCondition = testConditionInput
	qp = QuestionnairePage.objects.filter(
		pageID = pageObj
		).filter(
		questionnaireID = questionnaireObj
		).filter(
		testCondition = testCondition # is the "global flag" when record type = 'globalFlag'
		).filter(
		nextPageID = nextPageObj
		).filter(
		recordType = recordType
		)

	if qp.count() == 0: # condition does not already exist, so add it
		QuestionnairePage.objects.create(
			pageID = pageObj,
			questionnaireID = questionnaireObj,
			testCondition = testCondition,
			nextPageID = nextPageObj,
			recordType = recordType
			)
	return True

def getPageObjectFromTags(theProjectTag, theQuestionnaireTag, thePageTag): # *** not used
	"""Output is an object of type "Page", given the project, questionnaire and page tags.

	Args:
		Questionnaire object: workingQuestionnaire.

	Returns:
		QuerySet: of type Page 	

	Raises:
		None
	"""
	questObj = getQuestionnaireObjFromTags( theProjectTag, theQuestionnaireTag)
	[thePageObj, success] = getPageObj(questObj, thePageTag)
	return [thePageObj,success]
	
def displayAllPageInfo(allPages):
	"""Output is a table of page information ready to display.
	
	Logic must closely follow getAllPageObjsInQuestionnaires
	Args:
		None
	
	Returns:
		QuerySet: of type Questionnaire 	
	
	Raises:
		None
	"""
	colList = ['Page Tag','Description (not displayed)','Explanation','Prologue',
		'Epilogue','Language','Page Type', 'Last Updated']
	
	# get all QuestionnairePage records
	allQPs = QuestionnairePage.objects.all() # filter this query set
	allValuesUnsorted = []
	pageRecordDict = {}
	for (iRec,pageObj) in enumerate(allPages):
		# in which questionnaires does this page appear?
# 		list1 = allQPs.filter(pageID=pageObj) # this page is the "from" page
# 		list1Str = ["("+aQP.questionnaireID.shortTag+", "+str(aQP.questionnaireID.projectID)+")" for aQP in list1]
# 		list2 = allQPs.filter(nextPageID=pageObj) # this page is the "nextPage"
# 		list2Str = ["("+aQP.questionnaireID.shortTag+", "+str(aQP.questionnaireID.projectID)+")" for aQP in list2]
# 		allQuestionnairesWRedundancies = list1Str + list2Str # concatenate the two lists
# 		questList = list(set(allQuestionnairesWRedundancies)) # eliminate redundancies
# 		# questList is a list of all questionnaires which reference this page object.
# 		# make a single string
# 		tagListStr = ', '.join(questList)
		pageRecordDict.update({iRec:pageObj.id}) # useful when selecting
		rowValues = [
			pageObj.shortTag,	# 0
			pageObj.description,	# 1
			pageObj.explanation,	# 2
			pageObj.prologue,	# 3
			pageObj.epilogue,	# 4
			pageObj.language,	# 5
			pageObj.pageType,	# 6
			pageObj.lastUpdate,	# 7
#			tagListStr, # list of all questionnaires which reference this page object
			]
		allValuesUnsorted.append(rowValues)
	allValues = sorted( allValuesUnsorted, key=itemgetter(0,7))
	return [allValues, colList, pageRecordDict ]

def getCompleteListQuestionnairesReferencingAPage( pageObj ):
	"""Output is a QuerySet of objects of type "Questionnaire" which reference the given Page object.
	
	This function differs from getAllQuestionnairesReferencingAPage since all
	Questionnaires are listed, regardless of whether active or not.
	Args:
		Page object: aPageObj.

	Returns:
		QuerySet: of type Questionnaire 	

	Raises:
		None
	"""
	# get all QuestionnairePage records
	allQPs = QuestionnairePage.objects.all() # filter this query set
	# in which questionnaires does this page appear?
	list1 = allQPs.filter(pageID=pageObj) # this page is the "from" page
	fromIDlist1 = [aQP.questionnaireID.id for aQP in list1]
	list2 = allQPs.filter(nextPageID=pageObj) # this page is the "nextPage"
	toIDlist2 = [aQP.questionnaireID.id for aQP in list2]
	sumLists = fromIDlist1 + toIDlist2
	uniqueIDSet = list(set(sumLists))
	if len(uniqueIDSet) == 0: # no Questionnaire, so return empty queryset
		allUniqueQuestionnaires = Questionnaire.objects.none() # initialize
	else:
		allUniqueQuestionnaires = retrieveBulk( Questionnaire, uniqueIDSet )
	return allUniqueQuestionnaires

def getAllQuestionnairesReferencingAPage( pageObj ):
	"""Output is a QuerySet of objects of type "Questionnaire" which reference the given Page object.

	Logic must closely follow getAllPageObjsInQuestionnaires, therefore, only
	"active" questionnaires are listed.
	Args:
		Page object: aPageObj.

	Returns:
		QuerySet: of type Questionnaire 	

	Raises:
		None
	"""
	allQsRef = getCompleteListQuestionnairesReferencingAPage( pageObj )
	# create integer id list
	uniqueIDSet = set([aQ.id for aQ in allQsRef])
	# make sure this is one of the active questionnaires (not just a Response pointing to it)
	allQuestionnaires = getAllQuestionnaires()
	allQuestionnairesIDs = set([aQ.id for aQ in allQuestionnaires])
	# intersect the two sets
	allIDs = list(set.intersection(uniqueIDSet,allQuestionnairesIDs))
	# have list of record IDs, turn into a QuerySet
	if allIDs:  # non null list
		queryOR = Q(id=allIDs[0])
		for anID in allIDs[1:]:
			queryOR = queryOR | Q(id=anID)
		questToPage = allQuestionnaires.filter(queryOR)
	else:
		questToPage = Questionnaire.objects.none()
	return questToPage

def	getQuestionnaireforEditing( theProject, qTag ):
	"""Returns a Questionnaire object ready for editing.

	If the record id exists, then no Submission points to Questionnaire.
	If the record id does not exist, then a Submission points to Questionnaire.
	A subsequent "save" will create a new record.
	Duplicates a questionnaire if saved while a Submission points to it.

	Args:
		Questionnaire short tag: qTag.

	Returns:
		Questionnaire:  single object provided for editing 	

	Raises:
		None
	"""
	# find questionnaire object in database Questionnaire table with tag qTag
	# There must be only one questionnaire with the tag "qTag", so find latest
	
	try:
		qObj = Questionnaire.objects.filter(
			shortTag = qTag,
			projectID = theProject,
			).latest('lastUpdate')
		# get any Submission record which points to this object.
		# search for a Session record pointing to the Questionnaire object
		try:
			aSub = Submission.objects.filter(
				questionnaireID = qObj,
				).latest('lastUpdate')
			# Submission record exists
			submissionDate = aSub.lastUpdate
			# duplicate the Questionnaire record
			qObj.id = None # any subsequent "save" of this object will create a new record.
			success = True
		except Submission.DoesNotExist:
			# Not referenced by a Submission record, so safe to Edit record
			# do nothing further
			success = True
	except Questionnaire.DoesNotExist:
		# error in accessing Questionnaire to be deleted.
		errMsg = 'Questionnaire "%s" not found' %qTag
		success = False
		qObj = Questionnaire.objects.none()
	
	return qObj

def listQuestionnaireSubmissions( theQuestionnaire ):
	"""Returns queryset of Submissions lodged against this Questionnaire.

	Args:
		a Questionnaire object

	Returns:
		return_value: a queryset of Submission records. 	

	Raises:
		None.
	
	Side effects: No records deleted or modified.
	Tables accessed:
		Questionnaire:  single record deleted
		QuestionnairePage:  Cascade option implies that transition matrix is deleted.
		PageAnalysis:  Cascade option implies that records are deleted.
		Submission:  NO RECORDS ARE DELETED
	"""
	# search for Submission records pointing to the Questionnaire object
	aSub = Submission.objects.filter(
		questionnaireID = theQuestionnaire,
		).order_by('lastUpdate')
	return aSub

def listQuestionnairePageSharing( theQuestionnaire):
	"""Detects whether any of the elements of a Questionnaire are shared with other
	Questionnaires..

	Args:
		a Questionnaire object

	Returns:
		return_value: a queryset of Submission records. 	

	Raises:
		None.
	
	Side effects:
	Tables affected:
		Questionnaire:  single record deleted
		QuestionnairePage:  Cascade option implies that transition matrix is deleted.
		PageAnalysis:  Cascade option implies that records are deleted.
		Submission:  NO RECORDS ARE DELETED
	"""
	# retrieve all the objects from this questionnaire.
	allPages = getAllPageObjsForQuestionnaire(theQuestionnaire)
	

	return

def deleteQuestionnaireInDB( theQuestionnaire ):
	"""Deletes questionnaire unless a submission points to it.
	
	This function returns a list

	Args:
		a Questionnaire object

	Returns:
		return_value: "Success' flag. 	

	Raises:
		None.
	
	Side effects:
	Tables affected:
		Questionnaire:  single record deleted
		QuestionnairePage:  Cascade option implies that transition matrix is deleted.
		PageAnalysis:  Cascade option implies that records are deleted.
		Submission:  NO RECORDS ARE DELETED
	"""
	# find questionnaire object in database Questionnaire table.
	# Must not be any Submission pointers to Questionnaire record.
	# List the date of the most recent Submission
	
	errMsg = []
	# search for a Submission record pointing to the Questionnaire object
	qTag = theQuestionnaire.shortTag
	aSub = Submission.objects.filter(
		questionnaireID = theQuestionnaire,
		)
	if aSub.count() != 0:
		# Submission record exists
		submissionDate = aSub.lastUpdate
		success = False
		errMsg.append('Cannot delete quesionnaire "%s", since at least one submission dated %s references it' %(qTag,submissionDate))
		# do nothing
	else:
		# Not referenced by a Submission record, so safe to delete.
		theQuestionnaire.delete()
		success = True
		
	return [success, errMsg]
	
def getAllPageTags(workingQuestionnaire):
	"""Return a list of all page tags belonging to the questionnaire.
	Extract from the page transition table in QuestionnairePage
	Function dependencies:
		getAllPageObjsForQuestionnaire
		
	"""
	allPageObjs = getAllPageObjsForQuestionnaire(workingQuestionnaire)
	if allPageObjs:
		allPageTags = [item.shortTag for item in allPageObjs]
		allPageTags.sort()
	else: # no pages
		allPageTags = ''
	return allPageTags
	
def findAllPagesWQuestions(workingQuestionnaire):
	"""return a list of all page Objects, which have questions, belonging to the questionnaire"""
	# extract from the page transition table in QuestionnairePage
	# 
	allPageObjsForQuestionnaire = getAllPageObjsForQuestionnaire(workingQuestionnaire)
	# check each for questions
	pagesWQuestions = [] # integer page ids
	for aPageObj in allPageObjsForQuestionnaire:
		questCount=PageQuestion.objects.filter(pageID=aPageObj).count()
		aPageID = aPageObj.id
		if questCount != 0:
			pagesWQuestions.append(aPageID)
	
	# Make a queryset
	pagesWQuestionsObjs = retrieveBulk( Page, pagesWQuestions )
	return pagesWQuestionsObjs

def findAllPageObjWQuestions(workingQuestionnaire):
	"""return a queryset of all page objects (which have questions) belonging to the questionnaire"""
	allPageObjsForQuestionnaire = getAllPageObjsForQuestionnaire(workingQuestionnaire)
	# check each for questions
	allPageIDs = [] 
	for aPageObj in allPageObjsForQuestionnaire:
		questCount=PageQuestion.objects.filter(pageID=aPageObj).count()
		apageID = aPageObj.id
		if questCount != 0:
			allPageIDs.append(apageID)
	# have list of record IDs, turn into a QuerySet
	if allPageIDs:  # non null list
		queryOR = Q(id=allPageIDs[0])
		for aPageID in allPageIDs[1:]:
			queryOR = queryOR | Q(id=aPageID)
		allPageIDQuerySet = Page.objects.filter(queryOR)
	else:
		allPageIDQuerySet = Page.objects.none()
	
	return allPageIDQuerySet
