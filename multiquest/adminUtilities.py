# This Python file uses the following encoding: utf-8

# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context
from django.shortcuts import render_to_response, render, get_object_or_404
from django.conf import settings
from django import forms
from multiquest.forms import *
from multiquest.models import *
from datetime import datetime
#from dateutil.relativedelta import relativedelta
from django.utils.safestring import mark_safe
from django.utils.encoding import smart_text
from django.utils.timezone import *
#from multiquest.utilities_db import getAllProjects, getPageObjectViaTag, getModelFieldList, getModelFieldValueDict
from multiquest.utilities_db import *
from multiquest.utilities import *
from django.db import connection
import os
import pickle
import codecs

import csv
import unicodedata

tupd = '2014-02-15T15:00:00+07:00' # time zone aware time update


# Functions which analyze the database and Questionnaires

def checkAllQuestionnaireSharing():
	allQuestionnaires = Questionnaire.objects.all()
	# viewed results
	questTested = []
	for aQ1 in allQuestionnaires:
		questTested.append(aQ1)
		for aQ2 in allQuestionnaires:
			if aQ2 not in questTested:
				checkPageSharing(aQ1,aQ2)
	return
	
def checkPageSharing(quest1,quest2):
	# output is a queryset of shared pages
	messOut = 'Find elements shared between two questionnaires %s (%s) and %s (%s)'%(quest1.shortTag,quest1.id,quest2.shortTag,quest2.id)
	print messOut
	allPages1 = getAllPageObjsForQuestionnaire(quest1)
	allPages2 = getAllPageObjsForQuestionnaire(quest2)
	# collect record numbers
	pRecs1=set([ap.id for ap in allPages1])
	pRecs2=set([ap.id for ap in allPages2])
	mutualids = list(set.intersection(pRecs1,pRecs2))
	mutualPages = retrieveBulk( Page, mutualids )
	for aSharedPage in mutualPages:
		messOut = 'Page shared: "%s", rec: %s' %(aSharedPage.shortTag,aSharedPage.id)
		print messOut
	if not mutualPages:
		messOut = 'No Pages shared'
		print messOut
	return mutualPages
	
def listTestConditons(theQuestionnaire):

	return
	
def updateNullChoiceTags():
	""" update question and responsechoice null short tags
	"""
	allQ = Question.objects.all()
	for aq in allQ:
		if aq.questionTag == '':
			aq.questionTag = 'Quest_%s'%aq.id
			print('new question tag: %s'%aq.questionTag )
# 			aq.save()
	allRC = ResponseChoice.objects.order_by('choiceSequence').all()
	for rc in allRC:
		if rc.choiceTag == '':
			rc.choiceTag = 'Choice_%s'%rc.id
			print('new choice tag: %s'%rc.choiceTag )
# 			rc.save()
	return

def updateChoiceSequenceAndTags():

	allQ = Question.objects.all()
	for aq in allQ:
		print 'Question tag: "%s"'%aq.questionTag
		rcOnPage = ResponseChoice.objects.order_by('choiceSequence').filter(questionID=aq)
		for aChoice in rcOnPage:
			print 'Choice tag/Seq/typ: "%s/%s/%s"'%(aChoice.choiceTag,aChoice.choiceSequence,aChoice.choiceType)
# 			aChoice.choiceType = 'notUsed'
# 			aChoice.save()
			
	return


def choiceUniqueTagCheck():
	allQ = Question.objects.all()
	for aq in allQ:
		# get all choices for a question
		allChoices = ResponseChoice.objects.filter(id=aq.id)
		allChoiceTags = [ac.choiceTag for ac in allChoices]
		allChoiceTagsUnique = list(set(allChoiceTags))
		numDups = len(allChoiceTags) - len(allChoiceTagsUnique)
		if numDups != 0:
			print 'Question "%s/%s" has duplicate choice tags.'%(aq.questionTag,aq.id)
	return

def dumpTableTest():
	tableName = 'Page'
	theTable = Page
	fileName = 'test dump/%s.txt' %tableName
	fileOut = codecs.open(fileName,'w', encoding='utf-8')
	dumpSelectedTable(fileOut, theTable)
	fileOut.close()
	return


def doTestDumps():
	theProjectTag='test_project'
	theQuestionnaireTag='TestQuest'
	doSQDumps(theProjectTag,theQuestionnaireTag)
	return


def doSQDumps(theProjectTag,theQuestionnaireTag):
	"""Dump selected project and questionnaire from database to file.
	"""
	# initialize error log
	ferrLog = open('db dump/ErrorLog.txt','w')
	ferrLog.close()
#	deleteDatabaseLoad() # delete previous file contents in the database
	dumpSelectedProject(theProjectTag)
	dumpUserProject()
	dumpSelectedQuestionnaire(theProjectTag, theQuestionnaireTag)
	dumpProjectQuestionnaire()
	dumpPage()
	dumpQuestionnairePage()
	dumpQuestion()
	dumpPageQuestion()
	dumpResponseChoice()
	dumpPageAnalysis()
	return
	
def doAllDumps():
	"""Dump database to text files.
	"""
	# initialize error log
	ferrLog = open('db dump/ErrorLog.txt','w')
	ferrLog.close()
#	deleteDatabaseLoad() # delete previous file contents in the database
	dumpAllProjects()
	dumpUserProject()
	dumpAllQuestionnaires()
	dumpProjectQuestionnaire()
	dumpPage()
	dumpQuestionnairePage()
	dumpQuestion()
	dumpPageQuestion()
	dumpResponseChoice()
	dumpPageAnalysis()
	return

def deleteNewProjects():
	""" Delete new Projects and Questionnaires due to overzealousness. Shouldn't have created
	so many so soon.
	"""
	projectList=[
# 		'Lavender',
		'Magenta',
# 		'Gray',
# 		'Blue',
# 		'Green',
# 		'Cyan',
# 		'Coral',
# 		'Cerulean',
# 		'Pink',
# 		'Red',
# 		'Purple',
# 		'Mauve',
# 		'Puce',
# 		'Taupe',
# 		'Eggplant',
# 		'Eggshell',
# 		'Scarlet',
# 		'Amber',
# 		'Orange',
# 		'Vermillion',
		]		
	for aProjectTag in projectList:
		theProject = getProjectObj( aProjectTag)
		recNum = theProject.id
		allQuestionnaires = getAllQuestionnareObjForProject(theProject)
		for aQuestionnaire in allQuestionnaires:
			deleteQuestionnaire(aQuestionnaire)
		# delete the project
		Project.objects.get(id=recNum).delete()
	return

def checkQuestionSequenceOnPage():
	allPages = Page.objects.all()
	for aPage in allPages:
		# find a sequence value
		thePageQuestions=PageQuestion.objects.filter(pageID=aPage)
		# check for redundancies in the sequence data
		seqList = [aPQ.questionSequence for aPQ in thePageQuestions]
		numRedundant = len(seqList) - len(list(set(seqList)))
		if numRedundant:
			print 'for page %s, the sequence list: %s'%(aPage.shortTag,str(seqList))
		if len(seqList) != len(thePageQuestions):
			print 'for page %s, sequence list does not list count: %s'%(aPage.shortTag,str(seqList))
	return

def dumpSubmissions():
	allSubmissions = Submission.objects.all()
	frec = codecs.open('submissionDump.txt','w', encoding='utf-8')
	now = str(timezone.now())[:19]
	frec.write('Dump Submissions. Time: %s  Comma delimited fields follow:\n'%now)
	frec.write('Questionnaire short name, Respondent name, Respondent email, Submission date\n')
	for aSub in allSubmissions:
		qName = aSub.questionnaireID.shortTag
		respRec = aSub.respondentID
		respName = respondentName( respRec )
		email = respRec.contactEmail
		rDate = str(aSub.lastUpdate)[:19]
		wLine = qName + ', ' + respName + ' ' + email + ' ' + rDate
		frec.write(wLine + '\n')
	frec.close()
	return

def createNewProjects():
	""" Create new Projects and Questionnaires for class
	"""
	projectList=[
		'Lavender',
		'Magenta',
		'Gray',
		'Blue',
		'Green',
		'Cyan',
		'Coral',
		'Cerulean',
		'Pink',
		'Red',
		'Purple',
		'Mauve',
		'Puce',
		'Taupe',
		'Eggplant',
		'Eggshell',
		'Scarlet',
		'Amber',
		'Orange',
		'Vermillion',
		]		
	# create the projects in the database - if they don't already exist!!
	theQuestionnaire = getQuestionnaireObjFromTags('PAMF','BRCA_S') # to be copied
	tQuest = getQuestionnaireObjFromTags('test_project','TestQuest')
	oldProjectP=getProjectObj('PAMF')
	oldProjectT=getProjectObj('test_project')
	setEnabledFlag = 'enabled'
	for aProjectTag in projectList:
		# check for prior existence of the short tag
		spCount = Project.objects.filter(shortTag=aProjectTag).count()
		if spCount == 0: # If it does not exist then create it
			newProject = Project.objects.create(
				shortTag=aProjectTag,
				abbrev=aProjectTag,
				name='A colorful project:  %s'%aProjectTag,
				projectAddress='UCSC',
				)
			print 'Project %s created' %aProjectTag
			newQPAMF = duplicateQuestionnaire(newProject, theQuestionnaire, 'BRCA_S')
			setQuestionnaireStatusValue(newProject, newQPAMF, setEnabledFlag)
			newQPAMF2=duplicateQuestionnaire(newProject, tQuest, 'SampleQuestionnaire')
			setQuestionnaireStatusValue(newProject, newQPAMF2, setEnabledFlag)
		else:
			print 'Project %s already exists' %aProjectTag
		# Otherwise skip it
	return

def doAllLoads():
	"""Load database from text files.
	"""
	# initialize error log
	ferrLog = open('db dump/ErrorLog.txt','w')
	ferrLog.close()
#	deleteDatabaseLoad() # delete the previous!!!
	loadProject()
	loadUserProject()
	loadQuestionnaire()
	loadProjectQuestionnaire()
	loadPage()
	loadQuestionnairePage()
	loadQuestion()
	loadPageQuestion()
	loadResponseChoice()
	loadPageAnalysis()
	return


def deleteOrphanPages():
	allPages = Page.objects.all()
	allQPs = QuestionnairePage.objects.filter(
		recordType='next_page_default',
		)
	for aPage in allPages:
		queryOR = Q(pageID=aPage) | Q(nextPageID=aPage)
		queryAll = Q(recordType='next_page_default') & queryOR
		recsWithPage = QuestionnairePage.objects.filter(queryAll)
		# count the questionnaires which have this page.
		iCount = recsWithPage.count()
		if iCount == 0:
			print 'Page %s is not shared by any Questionnaires' %aPage.shortTag
			queryOR = Q(pageID=aPage) | Q(nextPageID=aPage)
			queryAll = Q(recordType='calculated') & queryOR
			recsWithCalc = QuestionnairePage.objects.filter(queryAll)
			iCount = recsWithCalc.count()
			if iCount:
				print 'Page %s has calculated transitions' %aPage.shortTag
			queryOR = Q(pageID=aPage) | Q(nextPageID=aPage)
			queryAll = Q(recordType='globalflag') & queryOR
			recsWithGlob = QuestionnairePage.objects.filter(queryAll)
			iCount = recsWithGlob.count()
			if iCount:
				print 'Page %s has global flag transition' %aPage.shortTag
			print 'Page %s deleted ******************************************' %aPage.shortTag
			aPage.delete()
	return

def deleteOrphanQuestions():
	allQuest = Question.objects.all()
	for aQuestion in allQuest:
		PQCount = PageQuestion.objects.filter(
			questionID = aQuestion,
			).count()
		if PQCount == 0:
			# not referenced by any page
			print 'Question %s (record: %s) not referenced by any page, so delete' %(aQuestion.questionTag,aQuestion.id)
			aQuestion.delete()
	return
	
def deleteQuestionnairesWithoutQuestions():
	allQuest = Questionnaire.objects.all()
	for aQuest in allQuest:
		iCount = QuestionnairePage.objects.filter(
			questionnaireID=aQuest,
			)
		if iCount == 0:
			# no questions assigned to the questionnaire
			print 'Questionnaire %s has no questions' %aQuest.shortTag
			aQuest.delete() # test first
			print 'Questionnaire %s deleted *************************************' %aQuest.shortTag
	return	

# deleteOrphanQuestions()
# deleteOrphanPages()
# deleteQuestionnairesWithoutQuestions()


def comprehensiveQuestionnaireProjectList():
	"""Display the Projects and Questionnaires.
	Note any pages or questions not belonging to a Questionnaire
	"""
	# tally totals
	# Projects
	allProjects = Project.objects.all()
	# Questionnaires
	allQuests = Questionnaire.objects.all()
	allQIDs = [aq.id for aq in allQuests]
	# Pages
	allPagesSystemWide = Page.objects.all()
	allPagesSystemWideIDs = [aq.id for aq in allPagesSystemWide]
	# Questions
	allQuestionsSystemWide = Question.objects.all()
	allQuestionsSystemWideIDs = [aq.id for aq in allQuestionsSystemWide]
	
	displayedQuestionnaireIDs = []
	displayedPageIDs = []
	displayedQuestionIDs = []
	analOut = codecs.open('db dump/systemAnalysis.txt','w', encoding='utf-8')
	messOut = "Project Tag,  Project ID, Questionnaire Tag, Questionnaire ID"
	analOut.write(messOut+"\n")
	print messOut
	bigSpace = '                 '
	for aProject in allProjects:
		projTag = aProject.shortTag
		projID = aProject.id
		questionnairesForThisProject = getAllQuestionnareObjForProject(aProject)
		if len(questionnairesForThisProject) == 0:
			messOut = 'No questionnaire in this project:'+projTag
			analOut.write(messOut+"\n")
			print messOut
		for aQuestionnaire in questionnairesForThisProject:
			questTag = aQuestionnaire.shortTag
			questID = aQuestionnaire.id
			displayedQuestionnaireIDs.append(questID)
			messOut = projTag +' '+ str(projID) +' '+ questTag +' '+ str(questID)
			analOut.write(messOut+"\n")
			print messOut
			allPages = getAllPageObjsForQuestionnaire(aQuestionnaire)
			if len(allPages)==0:
				messOut = bigSpace+'No pages in this questionnaire:'+questTag
				analOut.write(messOut+"\n")
				print messOut
			for aPage in allPages:
				PageTag = aPage.shortTag
				PageID = aPage.id
				displayedPageIDs.append(PageID)
				messOut = bigSpace+'Page tag: %s Rec num: %s' %(PageTag,PageID)
				analOut.write(messOut+"\n")
				print messOut
				allQuestions = getPageQuestions( aPage)
				if len(allQuestions) == 0:
					messOut = bigSpace+bigSpace+'No Questions in this Page: '+PageTag
					analOut.write(messOut+"\n")
					print(messOut)
				for aQuestion in allQuestions:
					displayedQuestionIDs.append(aQuestion.id)
					messOut = bigSpace+bigSpace+'Question tag: %s Rec num: %s' %(aQuestion.questionTag,aQuestion.id)
					analOut.write(messOut+"\n")
					print messOut
				
	# any Questionnaires not displayed? Any orphans?
	missingIDs = list(set(allQIDs) - set(displayedQuestionnaireIDs))
	if len(missingIDs) >0:
		messOut = 'There exist missing questionnaires not in any Project'
		analOut.write(messOut+"\n")
		print messOut
		messOut = 'Questionnaire Tag'+' '+'Questionnaire ID'
		analOut.write(messOut+"\n")
		print messOut
	else:
		messOut = 'All questionnaires belong to a project'
		analOut.write(messOut+"\n")
		print messOut
	for anID in missingIDs:
		missingQuest = allQuests.get(id=anID)
		messOut = missingQuest.shortTag+' '+str(missingQuest.id)
		analOut.write(messOut+"\n")
		print messOut
		
	# any Pages not displayed? Any orphans?
	missingIDs = list(set(allPagesSystemWideIDs) - set(displayedPageIDs))
	if len(missingIDs) >0:
		messOut = 'There exist missing pages not in any Questionnaire'
		analOut.write(messOut+"\n")
		print messOut
		messOut = 'Page Tag'+' '+'Page ID'
		analOut.write(messOut+"\n")
		print messOut
	else:
		messOut = 'All pages belong to a Questionnaire'
		analOut.write(messOut+"\n")
		print messOut
	for anID in missingIDs:
		missingQuest = allPagesSystemWide.get(id=anID)
		messOut = missingQuest.shortTag+' '+str(missingQuest.id)
		analOut.write(messOut+"\n")
		print messOut

	# any Questions not displayed? Any orphans?
	missingIDs = list(set(allQuestionsSystemWideIDs) - set(displayedQuestionIDs))
	if len(missingIDs) >0:
		messOut = 'There exist missing Questions not in any Page'
		analOut.write(messOut+"\n")
		print messOut
		messOut = 'Question Tag'+' '+'Question ID'
		analOut.write(messOut+"\n")
		print messOut
	else:
		messOut = 'All Questions belong to a Page'
		analOut.write(messOut+"\n")
		print messOut
	for anID in missingIDs:
		missingQuest = allQuestionsSystemWide.get(id=anID)
		messOut = missingQuest.questionTag+' '+str(missingQuest.id)
		analOut.write(messOut+"\n")
		print messOut
	return

def listAllQuestionsAndPagesInQuestionnarie(workingQuestionnaire):
	"""Display the Projects and Questionnaires.
	"""
	allPages = getAllPageObjsForQuestionnaire(workingQuestionnaire)
	if len(allPages) == 0:
		messOut = 'No pages in questionnarie'
		analOut.write(messOut)
		print messOut
	for aPage in allPages:
		pTag = aPage.shortTag
		pRec = aPage.id
		messOut = 'Page: %s with id %s' %(pTag,pRec)
		allQsInPage = getPageQuestions( aPage)
		for aQu in allQsInPage:
			qTag = aQu.questionTag
			qRec = aQu.id
			messOut = '       Question: %s with id %s' %(qTag,qRec)
	return

def deleteDatabaseLoad():
	"""Database load files must still be present.
	"""
	# Delete Project records
	try:
		projectRecDecode = open('db dump/ProjectRecDecode.txt','r') # record old and new records
		print 'deleting project records'
		for aRec in projectRecDecode:
			[oldRecordID,newRecordID] = aRec.split(',')
			newRecordID = int(newRecordID)
			try:
				aShortTag = Project.objects.get(id=newRecordID).shortTag
				try:
					Project.objects.get(id=int(newRecordID)).delete()
					print "Deleting Project record %s with tag %s." %(newRecordID,aShortTag)
				except Project.DoesNotExist:
					print "Project record %s with tag %s not found" %(newRecordID,aShortTag)
			except Project.DoesNotExist:
				aShortTag = ''
		projectRecDecode.close()
	except IOError:
		pass
	
	# Delete Questionnaire records
	print 'deleting questionnaire records'
	try:
		fQRecDecode = open('db dump/QuestionnaireRecDecode.txt','r')
		for aRec in fQRecDecode:
			[oldRecordID,newRecordID] = aRec.split(',')
			newRecordID = int(newRecordID)
			try:
				aShortTag = Questionnaire.objects.get(id=newRecordID).shortTag
				try:
					Questionnaire.objects.get(id=int(newRecordID)).delete()
					print "Deleting Questionnaire record %s with tag %s." %(newRecordID,aShortTag)
				except Questionnaire.DoesNotExist:
					print "Questionnaire record %s with tag %s not found" %(newRecordID,aShortTag)
			except Questionnaire.DoesNotExist:
				aShortTag = ''
		fQRecDecode.close()
	except IOError:
		pass
	
	# Delete Page records
	ii = 0
	try:
		fQRecDecode = open('db dump/PageRecDecode.txt','r')
		for aRec in fQRecDecode:
			[oldRecordID,newRecordID] = aRec.split(',')
			newRecordID = int(newRecordID)
			try:
				Page.objects.get(id=int(newRecordID)).delete()
				ii+=1
			except Page.DoesNotExist:
				print "Page record %s not found" %(newRecordID)
		fQRecDecode.close()
	except IOError:
		pass
	print 'Deleted %s Page records' %ii

	# Delete Question records
	print 'deleting Question records'
	try:
		fQRecDecode = open('db dump/QuestionRecDecode.txt','r')
		for aRec in fQRecDecode:
			[oldRecordID,newRecordID] = aRec.split(',')
			newRecordID = int(newRecordID)
			try:
				theQuestionTag = Question.objects.get(id=newRecordID).questionTag
				try:
					Question.objects.get(id=int(newRecordID)).delete()
					print "Deleting Question record %s with tag %s." %(newRecordID,theQuestionTag)
				except Question.DoesNotExist:
					print "Question record %s with tag %s not found" %(newRecordID,theQuestionTag)
			except Question.DoesNotExist:
				theQuestionTag = ''
		fQRecDecode.close()
	except IOError:
		pass
	
	# The ResponseChoice records are deleted along with the Question table records.
	
	return

def dumpAllProjects():
	"""Dump all Projects to a file
	"""
	print 'dumpAllProjects:  enter'
	allProjects = getAllProjects()
	if not allProjects:
		print 'No Projects in the database!!'
		return
	fieldList = ['shortTag','id','abbrev','name','email','contactPhone','internetLocation']
	frec = codecs.open('db dump/Project.txt','w', encoding='utf-8')
	frec.write("%s\n"%(fieldList))
	allOutMessages = []
	ii = 0
	for aProject in allProjects:
		print 'Project: %s' %aProject.shortTag
		dumpProject(aProject, frec)
		ii+=1
	print 'dumpAllProjects:  exit'
	return 'Projects dumped:  %s' %ii
	
def dumpSelectedProject(aProjectTag):
	"""Dump a selected Project to a file
	"""
	print 'dumpSelectedProject:  enter'
	aProject = getProjectObj( aProjectTag)
	if aProject.shortTag == '':
		print 'No such Project:  %s' %aProjectTag
		return
	else:
		print 'Project: %s' %aProject.shortTag
	fieldList = ['shortTag','id','abbrev','name','email','contactPhone','internetLocation']
	frec = codecs.open('db dump/Project.txt','w', encoding='utf-8')
	frec.write("%s\n"%(fieldList))
	dumpProject(aProject, frec)
	frec.close()
	print 'dumpSelectedProject:  exit'
	return

def dumpProject(aProject, frec):
	"""Dump Projects to a file
	"""
	fieldsToDumpRaw = [
		aProject.shortTag, # 0
		aProject.id,	#1
		aProject.abbrev, #2
		aProject.name, #3
		aProject.email, #4
		aProject.contactPhone, #5
		aProject.internetLocation, #6
		]
	fieldsToDump = [repTChar(aField) for aField in fieldsToDumpRaw]
	theLineToWrite = ",".join(fieldsToDump)
	frec.write("%s\n" %theLineToWrite)
	return

def loadProject():
	"""Load Projects to the database
	"""
	print 'loadProject:  enter'
	#fieldList = ['shortTag','id','abbrev','name','email','contactPhone','internetLocation']
	ferrLog = open('db dump/ErrorLog.txt','a')
	frec = open('db dump/Project.txt','r')
	projectRecDecode = codecs.open('db dump/ProjectRecDecode.txt','w', encoding='utf-8') # record old and new records
	ii = 0
	theH = frec.readline() # skip header
	for aRec in frec:
		aRec = aRec[:-1] # remove new line character at end of line
		recFieldsRaw = aRec.split(',')
		recFields = [repPChar(aField) for aField in recFieldsRaw]
		shortTag = recFields[0]
		oldProjectRec = int(recFields[1])
		# check for conflict
		icount = Project.objects.filter(shortTag=shortTag).count()
		if icount !=0:
			# another project of the same name. Rename.
			shortTagNew = shortTag + '_22'
			errMsg = 'loadProject:  shortTag conflict for "%s" renamed to "%s"' %(shortTag,shortTagNew)
			ferrLog.write(errMsg+os.linesep)
			print errMsg
			shortTag = shortTagNew
		print "Project: %s" %shortTag
		spObj=Project.objects.create(
			shortTag = shortTag,
			abbrev = recFields[2],
			name = recFields[3],
			email = recFields[4],
			contactPhone = recFields[5],
			internetLocation = recFields[6]
			)
		newProjectRec = spObj.id
		projectRecDecode.write('%s,%s\n' %(oldProjectRec,newProjectRec))
		ii+=1
	frec.close()
	projectRecDecode.close()
	ferrLog.close()
	print 'loadProject:  exit'
	return 'Projects loaded:  %s' %ii
	
def dumpUserProject():
	"""Dumps the UserProject table from the database to a file UserProject.txt.
	"""
	print 'dumpUserProject:  enter'
	ferrLog = open('db dump/ErrorLog.txt','a')
	# Note which Projects have been dumped. Might be a subset.
	projectFile = open('db dump/Project.txt','r')
	theH = projectFile.readline() # skip header
	projectIDList = [] # ids are text
	for aRec in projectFile:
		recFieldsRaw = aRec.split(',')
		recFields = [repPChar(aField) for aField in recFieldsRaw]
		# add the string version of the id
		projectIDList.append(recFields[1])
	projectFile.close()
	# dump UserProject into a file
	userLoginDump = codecs.open('db dump/UserProject.txt','w', encoding='utf-8')
	# for UserProject table
	fieldList = ['ErrorLogID', 'userID','projectID', 'username', 'projectTag', ]
	userLoginDump.write("%s\n"%(fieldList))
	ii = 0
	# gather all records for UserProject.
	# Copy to file UserProject.txt if ProjectID is null or exists in Project.txt
	allULObjs = UserProject.objects.all()
	for aULObj in allULObjs: # looping on UserProject records
		projectIDstr = str(aULObj.projectID.id)
		if projectIDstr in projectIDList: # User points to a Project dumped to file
			username = aULObj.userID.username
			projectTag = aULObj.projectID.shortTag
			fieldsToDumpRaw = [ # Compose the UserProject text record
				aULObj.id, # 0
				aULObj.userID.id, # 1
				aULObj.projectID.id, # 2
				username, #3
				projectTag, #4
				]
			# convert all to a string # remove line feeds
			fieldsToDump = [repTChar(str(aField)) for aField in fieldsToDumpRaw]
			theLineToWrite = ",".join(fieldsToDump)
			userLoginDump.write("%s\n" %theLineToWrite)
			ii+=1
		else:
			print 'Record "%s" for Project not found in Project.txt' %(projectIDstr)
		# else skip to next UserProject record	
	outMess = 'Number of UserProject records written: %s' %ii
	userLoginDump.close()
	ferrLog.close()
	print 'dumpUserProject:  exit'
	return outMess

def loadUserProject():
	"""Loads the UserProject table to the database from a file UserProject.txt.
	"""
	print 'UserProject:  enter'
	ferrLog = open('db dump/ErrorLog.txt','a')
	fileUserProject = open('db dump/UserProject.txt','r')
	# fieldList = quaires[0]._meta.get_all_field_names()
	# for UserProject table
# 	fieldList = ['ErrorLogID', 'userID','projectID', 'username', 'projectTag', ]
	theH = fileUserProject.readline() # skip header
	# read the record old/new decoding for the Project table <===========
	projectOldNewRec={}
	fProjectRecDecode = open('db dump/ProjectRecDecode.txt','r')
	for aRec in fProjectRecDecode:
		[oldRecordID,newRecordID] = aRec.split(',')
		projectOldNewRec.update({oldRecordID:int(newRecordID)})
	fProjectRecDecode.close()
	ii = 0
	fileUserProjectRecDecode = open('db dump/UserProjectRecDecode.txt','w')
	for anULRec in fileUserProject:
		anULRec = anULRec[:-1] # Remove line separator from the last field
		recFieldsSplit = anULRec.split(',')
		recFields = [repPChar(aField) for aField in recFieldsSplit]
		oldUserProjectIDstr = recFields[0] # string version of the record number
		userID = int(recFields[1])
		username = recFields[3]
		projectTag = recFields[4]
		try:
			userObj = User.objects.get(id=userID)
			if username != userObj.username:
				outMess = 'loadUserProject: Normal difference:  username in file "%s" does not match username in User table "%s" in this database' %(username,userObj.username)
				print outMess
				continue # continue to next UserProject record
		except:
			outMess= 'loadUserProject: Normal difference:  User %s does not exist for Project %s' %(username,projectTag)
			ferrLog.write(outMess+os.linesep)
			print outMess
			continue # continue to next UserProject record
		oldProjectIDstr = recFields[2]
		newProjectID = projectOldNewRec[oldProjectIDstr]
		# Project must already exist. Get the Project object
		try:
			projectObj = Project.objects.get(id=newProjectID)
		except Project.DoesNotExist:
			outMess= 'loadUserProject: Grievous error:  Project Tag %s referenced by user "%s" does not exist in Project table' %(projectTag,username)
			ferrLog.write(outMess+os.linesep)
			print outMess
			continue # continue to next UserProject record
		projectTag = projectObj.shortTag # use the project tag in the table
		if projectTag != recFields[4]:
			outMess = 'loadUserProject: Grievous error:  Project in file "%s" does not match Project in table "%s"' %(recFields[4],projectTag)
			print outMess
			continue # continue to next UserProject record
		print('UserProject record created username: %s for Project tag: %s' %(username,projectTag))
		userLoginObj=UserProject.objects.create(
			userID=userObj,
			projectID=projectObj,
			)
		newRecordID=userLoginObj.id
		oldRecordID=oldUserProjectIDstr
		fileUserProjectRecDecode.write('%s,%s\n'%(oldRecordID,newRecordID))
		ii = ii + 1
	fileUserProjectRecDecode.close()
	fileUserProject.close()
	outMess = 'Number of UserProject records added to database: %s' %ii
	print 'loadUserProject:  exit'
	return outMess

def dumpAllQuestionnairesForProject(aProjectTag):
	"""Dump all Questionnaires belonging to a Project to a file
	"""
	print 'dumpAllQuestionnairesForProject:  enter'
	aProject = getProjectObj( aProjectTag)
	if aProject.shortTag == '':
		print 'No such Project:  %s' %aProjectTag
		return
	fieldList = ['shortTag','id','barTitle','pageTitle','pageSubTitle',
		'description','footerText','version','versionDate',
		'language',
		'firstPageTag','imageFilePath','imageFileName','imageFileType', 
		'ProjectID', 'ProjectTag']
	fileQuest = codecs.open('db dump/Questionnaire.txt','w', encoding='utf-8')
	fileQuest.write("%s\n"%(fieldList))
	quaires = getQuestionnaireObjsForProject(aProject)
	ii = 0
	for aQuaire in quaires:
		print 'Dumping Questionnaire "%s"' %aQuaire.shortTag
		dumpQuestionnaire(aQuaire, fileQuest)
		ii+=1
	fileQuest.close()
	print 'dumpAllQuestionnairesForProject:  exit'
	return 'Questionnaires dumped:  %s' %ii

def dumpSelectedQuestionnaire(aProjectTag, aQuestionnaireTag):
	"""Dump a Questionnaires specified by Project and Questionnaire tag
	"""
	print 'dumpSelectedQuestionnaire:  enter'
	fieldList = ['shortTag','id','barTitle','pageTitle','pageSubTitle',
		'description','footerText','version','versionDate',
		'language',
		'firstPageTag','imageFilePath','imageFileName','imageFileType', 
		'ProjectID', 'ProjectTag']
	fileQuest = codecs.open('db dump/Questionnaire.txt','w', encoding='utf-8')
	fileQuest.write("%s\n"%(fieldList))
	aQuaire = getQuestionnaireObjFromTags(aProjectTag, aQuestionnaireTag)
	print 'Dumping Questionnaire "%s"' %aQuaire.shortTag
	dumpQuestionnaire(aQuaire, fileQuest)
	fileQuest.close()
	print 'dumpSelectedQuestionnaire:  exit'
	return

def dumpAllQuestionnaires():
	"""Dump all Questionnaires.
	"""
	print 'dumpAllQuestionnaires:  enter'
	# fieldList = quaires[0]._meta.get_all_field_names()
	fieldList = ['shortTag','id','barTitle','pageTitle','pageSubTitle',
		'description','footerText','version','versionDate',
		'language',
		'firstPageTag','imageFilePath','imageFileName','imageFileType', 
		'ProjectID', 'ProjectTag']
	fileQuest = codecs.open('db dump/Questionnaire.txt','w', encoding='utf-8')
	fileQuest.write("%s\n"%(fieldList))
	quaires = getAllQuestionnaires( )
	ii = 0
	for aQuaire in quaires:
		print 'Dumping Questionnaire "%s"' %aQuaire.shortTag
		dumpQuestionnaire(aQuaire, fileQuest)
		ii+=1
	fileQuest.close()
	print 'dumpAllQuestionnaires:  exit'
	return 'Questionnaires dumped:  %s' %ii

def dumpQuestionnaire(quaire, fQuaire):
	"""Dumps a Questionnaire to a file
	"""
# 	fieldList = ['shortTag','id','barTitle','pageTitle','pageSubTitle',
# 		'description','footerText','version','versionDate',
# 		'language',
# 		'firstPageTag','imageFilePath','imageFileName','imageFileType', 
# 		'ProjectID', 'ProjectTag']
	ii = 0
	spObj = getProjectObjForQuestionnaire(quaire)
	if spObj:
		projectShortTag = spObj.shortTag
		spID = spObj.id
	else:
		projectShortTag = ""
		spID = 0 # no Project
	fieldsToDumpRaw = [
		quaire.shortTag, #0 Questionnaire shortTag
		quaire.id, #1 Questionnaire id
		quaire.barTitle, #2
		quaire.pageTitle, #3
		quaire.pageSubTitle, #4
		quaire.description, #5
		quaire.footerText, #6
		quaire.version, #7
		quaire.versionDate, #8
		quaire.language, #9
		quaire.imageFilePath, #10
		quaire.imageFileName, #11
		quaire.imageFileType, #12
		projectShortTag, #13 # *** get rid of this
		spID, #14 # *** get rid of this
		]
	# make nice
	fieldsToDump = [repTChar(aField) for aField in fieldsToDumpRaw]
	theLineToWrite = ",".join(fieldsToDump)
	fQuaire.write("%s\n" %theLineToWrite)
	return

def loadQuestionnaire():
	"""Loads Questionnaire to the database
	"""
	# Load Project table before this
	# create Project record translation from file created by Project
	print 'loadQuestionnaire:  enter'
	ferrLog = open('db dump/ErrorLog.txt','a')
	frec = open('db dump/Questionnaire.txt','r')
# 	fieldList = ['shortTag','id','barTitle','pageTitle','pageSubTitle',
# 		'description','footerText','version','versionDate',
# 		'language',
# 		'firstPageTag','imageFilePath','imageFileName','imageFileType', 'ProjectTag']
	fQuestionnaireRecDecode = open('db dump/QuestionnaireRecDecode.txt','w')
	ii = 0
	theH = frec.readline() # skip header
	for aRec in frec:
		aRec = aRec[:-1] # Remove line separator from the last field
		recFieldsSplt = aRec.split(',')
		recFields = [repPChar(aF) for aF in recFieldsSplt]
		spTag = recFields[13] # Project Tag
		# find the project id
		if spTag:
			spObj = getProjectObj( spTag)
		else: # a Questionnaire may not have a project
			spObj = None
		shortTag = recFields[0] # Questionnaire Tag
		print 'Questionnaire tag: %s' %shortTag
		QuestionnaireObj=Questionnaire.objects.create(
			shortTag=shortTag,
			barTitle=recFields[2],
			pageTitle=recFields[3],
			pageSubTitle=recFields[4],
			description=recFields[5],
			footerText=recFields[6],
			version=recFields[7],
			versionDate=recFields[8][:19], # *** kludge for timezone
			language=recFields[9],
			imageFilePath=recFields[10],
			imageFileName=recFields[11],
			imageFileType=recFields[12],
			)
		oldQuestionnaireID = recFields[1]
		fQuestionnaireRecDecode.write('%s,%s\n' %(oldQuestionnaireID,QuestionnaireObj.id))
		ii+=1
	
	ferrLog.close()
	frec.close()
	fQuestionnaireRecDecode.close()
	outMess = 'Number of questionnaires: %s' %ii
	print 'loadQuestionnaire:  exit'
	return outMess

def dumpProjectQuestionnaire():
	"""Dump the ProjectQuestionnaire table to a file.
	Dump only the ProjectQuestionnaire records relating to Projects and Questionnaires
	dumped.
	"""
	print 'dumpProjectQuestionnaire:  enter'
	# create ProjectQuestionnaire Table,
	# which contains the link between Project and Questionnaire
	# Require that Project and Questionnaire have already been dumped
	projectFile = open('db dump/Project.txt','r') # record old and new records
	theH = projectFile.readline() # skip header
	projectInfoList = []
	for aRec in projectFile:
		recFieldsRaw = aRec.split(',')
		recFields = [repPChar(aField) for aField in recFieldsRaw]
		# add id and shortTag to list
		projectInfoList.append([int(recFields[1]),recFields[0]])
	projectFile.close()
	questionnaireFile = open('db dump/Questionnaire.txt','r')
	theH = questionnaireFile.readline() # skip header
	questionnaireInfoList = []
	for aRec in questionnaireFile:
		recFieldsRaw = aRec.split(',')
		recFields = [repPChar(aField) for aField in recFieldsRaw]
		# add id and shortTag to list
		questionnaireInfoList.append([int(recFields[1]),recFields[0]])
	questionnaireFile.close()
	# dump the Project - Questionnaire connection
	sqConnect = codecs.open('db dump/ProjectQuestionnaire.txt','w', encoding='utf-8')
	fieldList = ['Project ID', 'Project Tag','Questionnaire ID','Questionnaire Tag',
	'Record Type', 'Questionnaire Status']
	sqConnect.write("%s\n"%(fieldList))
	ii = 0
	for [sponID,sponShortTag] in projectInfoList:
		try:
			spObj = Project.objects.get(id=sponID)
		except Project.DoesNotExist:
			print 'Project record %s does not exist' %sponShortTag
			continue
		for [qID,questShortTag] in questionnaireInfoList:
			try:
				quaire = Questionnaire.objects.get(id=qID)
			except Questionnaire.DoesNotExist:
				print 'Questionnaire record %s does not exist' %questShortTag
				continue
			# Copy if connection is in ProjectQuestionnaire
			questionnaireStatus = getQuestionnaireStatusValue(spObj, quaire)
			try: # unique single record required
				sqObj = ProjectQuestionnaire.objects.get(
					projectID=spObj,
					questionnaireID=quaire,
					)
				fieldsToDumpRaw = [
					spObj.id, # 0
					spObj.shortTag, # 1
					quaire.id, #2
					quaire.shortTag, #3
					sqObj.recordType, #4
					sqObj.questionnaireStatus, #5
					]
				fieldsToDump = [repTChar(aField) for aField in fieldsToDumpRaw]
				theLineToWrite = ",".join(fieldsToDump)
				sqConnect.write("%s\n" %theLineToWrite)
				ii+=1
				print 'Questionnaire "%s" with Project "%s" record written to file.' %(quaire.shortTag,spObj.shortTag)
			except ProjectQuestionnaire.DoesNotExist:
				print 'Questionnaire "%s" with Project "%s" are not connected.' %(quaire.shortTag,spObj.shortTag)
	outMess = 'Number of ProjectQuestionnaire records: %s' %ii
	print 'dumpProjectQuestionnaire:  exit'
	return outMess

def loadProjectQuestionnaire():
	"""Create the ProjectQuestionnaire table.
	"""
	print 'loadProjectQuestionnaire:  enter'
	# create ProjectQuestionnaire Table,
	# which contains the link between Project and Questionnaire
	# The Project may not exist for a Questionnaire!
	#fieldList = ['Project ID', 'Project Tag','Questionnaire ID','Questionnaire Tag']
	projectRecDecode = open('db dump/ProjectRecDecode.txt','r')
	# read the record old/new decoding for the Project table
	sponOldNewRec={}
	for aRec in projectRecDecode:
		[oldRecordID,newRecordID] = aRec.split(',')
		sponOldNewRec.update({int(oldRecordID):int(newRecordID)})
	projectRecDecode.close()
	# read the record old/new decoding for the Questionnaire table
	questOldNewRec={}
	fQuestionnaireRecDecode = open('db dump/QuestionnaireRecDecode.txt','r')
	for aRec in fQuestionnaireRecDecode:
		[oldRecordID,newRecordID] = aRec.split(',')
		questOldNewRec.update({int(oldRecordID):int(newRecordID)})
	fQuestionnaireRecDecode.close()
	# read the ProjectQuestionnaire file for contents
	#fieldList = ['Project ID', 'Project Tag','Questionnaire ID','Questionnaire Tag']
	# *** add 'questionnaireStatus' for 'ProjectQuestionnaire' for model change
	sqFile = open('db dump/ProjectQuestionnaire.txt','r') # for this object
	theH = sqFile.readline() # skip header
	ii = 0
	for aRec in sqFile:
		aRec = aRec[:-1]
		recFieldsSplt = aRec.split(',')
		recFields = [repPChar(aF) for aF in recFieldsSplt]
		[oldProjectID, oldProjectTag, oldQuestionnaireID, oldQuestionnaireTag, theRecordType, theQuestionnaireStatus]= recFields
		# for to integer
		oldProjectID = int(oldProjectID)
		oldQuestionnaireID = int(oldQuestionnaireID)
		# translate to new ids
		if oldProjectID !=0: # not zero
			if oldProjectID in sponOldNewRec:
				newProjectID = sponOldNewRec[oldProjectID]
				newProjectTag = Project.objects.get(id=newProjectID).shortTag
			else:
				print 'Grevious error:  record %s not found with tag %s.' %(oldProjectID,oldProjectTag)
				continue
			newQuestionnaireID = questOldNewRec[int(oldQuestionnaireID)]
			newQuestionnaireTag = Questionnaire.objects.get(id=newQuestionnaireID).shortTag
			ProjectQuestionnaire.objects.create(
				projectID=Project.objects.get(id=newProjectID),
				questionnaireID=Questionnaire.objects.get(id=newQuestionnaireID),
				recordType=theRecordType,
				questionnaireStatus = theQuestionnaireStatus,
				)
			ii+=1
			print 'Project Tag: %s, Questionnaire Tag: %s' %(newProjectTag,newQuestionnaireTag)
		else:
			print 'No Project for questionnaire: %s' %newQuestionnaireTag
	sqFile.close()
	outMess = 'Number of ProjectQuestionnaire records: %s' %ii
	print 'loadProjectQuestionnaire:  exit'
	return outMess
	
def dumpPage():
	"""Dumps Pages to a file
	Dump only the Page records relating to Questionnaires dumped.
	"""
	print 'dumpPage:  enter'
	questionnaireFile = open('db dump/Questionnaire.txt','r')
	theH = questionnaireFile.readline() # skip header
	questionnaireInfoList = []
	for aRec in questionnaireFile:
		recFieldsRaw = aRec.split(',')
		recFields = [repPChar(aField) for aField in recFieldsRaw]
		# add id and shortTag to list
		questionnaireInfoList.append([int(recFields[1]),recFields[0]])
	questionnaireFile.close()
	fpage = codecs.open('db dump/Page.txt','w', encoding='utf-8')
	# fieldList = quaires[0]._meta.get_all_field_names()
	fieldList = ['shortTag','id','pageType','description','explanation',
		'prologue','epilogue','helpPage','helpButtonTitle',
		'language','imageFilePath','imageFileName','imageFileType']
	fpage.write('%s\n'%fieldList)
	ii = 0
	pagesidsSeen = []
	for [qID,questShortTag] in questionnaireInfoList:
		try:
			quaire = Questionnaire.objects.get(id=qID)
		except Questionnaire.DoesNotExist:
			outMess= 'Grievous error:  Questionnaire record/Tag %s/%s does not exist in file Questionnaire.txt' %(qID,questShortTag)
			ferrLog.write(outMess+os.linesep)
			print outMess
			continue
		# Get questions belonging to the questionnaire
		somePages = getAllPageObjsForQuestionnaire(quaire)	
		jjpages = 0
		for aPage in somePages:
			if aPage.id not in pagesidsSeen: # check for pages already dumped to file.
				fieldsToDumpRaw = [
					aPage.shortTag, #0
					aPage.id, #1
					aPage.pageType, #2
					aPage.description, #3
					aPage.explanation, #4
					aPage.prologue, #5
					aPage.epilogue, #6
					aPage.helpPage, #7
					aPage.helpButtonTitle, #8
					aPage.language, #9
					aPage.imageFilePath, #10
					aPage.imageFileName, #11
					aPage.imageFileType, #12
					]
				# make nice
				fieldsToDump = [repTChar(aField) for aField in fieldsToDumpRaw]
				theLineToWrite = ",".join(fieldsToDump)
				fpage.write("%s\n" %theLineToWrite)
				pagesidsSeen.append(aPage.id) # don't repeat the page in the file
			ii+=1
			jjpages+=1
		print 'Found Page count %s for questionnaire %s' %(jjpages,quaire.shortTag)
	fpage.close()
	outMess = 'Number of Pages: %s' %ii
	print 'dumpPage:  exit'
	return outMess

def loadPage():
	# Loads Pages to the database
	print 'loadPage:  enter'
	ferrLog = open('db dump/ErrorLog.txt','a')
	fpage = open('db dump/Page.txt','r')
	# fieldList = quaires[0]._meta.get_all_field_names()
# 	fieldList = ['shortTag','id','pageType','description','explanation',
# 		'prologue','epilogue','helpPage','helpButtonTitle',
# 		'language','imageFilePath','imageFileName','imageFileType']
	theH = fpage.readline() # skip header
	ii = 0
	fpageRecDecode = open('db dump/PageRecDecode.txt','w')
	for aPage in fpage:
		aPage = aPage[:-1] # Remove line separator from the last field
		recFieldsSplt = aPage.split(',')
		recFields = [repPChar(aF) for aF in recFieldsSplt]
		shortTag=recFields[0]
		print('Page tag: %s' %(shortTag))
		pageObj=Page.objects.create(
			shortTag=shortTag,
			pageType=recFields[2],
			description=repPChar(recFields[3]),
			explanation=repPChar(recFields[4]),
			prologue=repPChar(recFields[5]),
			epilogue=repPChar(recFields[6]),
			helpPage=recFields[7],
			helpButtonTitle=recFields[8],
			language=recFields[9],
			imageFilePath=recFields[10],
			imageFileName=recFields[11],
			imageFileType=recFields[12],
			)
		newRecordID=pageObj.id
		oldRecordID=recFields[1]
		fpageRecDecode.write('%s,%s\n'%(oldRecordID,newRecordID))
		ii = ii + 1
	fpageRecDecode.close()
	fpage.close()
	outMess = 'Number of pages: %s' %ii
	print 'loadPage:  exit'
	return outMess

def dumpQuestionnairePage():
	"""Dump the QuestionnairePage table to a file.
	Dump only the QuestionnairePage records relating to Pages and Questionnaires
	already dumped to file.
	"""
	print 'dumpQuestionnairePage:  enter'
	ferrLog = open('db dump/ErrorLog.txt','a')
	# create QuestionnairePage Table,
	# which contains the link between Questionnaire and Page
	questionnaireFile = open('db dump/Questionnaire.txt','r')
	theH = questionnaireFile.readline() # skip header
	questionnaireInfoList = []
	for aRec in questionnaireFile:
		recFieldsRaw = aRec.split(',')
		recFields = [repPChar(aField) for aField in recFieldsRaw]
		# add id and shortTag to list
		questionnaireInfoList.append([int(recFields[1]),recFields[0]])
	questionnaireFile.close()
	pageFile = open('db dump/Page.txt','r')
	theH = pageFile.readline() # skip header
	pageids = []
	for aRec in pageFile:
		recFieldsRaw = aRec.split(',')
		recFields = [repPChar(aField) for aField in recFieldsRaw]
		# add id and shortTag to list
		pageids.append(int(recFields[1])) # only the record number
	pageFile.close()
	# dump the Questionnaire - Page connection
	qpConnect = codecs.open('db dump/QuestionnairePage.txt','w', encoding='utf-8')
	fieldList = ['Questionnaire ID', 'Questionnaire Tag','Page ID','Page Tag',
		'Next Page ID', 'Next Page shortTag', 'Test Condition', 'Record Type', ]
	qpConnect.write("%s\n"%(fieldList))
	ii = 0
	for [qID,questShortTag] in questionnaireInfoList:
		try:
			quaire = Questionnaire.objects.get(id=qID)
		except Questionnaire.DoesNotExist:
			outMess= 'Grievous error:  Questionnaire record/Tag %s/%s does not exist in file Questionnaire.txt' %(qID,questShortTag)
			ferrLog.write(outMess+os.linesep)
			print outMess
			continue
		# Copy if connection is in QuestionnairePage
		# gather all records for Questionnaire
		qpObjs = QuestionnairePage.objects.filter(
			questionnaireID=quaire,
			)
		if qpObjs.count() == 0: # questionnaire has no pages. OK
			continue
		jjqp = 0
		for qpObj in qpObjs: # examine each QuestionnairePage record
			currentPageObj = qpObj.pageID
			currentPageid = qpObj.pageID.id
			if currentPageid not in pageids:
				outMess = 'Grievous error: Current page record "%s" not found in list in Page.txt' %currentPageObj.shortTag
				ferrLog.write(outMess+os.linesep)
				print outMess
				outMess = 'Questionnaire record/tag is %s/%s' %(quaire.id,quaire.shortTag)
				ferrLog.write(outMess+os.linesep)
				print outMess
				# continue to next page
				continue
			nextPageObj = qpObj.nextPageID # take "next page" info from QuestionnairePage table
			nextPageid = nextPageObj.id
			if nextPageid not in pageids:
				outMess = 'Grievous error: Next page record "%s" not found in list in Page.txt' %nextPageObj.shortTag
				ferrLog.write(outMess+os.linesep)
				print outMess
				outMess = 'Questionnaire record/tag is %s/%s' %(quaire.id,quaire.shortTag)
				ferrLog.write(outMess+os.linesep)
				print outMess
				# continue to next page
				continue
			fieldsToDumpRaw = [
				quaire.id, # 0
				quaire.shortTag, # 1
				currentPageObj.id, #2
				currentPageObj.shortTag, #3
				nextPageObj.id, #4
				nextPageObj.shortTag, #5
				qpObj.testCondition, #6
				qpObj.recordType, #7
				]
			fieldsToDump = [repTChar(aField) for aField in fieldsToDumpRaw]
			theLineToWrite = ",".join(fieldsToDump)
			qpConnect.write("%s\n" %theLineToWrite)
			ii+=1
			jjqp+=1 # count qp records per questionnaire
		print 'Found count of %s QuestionnairePage records for Questionnaire %s' %(jjqp,quaire.shortTag)
	outMess = 'Number of QuestionnairePage records: %s' %ii
	qpConnect.close()
	ferrLog.close()
	print 'dumpQuestionnairePage:  exit'
	return outMess

def loadQuestionnairePage():
	# Loads QuestionnairePage
	# Needs Questionnaire and Page
	# replace all contents with loaded value
	print 'loadQuestionnairePage:  enter'
# 	fieldList = ['Questionnaire ID', 'Questionnaire Tag','Page ID','Page Tag',
# 		'Next Page ID', 'Next Page shortTag', 'Test Condition', 'Record Type', ]
	PageRecDecode = open('db dump/PageRecDecode.txt','r')
	# read the record old/new decoding for the Page table <===========
	pageOldNewRec={}
	for aRec in PageRecDecode:
		[oldRecordID,newRecordID] = aRec.split(',')
		pageOldNewRec.update({oldRecordID:int(newRecordID)})
	PageRecDecode.close()
	# read the record old/new decoding for the Questionnaire table <===========
	questOldNewRec={}
	fQuestionnaireRecDecode = open('db dump/QuestionnaireRecDecode.txt','r')
	for aRec in fQuestionnaireRecDecode:
		[oldRecordID,newRecordID] = aRec.split(',')
		questOldNewRec.update({oldRecordID:int(newRecordID)})
	fQuestionnaireRecDecode.close()
	sqFile = open('db dump/QuestionnairePage.txt', 'r')
	theH = sqFile.readline() # skip header
	# Load QuestionnairePage table <===========
	ii = 0
	for aRec in sqFile:
		aRec = aRec[:-1]
		recFieldsSplit = aRec.split(',')
		recFields = [repPChar(aF) for aF in recFieldsSplit]
		qaireID = int(questOldNewRec[recFields[0]]) # Questionnaire id
		pgCurrID = int(pageOldNewRec[recFields[2]]) # current page id
		pgNextID = int(pageOldNewRec[recFields[4]]) # next page id, convert to new record
		qaireShortTag = recFields[1]
		testConditionIn = recFields[6]
		recordType = recFields[7]
		q1=Questionnaire.objects.get(id=qaireID)
		pg=Page.objects.get(id=pgCurrID)
		pg2=Page.objects.get(id=pgNextID)
		pq=QuestionnairePage.objects.create(
			questionnaireID=q1,
			pageID = pg, # an object
			nextPageID = pg2, # an object
			testCondition = testConditionIn, # text
			recordType = recordType
			)
		ii = ii + 1
	sqFile.close()
	outMess = 'Number of records: %s' %ii
	print 'loadQuestionnairePage:  exit'
	return outMess

def dumpQuestion():
	"""Dumps Questions to a file
	Dump only the Question records relating to Questionnaires dumped.
	"""
	print 'dumpQuestion:  enter'
	questionnaireFile = open('db dump/Questionnaire.txt','r')
	theH = questionnaireFile.readline() # skip header
	questionnaireInfoList = []
	for aRec in questionnaireFile:
		recFieldsRaw = aRec.split(',')
		recFields = [repPChar(aField) for aField in recFieldsRaw]
		# add id and shortTag to list
		questionnaireInfoList.append([int(recFields[1]),recFields[0]])
	questionnaireFile.close()
	fquestion = codecs.open('db dump/Question.txt','w', encoding='utf-8')
	# fieldList = quaires[0]._meta.get_all_field_names()
# 	# for Question object
	fieldList = ['questionTag','id','questionText','helpText','explanation',
		'language','description','responseType','imageFilePath','imageFileName',
		'imageFileType']
	fquestion.write('%s\n'%fieldList)
	ii = 0
	questionRecordsAlreadyDumped = []
	for [qID,questShortTag] in questionnaireInfoList:
		try:
			quaire = Questionnaire.objects.get(id=qID)
		except Questionnaire.DoesNotExist:
			outMess= 'Grievous error:  Questionnaire record/Tag %s/%s from file Questionnaire.txt does not exist in database' %(qID,questShortTag)
			ferrLog.write(outMess+os.linesep)
			print outMess
			continue
		# Get questions belonging to the questionnaire
		someQuestions = getAllQuestionObjsForQuestionnaire(quaire)	
		jjQuestions = 0
		for aQuestion in someQuestions:
			thisQuestionRecid = aQuestion.id
			if thisQuestionRecid in questionRecordsAlreadyDumped:
				jjQuestions+=1
				continue # go to next question
			questionRecordsAlreadyDumped.append(thisQuestionRecid)
			fieldsToDumpRaw = [
				aQuestion.questionTag, #0
				thisQuestionRecid, #1
				aQuestion.questionText, #2
				aQuestion.helpText, #3
				aQuestion.explanation, #4
				aQuestion.language, #5
				aQuestion.description, #6
				aQuestion.responseType, #7
				aQuestion.imageFilePath, #10
				aQuestion.imageFileName, #11
				aQuestion.imageFileType, #12
				]
			# make nice
			fieldsToDump = [repTChar(aField) for aField in fieldsToDumpRaw]
			theLineToWrite = ",".join(fieldsToDump)
			fquestion.write("%s\n" %theLineToWrite)
			ii+=1
			jjQuestions+=1
		print 'Found Question count %s for questionnaire %s' %(jjQuestions,quaire.shortTag)
	fquestion.close()
	outMess = 'Total number of distinct Questions: %s' %ii
	print 'dumpQuestion:  exit'
	return outMess

def loadQuestion():
	# Loads Questions to the database
	print 'loadQuestion:  enter'
	ferrLog = open('db dump/ErrorLog.txt','a')
	fquestion = open('db dump/Question.txt','r')
	# fieldList = quaires[0]._meta.get_all_field_names()
# 	# for Question object
# 	fieldList = ['questionTag','id','questionText','helpText','explanation',
# 		'language','description','responseType','imageFilePath','imageFileName',
# 		'imageFileType']
	theH = fquestion.readline() # skip header
	ii = 0
	fquestionRecDecode = open('db dump/QuestionRecDecode.txt','w')
	for aQuestion in fquestion:
		aQuestion = aQuestion[:-1] # Remove line separator from the last field
		recFieldsSplt = aQuestion.split(',')
		recFields = [repPChar(aF) for aF in recFieldsSplt]
		questionTag=recFields[0]
		print('Question tag: %s' %(questionTag))
		questionObj=Question.objects.create(
			questionTag=questionTag,
			questionText=recFields[2],
			helpText=recFields[3],
			explanation=recFields[4],
			language=recFields[5],
			description=recFields[6],
			responseType=recFields[7],
			imageFilePath=recFields[8],
			imageFileName=recFields[9],
			imageFileType=recFields[10],
			)
		newRecordID=questionObj.id
		oldRecordID=recFields[1]
		fquestionRecDecode.write('%s,%s\n'%(oldRecordID,newRecordID))
		ii = ii + 1
	fquestionRecDecode.close()
	fquestion.close()
	outMess = 'Number of pages: %s' %ii
	print 'loadQuestion:  exit'
	return outMess	

def dumpPageQuestion():
	"""Dump the PageQuestion table to a file.
	Dump only the PageQuestion records relating to Pages and Questions
	already dumped to file.
	"""
	print 'dumpPageQuestion:  enter'
	ferrLog = open('db dump/ErrorLog.txt','a')
	# create PageQuestion Table,
	# which contains the link between Question and Page
	pageFile = open('db dump/Page.txt','r')
	theH = pageFile.readline() # skip header
	pageInfoFile = []
	for aRec in pageFile:
		recFieldsRaw = aRec.split(',')
		recFields = [repPChar(aField) for aField in recFieldsRaw]
		# add id and shortTag to list
		pageInfoFile.append([int(recFields[1]),recFields[0]])
	pageFile.close()
	questionFile = open('db dump/Question.txt','r')
	theH = questionFile.readline() # skip header
	questionids = [] # integer ids only
	for aRec in questionFile:
		recFieldsRaw = aRec.split(',')
		recFields = [repPChar(aField) for aField in recFieldsRaw]
		# add only the id
		questionids.append(int(recFields[1])) # only the record number
	questionFile.close()
	# dump the Question - Page connection
	qpConnect = codecs.open('db dump/PageQuestion.txt','w', encoding='utf-8')
	# for PageQuestion table
	fieldList = ['Question ID', 'Question Tag','Page ID','Page Tag', 
		'Question Sequence', 'Question Group', ]
	qpConnect.write("%s\n"%(fieldList))
	ii = 0
	for [pageid,pageShortTag] in pageInfoFile: # looping on pages
		try:
			pageObj = Page.objects.get(id=pageid)
		except Page.DoesNotExist:
			outMess= 'Grievous error:  Page record/Tag %s/%s does not exist in file Page.txt' %(pageid,pageShortTag)
			ferrLog.write(outMess+os.linesep)
			print outMess
			continue
		# Copy if connection is in PageQuestion
		# gather all records for Page
		qpObjs = PageQuestion.objects.filter(
			pageID=pageObj,
			)
		if qpObjs.count() == 0: # page has no questions. OK
			continue
		jjqp = 0 # count the qp records for this page
		for qpObj in qpObjs: # examine each PageQuestion record # looping on Questions
			questionObj = qpObj.questionID
			currentQuestionid = questionObj.id
			if currentQuestionid not in questionids:
				outMess = 'Grievous error: Current Question record "%s" not found in list in Question.txt' %questionObj.questionTag
				ferrLog.write(outMess+os.linesep)
				print outMess
				outMess = 'Question is part of Page record/tag %s/%s' %(pageObj.id,pageObj.shortTag)
				ferrLog.write(outMess+os.linesep)
				print outMess
				# continue to next page
				continue
			fieldsToDumpRaw = [ # Compose the PageQuestion text record
				questionObj.id, # 0
				questionObj.questionTag, # 1
				pageObj.id, #2
				pageObj.shortTag, #3
				qpObj.questionSequence, #4
				qpObj.questionGroup, #5
				]
			fieldsToDump = [repTChar(aField) for aField in fieldsToDumpRaw]
			theLineToWrite = ",".join(fieldsToDump)
			qpConnect.write("%s\n" %theLineToWrite)
			ii+=1
			jjqp+=1 # count qp records per questionnaire
		print 'Found count of %s PageQuestion records for Page %s' %(jjqp,pageObj.shortTag)
	outMess = 'Number of PageQuestion records: %s' %ii
	qpConnect.close()
	ferrLog.close()
	print 'dumpPageQuestion:  exit'
	return outMess

def loadPageQuestion():
	"""Loads the PageQuestion file to the database table.
	"""
	# Loads PageQuestion
	# Needs Question and Page
	# replace all contents with loaded value
	print 'loadPageQuestion:  enter'
	# for PageQuestion table
# 	fieldList = ['Question ID', 'Question Tag','Page ID','Page Tag', 
# 		'Question Sequence', 'Question Group', ]
	PageRecDecode = open('db dump/PageRecDecode.txt','r')
	# read the record old/new decoding for the Page table <===========
	pageOldNewRec={}
	for aRec in PageRecDecode:
		[oldRecordID,newRecordID] = aRec.split(',')
		pageOldNewRec.update({oldRecordID:int(newRecordID)})
	PageRecDecode.close()
	# read the record old/new decoding for the Question table <===========
	questOldNewRec={}
	fQuestionRecDecode = open('db dump/QuestionRecDecode.txt','r')
	for aRec in fQuestionRecDecode:
		[oldRecordID,newRecordID] = aRec.split(',')
		questOldNewRec.update({oldRecordID:int(newRecordID)})
	fQuestionRecDecode.close()
	pqFile = open('db dump/PageQuestion.txt', 'r')
	theH = pqFile.readline() # skip header
	# Load PageQuestion table <===========
	ii = 0
	for aRec in pqFile:
		aRec = aRec[:-1]
		recFieldsSplit = aRec.split(',')
		recFields = [repPChar(aF) for aF in recFieldsSplit]
		questid = int(questOldNewRec[recFields[0]]) # Question id
		pgCurrID = int(pageOldNewRec[recFields[2]]) # current page id
		q1=Question.objects.get(id=questid)
		pg=Page.objects.get(id=pgCurrID)
		pq=PageQuestion.objects.create(
			questionID=q1,
			pageID = pg, # an object
			questionSequence = recFields[4], # text
			questionGroup = recFields[5]
			)
		ii = ii + 1
	pqFile.close()
	outMess = 'Number of records: %s' %ii
	print 'loadPageQuestion:  exit'
	return outMess

def dumpResponseChoice():
	"""Dumps the ResponseChoice table from the database to a file.
	"""
	print 'dumpResponseChoice:  enter'
	ferrLog = open('db dump/ErrorLog.txt','a')
	# create ResponseChoice file
	# which contains the link between ResponseChoice: and Question
	questionFile = open('db dump/Question.txt','r')
	theH = questionFile.readline() # skip header
	qids = [] # integer ids only
	for aRec in questionFile:
		recFieldsRaw = aRec.split(',')
		recFields = [repPChar(aField) for aField in recFieldsRaw]
		# add the id and tag
		qids.append([int(recFields[1]),recFields[0]])
	questionFile.close()
	# dump the Question - ResponseChoice connection into a file
	rcConnect = codecs.open('db dump/ResponseChoice.txt','w', encoding='utf-8')
	# for ResponseChoice table
	fieldList = ['ResponseChoice ID', 'Choice Tag', 'Question ID', 'Question Tag',
		'Choice Text', 'Choice Type', 'Choice Sequence', ]
	rcConnect.write("%s\n"%(fieldList))
	ii = 0
	for [qid,qtag] in qids: # looping on questions
		try:
			questionObj = Question.objects.get(id=qid)
		except Question.DoesNotExist:
			outMess= 'Grievous error:  Question record/Tag %s/%s in file Question.txt does not exist in Question DB' %(qid,qtag)
			ferrLog.write(outMess+os.linesep)
			print outMess
			continue
		# Copy if connection is in ResponseChoice
		# gather all records for Question
		rcObjs = ResponseChoice.objects.filter(
			questionID=questionObj,
			)
		if rcObjs.count() == 0: # Question has no response choice. That's OK
			continue
		jjrc = 0 # count the ResponseChoice records for this Question
		for rcObj in rcObjs: # examine each ResponseChoice record # looping on Questions
			fieldsToDumpRaw = [ # Compose the ResponseChoice text record
				rcObj.id, # 0
				rcObj.choiceTag, # 1
				questionObj.id, # 2
				questionObj.questionTag, # 3
				rcObj.choiceText, #4
				rcObj.choiceType, #5
				rcObj.choiceSequence, #6
				]
			fieldsToDump = [repTChar(aField) for aField in fieldsToDumpRaw]
			theLineToWrite = ",".join(fieldsToDump)
			rcConnect.write("%s\n" %theLineToWrite)
			ii+=1
			jjrc+=1 # count qp records per questionnaire
		print 'Found count of %s ResponseChoice records for Question %s' %(jjrc,questionObj.questionTag)
	outMess = 'Number of ResponseChoice records: %s' %ii
	rcConnect.close()
	ferrLog.close()
	print 'dumpResponseChoice:  exit'
	return outMess	

def loadResponseChoice():
	# Loads ResponseChoice file to the database
	print 'ResponseChoice:  enter'
	ferrLog = open('db dump/ErrorLog.txt','a')
	fileRC = open('db dump/ResponseChoice.txt','r')
	# fieldList = quaires[0]._meta.get_all_field_names()
# 	# for ResponseChoice object
# 	fieldList = ['ResponseChoice ID', 'Choice Tag', 'Question ID', 'Question Tag',
# 		'Choice Text', 'Choice Type', 'Choice Sequence', ]
	theH = fileRC.readline() # skip header
	# read the record old/new decoding for the Question table <===========
	questOldNewRec={}
	fQuestionRecDecode = open('db dump/QuestionRecDecode.txt','r')
	for aRec in fQuestionRecDecode:
		[oldRecordID,newRecordID] = aRec.split(',')
		questOldNewRec.update({oldRecordID:int(newRecordID)})
	fQuestionRecDecode.close()
	ii = 0
	fileRCRecDecode = open('db dump/ResponseChoiceRecDecode.txt','w')
	for anRCRec in fileRC:
		anRCRec = anRCRec[:-1] # Remove line separator from the last field
		recFieldsSplt = anRCRec.split(',')
		recFields = [repPChar(aF) for aF in recFieldsSplt]
		choiceTag=recFields[1]
		questid = recFields[2] # string version of the record number
		questShortTag = recFields[3]
		# Question must already exist
		try:
			questObj = Question.objects.get(id=questOldNewRec[questid])
		except Question.DoesNotExist:
			outMess= 'loadResponseChoice: Grievous error:  Question record/Tag %s/%s does not exist in table Question' %(questid,questShortTag)
			ferrLog.write(outMess+os.linesep)
			print outMess
			continue # continue to next ResponseChoice record
		questionTag = questObj.questionTag
		print('ResponseChoice tag: %s for Question tag: %s' %(choiceTag,questionTag))
		rcObj=ResponseChoice.objects.create(
			questionID=questObj,
			choiceTag=choiceTag,
			choiceText=recFields[4],
			choiceType=recFields[5],
			choiceSequence=recFields[6],
			)
		newRecordID=rcObj.id
		oldRecordID=questid
		fileRCRecDecode.write('%s,%s\n'%(oldRecordID,newRecordID))
		ii = ii + 1
	fileRCRecDecode.close()
	fileRC.close()
	outMess = 'Number of ResponseChoice records added to database: %s' %ii
	print 'loadResponseChoice:  exit'
	return outMess
	
def dumpPageAnalysis():
	"""Dumps the PageAnalysis table from the database to a file.
	Dump only the PageAnalysis records relating to Questionnaires dumped.
	"""
	print 'dumpPageAnalysis:  enter'
	ferrLog = open('db dump/ErrorLog.txt','a')
	questionnaireFile = open('db dump/Questionnaire.txt','r')
	theH = questionnaireFile.readline() # skip header
	questionnaireInfoList = []
	for aRec in questionnaireFile:
		recFieldsRaw = aRec.split(',')
		recFields = [repPChar(aField) for aField in recFieldsRaw]
		# add id and shortTag to list
		questionnaireInfoList.append([int(recFields[1]),recFields[0]])
		# add id
	questionnaireFile.close()
	# create PageAnalysis file
	paFile = codecs.open('db dump/PageAnalysis.txt','w', encoding='utf-8')
	# for PageAnalysis file
	fieldList = ['PageAnalysis ID', 'questionnaire ID', 'questionnaire Tag', 'Page ID', 'Page Tag',
		'Test Condition', 'Test Result Flag', 'Test Flag Priority',
		'Test Flag Description', ]
	paFile.write("%s\n"%(fieldList))
	ii = 0
	for [aQuestid,aQuestTag] in questionnaireInfoList: # looping on questionnaires
		try:
			quaire = Questionnaire.objects.get(id=aQuestid)
		except Question.DoesNotExist:
			outMess= 'Grievous error:  Questionnaire record/Tag %s/%s in file Question.txt does not exist in Questionnaire DB' %(aQuestid,aQuestTag)
			ferrLog.write(outMess+os.linesep)
			print outMess
			continue
		# gather all records for PageAnalysis
		paObjs = PageAnalysis.objects.filter(
			questionnaireID=quaire,
			)
		if paObjs.count() == 0: # No PageAnalysis records for this Questionnaire. That's OK
			continue
		jjpa = 0 # count the PageAnalysis records written for this Questionnaire
		for paObj in paObjs: # examine each PageAnalysis record # looping on Questions
			fieldsToDumpRaw = [ # Compose the PageAnalysis text record
				paObj.id, # 0
				quaire.id, # 1
				quaire.shortTag, # 2
				paObj.pageID.id, #3
				paObj.pageID.shortTag, #4
				paObj.testCondition, #5
				paObj.testResultFlag, #6
				paObj.testResultFlagPriority, #7
				paObj.testResultFlagDescription, #8
				]
			fieldsToDump = [repTChar(aField) for aField in fieldsToDumpRaw]
			theLineToWrite = ",".join(fieldsToDump)
			paFile.write("%s\n" %theLineToWrite)
			ii+=1
			jjpa+=1 # count qp records per questionnaire
		print 'Found count of %s PageAnalysis records for Questionnaire %s' %(jjpa,quaire.shortTag)
	outMess = 'Number of PageAnalysis records: %s' %ii
	paFile.close()
	ferrLog.close()
	print 'dumpPageAnalysis:  exit'
	return outMess	

def loadPageAnalysis():
	"""Loads PageAnalysis file to the database.
	"""
	print 'PageAnalysis:  enter'
	ferrLog = open('db dump/ErrorLog.txt','a')
	paFile = open('db dump/PageAnalysis.txt','r')
	# fieldList = quaires[0]._meta.get_all_field_names()
	# for PageAnalysis file
# 	fieldList = ['PageAnalysis ID', 'questionnaire ID', 'questionnaire Tag', 'Page ID', 'Page Tag',
# 		'Test Condition', 'Test Result Flag', 'Test Flag Priority',
# 		'Test Flag Description', ]
	theH = paFile.readline() # skip header
	# read the record old/new decoding for the Questionaire table <===========
	questOldNewRec={}
	fQuestionaireRecDecode = open('db dump/QuestionnaireRecDecode.txt','r')
	for aRec in fQuestionaireRecDecode:
		[oldRecordID,newRecordID] = aRec.split(',')
		questOldNewRec.update({oldRecordID:int(newRecordID)})
	fQuestionaireRecDecode.close()
	# read the record old/new decoding for the Page table <===========
	pageOldNewRec={}
	fPageRecDecode = open('db dump/PageRecDecode.txt','r')
	for aRec in fPageRecDecode:
		[oldRecordID,newRecordID] = aRec.split(',')
		pageOldNewRec.update({oldRecordID:int(newRecordID)})
	fPageRecDecode.close()
	ii = 0
	for aPAFileRec in paFile: # Select a PageAnalysis
		aPAFileRec = aPAFileRec[:-1] # Remove line separator from the last field
		recFieldsSplt = aPAFileRec.split(',')
		recFields = [repPChar(aF) for aF in recFieldsSplt]
		# Questionnaire must already exist
		questid = recFields[1] # string version of the record number
		questShortTag = recFields[2]
		try:
			questObj = Questionnaire.objects.get(id=questOldNewRec[questid])
		except Questionnaire.DoesNotExist:
			outMess= 'loadPageAnalysis: Grievous error:  Questionnaire record/Tag %s/%s in PageAnalysis.txt does not exist in database' %(questid,questShortTag)
			ferrLog.write(outMess+os.linesep)
			print outMess
			continue # continue to next PageAnalysis record
		# Page must already exist
		pageid = recFields[3] # string version of the record number
		pageShortTag = recFields[4]
		try:
			pageObj = Page.objects.get(id=pageOldNewRec[pageid])
		except Page.DoesNotExist:
			outMess= 'loadPageAnalysis: Grievous error:  Page record/Tag %s/%s  in PageAnalysis.txt does not exist in database' %(pageid,pageShortTag)
			ferrLog.write(outMess+os.linesep)
			print outMess
			continue # continue to next PageAnalysis record
		# write the PageAnalysis record to the dtabase
		paObj=PageAnalysis.objects.create(
			questionnaireID=questObj,
			pageID=pageObj,
			testCondition=recFields[5],
			testResultFlag=recFields[6],
			testResultFlagPriority=recFields[7],
			testResultFlagDescription=recFields[8],
			)
		newRecordID=paObj.id
		oldRecordID=questid
		ii = ii + 1
	paFile.close()
	outMess = 'Number of PageAnalysis records added to database: %s' %ii
	print 'loadPageAnalysis:  exit'
	return outMess	

def dumpSubmission():
	# Dumps Submissions to a file
	print('dumpSubmission:  enter')
	allRespondents = Respondent.objects.all()
	fpageA = codecs.open('db dump/Respondent.txt','w', encoding='utf-8')
	
	for aRespondent in allRespondents:
		fpageA.write("%s\n"%(aRespondent.id))
		fpageA.write("%s\n"%(aRespondent.lastName))
		fpageA.write("%s\n"%(aRespondent.middleName))
		fpageA.write("%s\n"%(aRespondent.firstName))
		fpageA.write("%s\n"%(aRespondent.birthDate))
		fpageA.write("%s\n"%(aRespondent.contactEmail))
		fpageA.write("%s\n"%(aRespondent.contactPhone))
		fpageA.write("%s\n"%(aRespondent.externalID))
		fpageA.write("%s\n"%(aRespondent.externalIDAuthority))
		fpageA.write("%s\n"%(aRespondent.ptUniqueID))
	fpageA.close()
	allSubmissions = Submission.objects.all()
	fpageA = codecs.open('db dump/Submission.txt','w', encoding='utf-8')
	for aSubmission in allSubmissions:
		fpageA.write("%s\n"%(aSubmission.id))
		fpageA.write("%s\n"%(aSubmission.questionnaireID.shortTag))
		fpageA.write("%s\n"%(aSubmission.respondentID.ptUniqueID))
		fpageA.write("%s\n"%(aSubmission.lastUpdate))
		fpageA.write("%s\n"%(aSubmission.completedYN))
		fpageA.write("%s\n"%(aSubmission.reviewedBy))
		fpageA.write("%s\n"%(aSubmission.reviewDate))
		fpageA.write("%s\n"%(aSubmission.okForExport))
	fpageA.close()
	#
	allSubmissionAnalysiss = SubmissionAnalysis.objects.all()
	fpageA = codecs.open('db dump/SubmissionAnalysis.txt','w', encoding='utf-8')
	for aSubmissionAnalysis in allSubmissionAnalysiss:
		fpageA.write("%s\n"%(aSubmissionAnalysis.id))
		fpageA.write("%s\n"%(aSubmissionAnalysis.submissionID.id))
		fpageA.write("%s\n"%(aSubmissionAnalysis.testResultFlag))
		fpageA.write("%s\n"%(aSubmissionAnalysis.testResultDescription))
	fpageA.close()
	#
	allResponses = Response.objects.all()
	fpageA = codecs.open('db dump/Response.txt','w', encoding='utf-8')
	for aResponse in allResponses:
		fpageA.write("%s\n"%(aResponse.id))
		# determine "SubmissionID" from the following items
		fpageA.write("%s\n"%(aResponse.submissionID.id))
		fpageA.write("%s\n"%(aResponse.questionID.questionTag))
	fpageA.close()
	allResponseSelections = ResponseSelection.objects.all()
	fpageA = codecs.open('db dump/ResponseSelection.txt','w', encoding='utf-8')
	for aResponseSelection in allResponseSelections:
		fpageA.write("%s\n"%(aResponseSelection.id))
		fpageA.write("%s\n"%(aResponseSelection.responseID.id))
		fpageA.write("%s\n"%(aResponseSelection.language))
		fpageA.write("%s\n"%(aResponseSelection.responseText))
		fpageA.write("%s\n"%(aResponseSelection.responseType))
	fpageA.close()
	print('dumpSubmission:  exit')
	return True
	
def loadSubmission():
	# Loads Submissions to the database
	print('loadSubmission:  enter')
	Respondent.objects.all().delete() # delete and replace

	fpageA = open('db dump/Respondent.txt','r')
	for aline in fpageA:
		aRespondent
	
	print('loadSubmission:  exit')
	return True
