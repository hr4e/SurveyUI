from django.db import models
import datetime
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.forms import ModelForm
from django.contrib.auth.models import Group, User

# Create model for multiple questionnaires

FIELD_TYPES = (# Form field type
	('CharField', 'CharField'),	# less than 100 characters
	('TextField', 'TextField'), # larger amounts of text
	('DateField', 'DateField'),
	('DecimalField', 'DecimalField'),
	('IntegerField', 'IntegerField'),
	('EmailField', 'EmailField'), # checks for email format
	('MultipleChoiceField', 'MultipleChoiceField'), # select some, all or none.
	('MultipleChoiceRequiredField', 'MultipleChoiceRequiredField'), # at least one selection is required
	('SingleChoiceField', 'SingleChoiceField'), # Select only one choice, required
	('YesNoField', 'YesNoField'), # single choice 'Yes' or 'No'
	('BooleanField', 'BooleanField'), # single choice check box
)

PAGE_TYPES = (# page type
	('singlePass', 'singlePass'), # single question
	('multiPass', 'multiPass'),
	('sendQuestions', 'sendQuestions'),
	('hasTemplateAndFunction', 'hasTemplateAndFunction'),
	('completion', 'completion'),
	('respondentID', 'respondentID'),
	('questionnaireSummary', 'questionnaireSummary'),
)
KEY_NAME = (# key category for Attributes
	('NotEditable', 'Not Editable'),
	('Display', 'Display'),
	('DoNotDisplay', 'Do Not Display'),
	('Archive', 'Archive'),
)


class Question(models.Model):
	questionTag = models.CharField(max_length=50) # unique question selection tag
	questionText = models.TextField(max_length=400) # Actual question text seen by respondent.
	helpText = models.CharField(blank=True, max_length=500) # Additional text presented to respondent.
	lastUpdate = models.DateTimeField(auto_now=True)
	explanation = models.TextField(blank=True, max_length=500) # Further explanation
	language = models.CharField(default='English', max_length=30)
	description = models.TextField(max_length=100) # Short description. Not presented to respondent.
	imageFilePath = models.FileField(blank=True, upload_to='/multiquest')
	imageFileName = models.CharField(blank=True, max_length=30)
	imageFileType = models.CharField(blank=True, max_length=30)
	responseType = models.CharField(max_length=30, choices=FIELD_TYPES)
	
	def __unicode__(self):
		return u'%s, %s, %s, %s, %s\n' % (self.id, self.questionTag, self.questionText, self.responseType, str(self.lastUpdate))
		
	class Meta:
		ordering = ['questionTag']
		
class ResponseChoice(models.Model):
	questionID = models.ForeignKey(Question) # points to a question of type 'MultipleChoiceField'
	choiceTag = models.CharField(max_length=30)
	choiceText = models.CharField(max_length=200)
	choiceType = models.CharField(max_length=30, choices=FIELD_TYPES) # not used
	choiceSequence = models.CharField(max_length=10) # use character sort
	
	def __unicode__(self):
		return  u'%s %s %s %s %s \n' % (self.id,self.choiceTag, self.choiceText, self.choiceSequence, self.choiceType)

	class Meta:
		ordering = ['choiceSequence']

class Page(models.Model):
	shortTag = models.CharField('short tag', max_length=30, help_text='*** only contiguous characters, no blanks.')
		# *** only contiguous characters, no blanks, no underscores. Must make a legal url
	pageType = models.CharField('page type', max_length=30, choices=PAGE_TYPES, help_text='Further instructions to html rendering.')
	description = models.CharField(blank=True, max_length=100, help_text='Short description. Does not appear to the respondent')
	explanation = models.TextField(blank=True, max_length=1000, help_text='Appears underneath the banner')
		# Provide context for the page.
	prologue = models.TextField(blank=True, max_length=1000, help_text="Appears before the question('s)")
	epilogue = models.TextField(blank=True, max_length=1000, help_text="Appears after the question('s)")
	lastUpdate = models.DateTimeField(auto_now=True)
	helpPage = models.CharField(blank=True, max_length=200)
	helpButtonTitle = models.CharField(blank=True, max_length=50)
	language = models.CharField(default='English', max_length=30)
	imageFilePath = models.FileField(blank=True, upload_to='/multiquest/working_pages/images/')
	imageFileName = models.CharField(blank=True, max_length=40)
	imageFileType = models.CharField(blank=True, max_length=30)

	def __unicode__(self):
		return u'%s, %s, %s, %s, %s\n' % (self.id,self.shortTag, self.pageType, self.description, self.lastUpdate)

	class Meta:
		ordering = ['shortTag']

class Project(models.Model):
	shortTag = models.CharField(max_length=30)  # unique project abbreviation used as url
		# *** only contiguous characters, no blanks, no underscores. Must make a legal url
	abbrev = models.CharField(max_length=20,verbose_name='Abbreviation')
	name = models.CharField(max_length=100)
	projectAddress = models.CharField(max_length=100, blank=True)
	lastUpdate = models.DateTimeField(auto_now=True)
	email = models.EmailField(max_length=50, blank=True)
	contactPhone = models.CharField(max_length=30, blank=True)
	internetLocation = models.TextField(max_length=250, blank=True)
	
	def __unicode__(self):
		return u'%s, %s, %s, %s\n' % (self.id ,self.shortTag, self.name, self.lastUpdate)
	
	class Meta:
		ordering = ['name']

class UserProject(models.Model):
	userID = models.ForeignKey(User)
	projectID = models.ForeignKey(Project,verbose_name='Project')

	def __unicode__(self):
		return u'%s, %s, %s, %s, %s\n' % (self.projectID.shortTag, self.userID.last_name, self.userID.first_name ,self.userID.email, self.userID.username)

class ProjectAttributes(models.Model):
	projectID = models.ForeignKey(Project)
	keyName = models.CharField(max_length=30, choices=KEY_NAME)
	keyValue = models.CharField(max_length=50, blank=True)
	keyDescription = models.CharField(max_length=100, blank=True)
	keyCategory = models.CharField(blank=True, max_length=30)

	def __unicode__(self):
		return u'%s, %s, %s, %s, %s\n' %( self.projectID.shortTag, self.keyName, self.keyValue, self.keyDescription, self.keyCategory)

class Questionnaire(models.Model):
	shortTag = models.CharField(verbose_name='Short tag', max_length=30) # short tag for questionnaire selection
		# *** only contiguous characters, no blanks, no underscores. Must make a legal url
	barTitle = models.CharField(verbose_name='Text on the title bar', max_length=100) # for text on page window title bar
	pageTitle = models.CharField(verbose_name='Banner at the top of every page', max_length=100) # for (header) text to appear at the top of every page
	pageSubTitle = models.CharField(verbose_name='Banner subtitle',blank=True, max_length=100) # further, smaller, text below the header
	description = models.CharField(blank=True, max_length=100, help_text='Short description. Does not appear to the respondent')
	footerText = models.CharField(verbose_name='Footer at the bottom of every page', blank=True, max_length=100)
	version = models.CharField(verbose_name='Questionnaire version (appears in the footer)', max_length=30)
	versionDate = models.DateTimeField(verbose_name='Version date',blank=True)
	lastUpdate = models.DateTimeField(auto_now=True)
	language = models.CharField(default='English', max_length=30)
	imageFilePath = models.FileField(blank=True, upload_to='/multiquest/images', verbose_name='Image file (if any)')
	imageFileName = models.CharField(blank=True, max_length=30)
	imageFileType = models.CharField(blank=True, max_length=10)

	def __unicode__(self):
		return u'%s, %s, %s, %s\n' %( self.id, self.shortTag, self.pageTitle, self.lastUpdate)

	class Meta:
		ordering = ['pageTitle']
		
class QuestionnaireAttributes(models.Model):
	questionnaireID = models.ForeignKey(Questionnaire)
	keyName = models.CharField(max_length=30)
	keyValue = models.CharField(max_length=50, blank=True)
	keyDescription = models.CharField(max_length=100, blank=True)
	keyCategory = models.CharField(max_length=30, blank=True)

	def __unicode__(self):
		return u'%s, %s, %s, %s, %s\n' %( self.questionnaireID.shortTag, self.keyName, self.keyValue, self.keyDescription, self.keyCategory)
	
	class Meta:
		ordering = ['keyName']

class QuestionnairePage(models.Model):	# Many to many intermediary between Page and Questionniare
	# determine "next page" via by default or by test condition
	questionnaireID = models.ForeignKey(Questionnaire)
	pageID = models.ForeignKey(Page, related_name='current_page')
	nextPageID = models.ForeignKey(Page,null=True, related_name='next_page') # A default which may be superseded by page/question logic.
	testCondition = models.CharField(default='next_page_default', max_length=500, help_text='When satisfied go to the nextPage')
	recordType = models.CharField(max_length=30, default='next_page_default')

	def __unicode__(self):
		return u'%s, %s, %s, %s, %s, %s\n' %( self.id, self.questionnaireID.shortTag, self.pageID.shortTag, self.nextPageID.shortTag, self.testCondition, self.recordType)
	# record types are
		# 'next_page_default'
		# 'calculated'
		# 'globalflag'
		# 'start_page'
	class Meta:
		ordering = ['pageID']

class ProjectQuestionnaire(models.Model):
	projectID = models.ForeignKey(Project)
	questionnaireID = models.ForeignKey(Questionnaire)
	recordType = models.CharField(max_length=30, default='connection')
	questionnaireStatus = models.CharField(max_length=30, default='enabled')

	def __unicode__(self):
		return u'%s, %s, %s, %s\n' %( self.projectID.shortTag, self.questionnaireID.shortTag, self.recordType, self.questionnaireStatus)

class PageAnalysis(models.Model):	# Page level analysis.
	questionnaireID = models.ForeignKey(Questionnaire)
	pageID = models.ForeignKey(Page) # current page
	testCondition = models.CharField(max_length=500, help_text='When satisfied create the global flag "testResultFlag"')
	# the following is also referred to "global flag"
	testResultFlag = models.CharField(max_length=30, help_text='flag is enabled when testCondition is True')
	testResultFlagPriority = models.CharField(max_length=10, default='a') # use character sort
	testResultFlagDescription = models.CharField(blank=True, max_length=100) # use character sort
	def __unicode__(self):
		return u'%s, %s, %s, %s\n' % ( self.questionnaireID.shortTag, self.pageID.shortTag, self.testCondition, self.testResultFlag)

#	Analysis:
#	If testCondition matches: then set testResultFlag
#	If testCondition matches: All "Yes", then set testResultFlag
#	If testCondition matches: At least one "Yes", and perhaps all "Yes", then set testResultFlag
#	If testCondition matches: At least one "No", and perhaps all "No", then set testResultFlag
#	If testCondition matches: All "No", then set testResultFlag

class QuestionnaireAnalysis(models.Model):	# Questionnaire level analysis
	questionnaireID = models.ForeignKey(Questionnaire)
	testCondition = models.CharField(max_length=500, help_text='When satisfied set the value of testResultFlag')
	testResultFlag = models.CharField(max_length=30, help_text='flag is enabled when testCondition is True')

	def __unicode__(self):
		return u'%s %s %s\n' % (self.questionnaireID.shortTag, self.testCondition, self.testResultFlag)

class PageQuestion(models.Model):
	pageID = models.ForeignKey(Page)
	questionID = models.ForeignKey(Question)
	questionSequence = models.CharField(default='1',max_length=10) # use character sort
	questionGroup = models.CharField(default='1',max_length=10) # Use '2' to indicate a follow-on equation

	def __unicode__(self):
		return u'%s %s %s %s %s\n' % (self.id, self.questionSequence, self.pageID.shortTag, self.questionID.questionTag, self.questionID.questionText)
	
class Respondent(models.Model):
	lastName = models.CharField(max_length=50)
	middleName = models.CharField(blank=True, max_length=30)
	firstName = models.CharField(max_length=50)
	birthDate = models.DateField()
	contactEmail = models.EmailField(blank=True, verbose_name='e-mail')
	contactPhone = models.CharField(blank=True, max_length=30)
	externalID = models.CharField(blank=True, max_length=30)
	externalIDAuthority = models.CharField(blank=True, max_length=30)
	ptUniqueID = models.CharField(max_length=200, unique=True)
	
	def __unicode__(self):
		return u'%s, %s\n' % (self.lastName, self.firstName)

	class Meta:
		ordering = ['lastName', 'firstName']

class Submission(models.Model):
	questionnaireID = models.ForeignKey(Questionnaire)
	respondentID = models.ForeignKey(Respondent)
	lastUpdate = models.DateTimeField(auto_now=True)
	completedYN = models.BooleanField(default=False)
	reviewedBy = models.CharField(blank=True, max_length=30)
	reviewDate = models.DateTimeField(null=True, blank=True)
	okForExport = models.BooleanField(default=False) # Has been reviewed, and ok'd for export
	
	def __unicode__(self):
		return u'%s, %s, (%s, %s, %s)\n' % (self.lastUpdate, self.completedYN, self.respondentID.firstName, self.respondentID.middleName, self.respondentID.lastName)

	class Meta:
		ordering = ['lastUpdate']

class Response(models.Model):
	questionID = models.ForeignKey(Question)
	questionOnPageID = models.ForeignKey(Page)
	submissionID = models.ForeignKey(Submission)
	
	def __unicode__(self):
		return u' %s, %s, %s\n' % ( self.submissionID.respondentID.lastName, self.questionOnPageID.shortTag, self.questionID.questionTag)

	class Meta:
		ordering = ['questionID']

class ResponseSelection(models.Model):
	responseID = models.ForeignKey(Response)
	responseChoiceID = models.ForeignKey(ResponseChoice, null=True) # required only for multiple-choice
	language = models.CharField(default='English', max_length=30)
	responseText = models.CharField(blank=True, max_length=200) # depends upon the Question.responseType.
	responseType = models.CharField(max_length=30, choices=FIELD_TYPES) # not used
	
	def __unicode__(self):
		return u'%s, %s\n' % (self.language, self.responseText)

	class Meta:
		ordering = ['responseID']

class PageAttributes(models.Model):
	pageType = models.CharField('page type', max_length=30, choices=PAGE_TYPES, help_text='Further instructions to html rendering.')
	keyName = models.CharField(max_length=30)
	keyValue = models.CharField(max_length=50, blank=True)
	keyDescription = models.CharField(max_length=100, blank=True)
	keyCategory = models.CharField(max_length=30, blank=True)

	def __unicode__(self):
		return u'%s, %s, %s, %s, %s\n' %( self.pageType, self.keyName, self.keyValue, self.keyDescription, self.keyCategory)

class SubmissionAnalysis(models.Model):
	submissionID = models.ForeignKey(Submission)
	testResultFlag = models.CharField(max_length=30)
	testResultFlagPriority = models.CharField(max_length=10, default='a') # use character sort
	testResultDescription = models.TextField(blank=True, max_length=100)

	def __unicode__(self):
		return u'%s, %s, %s\n' % (self.submissionID.respondentID.ptUniqueID, self.testResultFlag, self.testResultDescription)

class RiskCalculation(models.Model): # Identifies the risk calculation
	riskType = models.CharField(max_length=50)
	riskCalcName = models.CharField(max_length=50)
	riskDescription = models.CharField(max_length=200)
	riskCalcVersion = models.CharField(max_length=50)
	submissionOrganization = models.CharField(max_length=50)

	def __unicode__(self):
		return u'%s, %s, %s\n' % ( self.riskType, self.riskCalcName, self.submissionOrganization)

class RiskSubmission(models.Model): # Connections risk calculation to the submission
	submissionID = models.ForeignKey(Submission)
	riskValue = models.CharField(max_length=50)
	riskCalculationID = models.ForeignKey(RiskCalculation)
	dateofSubmission = models.DateTimeField(auto_now=True)
	
	def __unicode__(self):
		return u'%s, %s, %s, %s\n' % ( self.submissionID.respondentID.lastName, self.riskValue, self.riskCalc.riskCalcName, self.dateofSubmission)

	