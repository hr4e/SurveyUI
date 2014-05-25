# Forms for screener pages
from django import forms
from django.forms.widgets import RadioSelect
from django.utils.safestring import mark_safe, SafeString
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
#from multiquest.views import SubstituteWords
from django.forms import ModelForm
from multiquest.models import Project, ResponseChoice

theYESNOChoices = (('Yes', 'Yes'), ('No', 'No'))
ChoiceTypes = [
	'MultipleChoiceField',
	'MultipleChoiceRequiredField',
	'SingleChoiceField',
	]
FIELD_TYPES = (# Form field type
	('CharField', 'CharField'),	# less than 100 characters
	('TextField', 'TextField'), # larger amounts of text
#	('DateField', 'DateField'),
#	('DecimalField', 'DecimalField'),
	('IntegerField', 'IntegerField'),
#	('EmailField', 'EmailField'), # checks for email format
	('MultipleChoiceField', 'MultipleChoiceField'), # select some, all or none.
	('MultipleChoiceRequiredField', 'MultipleChoiceRequiredField'), # at least one selection is required
	('SingleChoiceField', 'SingleChoiceField'), # Select only one choice, required
	('YesNoField', 'YesNoField'), # single choice 'Yes' or 'No'
#	('BooleanField', 'BooleanField'), # single choice check box
)
class ProjectForm(ModelForm):
	class Meta:
		model = Project
#		fields = ['shortTag', 'name', 'abbrev', 'projectAddress', 'email', 'contactPhone', 'internetLocation']


class RespondentIdentForm(forms.Form):
	error_css_class = 'error'
	required_css_class = 'required'
	firstName = forms.CharField(max_length=50, label='My first name is'
		,widget=forms.TextInput(attrs={'class':'inlineLabels'}))
	middleName = forms.CharField(max_length=50,  required=False, label='My middle name is'
		,widget=forms.TextInput(attrs={'class':'inlineLabels'}))
	lastName = forms.CharField(max_length=50, label='My last name is'
		,widget=forms.TextInput(attrs={'class':'inlineLabels'}))
	birthDate = forms.DateField(label='My birth date is (mm/dd/yyyy)'
		,widget=forms.TextInput(attrs={'class':'inlineLabels'}))
	contactPhone = forms.CharField( max_length=30, label='My phone number is (NNN-NNN-NNNN)'
		,widget=forms.TextInput(attrs={'class':'inlineLabels'}))
	contactEmail = forms.EmailField( required=False, label='(optional) My e-mail address is'
		,widget=forms.TextInput(attrs={'class':'inlineLabels'}))
#	externalID = forms.CharField( required=False, label='(optional) My identification number is')
#	externalIDAuthority = forms.CharField( required=False, label='(optional) Institution issuing your idenfication')

class PageForm(forms.Form):
	pageTitle = forms.CharField(label='Banner', max_length=100, help_text='Appears at the top of every page.'
		,widget=forms.TextInput(attrs={'class':'bigBanner'}))
	pageSubTitle = forms.CharField(label='Sub Banner',required=False, max_length=100, help_text='Appears just below the banner')
	shortTag = forms.CharField(label='short tag', help_text='*** only contiguous characters, no blanks.')
		# *** only contiguous characters, no blanks, no underscores. Must make a legal url
	description = forms.CharField(required=False, widget=forms.Textarea({'cols' :'50','rows' :'1'}), max_length=100, help_text='Does not appear to the respondent')
	explanation = forms.CharField(required=False, widget=forms.Textarea({'cols' :'50','rows' :'5'}), max_length=1000, help_text='Appears underneath the banner')
		# Provide context for the page.
	prologue = forms.CharField(required=False, widget=forms.Textarea({'cols' :'50','rows' :'5'}), max_length=1000, help_text="Appears before the question('s)")
	epilogue = forms.CharField(required=False, widget=forms.Textarea({'cols' :'50','rows' :'5'}), max_length=1000, help_text="Appears after the question('s)")

class PageTransitionForm(forms.Form):
	workingProjectTag = forms.CharField(label='current Project tag', help_text='*** only contiguous characters, no blanks.')
	workingQuestionnaireTag = forms.CharField(label='current Questionnaire tag', help_text='*** only contiguous characters, no blanks.')
	workingPageTag = forms.CharField(label='current Page tag', help_text='*** only contiguous characters, no blanks.')	

class QuestionForm(forms.Form):
	questionTag = forms.CharField(label='short tag', help_text='*** only contiguous characters, no blanks.')
		# *** only contiguous characters, no blanks, no underscores. Must make a legal url
	questionText = forms.CharField(widget=forms.Textarea, max_length=200, help_text='Appears as a question.')
	description = forms.CharField(required=False, widget=forms.Textarea, max_length=500, help_text='Does not appear on the page')
		# Provide context for the Question to the person building the questionnaire.
	responseType = forms.CharField(required=False, widget=forms.Textarea, max_length=30, help_text="e.g. CharField")

class PageQuestionLinkForm(forms.Form):
	questionSeq = forms.CharField(label='Enter the number in the question list where the new question is to appear. Other questions will be bumped down.')
	
class setPageToPageTransitionForm(forms.Form):
	nextPageTag = forms.CharField(label='short tag of the next page to transition to', help_text='*** only contiguous characters, no blanks.')

class setGlobalFlagForm(forms.Form):
	testResultFlag = forms.CharField( label='Global flag (max 30 characters)',max_length=30)
	testResultFlagPriority = forms.CharField( label='Global flag priority (use single characters, a,b,c)',max_length=10)
	testResultFlagDescription = forms.CharField( label='Global flag description (max 100 letters)',max_length=100)
	
class editSummaryAndAnalysisForm(forms.Form):
	newSummaryPage = forms.CharField( label='Summary page tag', max_length=30)
	
class editQuestionnaireForm(forms.Form):
	shortTag = forms.CharField(label='Short tag', max_length=30) # short tag for questionnaire selection
		# *** only contiguous characters, no blanks, no underscores. Must make a legal url
	barTitle = forms.CharField(label='Text on the title bar', max_length=100) # for text on page window title bar
	pageTitle = forms.CharField(label='Banner at the top of every page', max_length=100) # for (header) text to appear at the top of every page
	pageSubTitle = forms.CharField(label='Banner subtitle',required=False, max_length=100) # further, smaller, text below the header
	description = forms.CharField(required=False, max_length=100, help_text='Short description. Does not appear to the respondent')
	footerText = forms.CharField(label='Footer at the bottom of every page', required=False, max_length=100)
	version = forms.CharField(label='Questionnaire version (appears in the footer)', max_length=30)
	versionDate = forms.DateTimeField(label='Version date',required=False)
	language = forms.CharField( max_length=30)

class editDefaultTransitions(forms.Form):
	ptlString = forms.CharField(label='Default page transitions', 
		widget=forms.Textarea({'cols' :'80','rows' :'10'}), max_length=500,required=False)


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, help_text="Required. 30 characters or fewer.")
    last_name = forms.CharField(max_length=30, help_text="Required. 30 characters or fewer.")
    email = forms.EmailField(max_length=75, help_text="Required. 75 characters or fewer.")

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email",)

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class UploadFileForm(forms.Form):
    theFile  = forms.FileField()


# http://jacobian.org/writing/dynamic-form-generation/
class UserFormPoly(forms.Form):
	def __init__(self,  *args, **kwargs):
		quests= kwargs.pop('questions')
		if 'choices' in kwargs:
			theChoices = kwargs.pop('choices')
		super(UserFormPoly, self).__init__( *args, **kwargs)		
		for aQuestion in quests:
			# aQuestion is a dictionary
			theQRespType = aQuestion.get('responseType',None)
			theQText = mark_safe(aQuestion.get('questionText',None)) # allow html
 			theQLabel = aQuestion.get('theQLabel',None)
			if theQRespType == 'MultipleChoiceField':
				self.fields[theQLabel] = forms.MultipleChoiceField( label=theQText, required=False, widget=forms.CheckboxSelectMultiple(attrs={'class':'inlineLabels'}), choices=theChoices)
			elif theQRespType == 'MultipleChoiceRequiredField':
				self.fields[theQLabel] = forms.MultipleChoiceField( label=theQText, widget=forms.CheckboxSelectMultiple(attrs={'class':'inlineLabels'}), choices=theChoices)
			elif theQRespType == 'YesNoField':
				self.fields[theQLabel] = forms.ChoiceField(label=theQText, widget=forms.RadioSelect(attrs={'class':'inlineLabels'}), choices=theYESNOChoices)
			elif theQRespType == 'SingleChoiceField':
				self.fields[theQLabel] = forms.ChoiceField(label=theQText, widget=forms.RadioSelect(attrs={'class':'inlineLabels'}), choices=theChoices)
			elif theQRespType == 'BooleanField':
				self.fields[theQLabel] = forms.BooleanField(label=theQText, required=False)
			elif theQRespType == 'CharField':
				self.fields[theQLabel] = forms.CharField( widget=forms.TextInput(attrs={'class':'inlineLabels'}),label=theQText, max_length=100)
			elif theQRespType == 'IntegerField':
				self.fields[theQLabel] = forms.IntegerField( widget=forms.TextInput(attrs={'class':'inlineLabels'}),label=theQText)
#	required_css_class = 'inlineLabels'
	
class BulkPageEditForm(forms.Form):
	def __init__(self,  *args, **kwargs):
		if 'questions' in kwargs:
			quests= kwargs.pop('questions')
		else:
			quests=[]
		if 'choices' in kwargs:
			theChoices = kwargs.pop('choices')
		super(BulkPageEditForm, self).__init__( *args, **kwargs)		
		self.fields['description'] = forms.CharField(required=False, label='Page Description', max_length=100, help_text='Page Description:  Does not appear to the respondent'
			,widget=forms.TextInput({'size':'92'}))
		self.fields['explanation'] = forms.CharField(required=False, widget=forms.Textarea({'cols' :'90','rows' :'5'}), max_length=1000, help_text='Explanation:  Appears underneath the banner')
			# Provide context for the page.
		self.fields['prologue'] = forms.CharField(required=False, widget=forms.Textarea({'cols' :'90','rows' :'5'}), max_length=1000, help_text="Prologue:  Appears before the question('s)")
		questionCount = 1
		for aQuestion in quests:
			theQText = aQuestion.questionText
			theQTag = 'QuestionText_'+str(questionCount)
			self.fields[theQTag] = forms.CharField(initial=theQText, required=False, label=theQTag, widget=forms.Textarea({'cols' :'90','rows' :'1','class':'inlineLabels'}), max_length=400)
			theQRespType = aQuestion.responseType
			theQRTag = 'QuestionType_'+str(questionCount)
			self.fields[theQRTag] = forms.ChoiceField(initial=theQRespType, required=False, label=theQRTag, choices=FIELD_TYPES)
			questionCount+=1
			theResponses = ResponseChoice.objects.order_by('choiceSequence').filter(questionID=aQuestion)
			choiceCount=1
			for aResponse in theResponses:
				choiceTag = 'Choice_'+str(choiceCount)
				choiceCount+=1
				choiceText = aResponse.choiceText
				self.fields[choiceTag] = forms.CharField(initial=choiceText, required=False, label=choiceTag, widget=forms.TextInput({'size' :'80','class':'inlineLabels'}), max_length=100)
			if choiceCount >1:
				# add a blank choice to the end of the multiple choice
				choiceTag = 'Choice_'+str(choiceCount)
				choiceText = '' # blank
				self.fields[choiceTag] = forms.CharField(initial=choiceText, required=False, label=choiceTag, widget=forms.TextInput({'size' :'80','class':'inlineLabels'}), max_length=100)
				
		self.fields['epilogue'] = forms.CharField(required=False, widget=forms.Textarea({'cols' :'90','rows' :'5'}), max_length=1000, help_text="Epilogue:  Appears after the question('s)")

class BulkQuestionEditForm(forms.Form):
	def __init__(self,  *args, **kwargs):
		if 'questions' in kwargs:
			quests= kwargs.pop('questions')
		else:
			quests=[]
		if 'choices' in kwargs:
			theChoices = kwargs.pop('choices')
		super(BulkQuestionEditForm, self).__init__( *args, **kwargs)		
		for aQuestion in quests:
			theQRespType = aQuestion.responseType
			theQTag = aQuestion.questionTag
			self.fields[theQTag] = forms.CharField(label=theQTag, widget=forms.Textarea({'cols' :'90','rows' :'1','class':'inlineLabels'}), max_length=400)
			if theQRespType in ChoiceTypes:
				self.fields[theQTag] = forms.CharField(label=theQTag, widget=forms.Textarea({'cols' :'90','rows' :'1','class':'inlineLabels'}), max_length=100)
		self.fields['epilogue'] = forms.CharField(required=False, widget=forms.Textarea({'cols' :'90','rows' :'5'}), max_length=1000, help_text="Appears after the question('s)")

