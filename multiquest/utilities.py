from django.utils import timezone
from django.utils.timezone import *
from datetime import datetime
from django.conf import settings
from dateutil.relativedelta import relativedelta
from django.utils.encoding import smart_str, smart_text
from os import listdir
import django
import os
from os.path import isfile, join
import glob
import codecs

# ==================================<h3>General Utilities and tools</h3>
# ==================================
# ==================================

def convertCSVMultiLineTo2DList(ptlLinesRaw):
	"""Reformats a transition matrix in the form of a multi-line character string,
	with each line comma separated keywords. Output is a two dimensional list of
	keywords.
	All blanks are removed!
		
	Args:
		a transition matrix in the form of a dictionary of a multi-line character string

	Returns:
		two dimensional list of keywords.

	Raises:
		None.
	"""
	ptlLines = ptlLinesRaw.replace(" ","").splitlines() # remove blanks, then split at end of line
	ptl2DList = []
	for aLineStr in ptlLines:
		aLineListTemp = aLineStr.split(',') # break at commas
		aLineList = filter(None, aLineListTemp) # remove '' null strings when
			# encountering successive commas or a comma at the end of the line.
		ptl2DList.append(aLineList)
		
	return ptl2DList
	
def transitionListToMatrix(tListOfLists):
	"""Reformats a transition matrix in the form of a list of lists of the objects in
	sequence to a dictionary of "from, to" pairs.
		
	Args:
		a transition matrix in the form of a list of lists. Each list element is a list of objects in sequence.

	Returns:
		a dictionary object. "From" is the index, and To is the result.

	Raises:
		None.
	"""
	tMatrixPairs={}
	for aList in tListOfLists:
		aListIter = iter(aList)
		fromItem = next(aListIter)
		for toItem in aListIter:
			tMatrixPairs.update({fromItem : toItem})
			fromItem = toItem
	return tMatrixPairs

def transitionListofList_To_FromToList(tListOfLists):
	"""Reformats a transition matrix in the form of a list of lists of the objects in
	sequence to a list of "from, to" pairs.
	Note:  if only one element on a line, then duplicate the item in the "to" slot
	Args:
		a transition matrix in the form of a list of lists. Each list element is a list of objects in sequence.

	Returns:
		a list of lists object. Output is a list of from/to list pairs

	Raises:
		None.
	"""
	tMatrixPairs=[]
	for aList in tListOfLists:
		aListIter = iter(aList)
		fromItem = next(aListIter)
		if len(aList) == 1:  # length of 1. Repeat the item - no place to go to!
			tMatrixPairs.append([fromItem , fromItem])
		else:
			for toItem in aListIter:
				tMatrixPairs.append([fromItem , toItem])
				fromItem = toItem
	return tMatrixPairs

def transitionMatrixTo2DList(tMatrixPairs):
	"""Reformats a transition matrix in the form of a dictionary of "from, to" pairs into a
	set of lists with the objects in sequence.
		
	Args:
		tMatrixPairs: a transition matrix in the form of a dictionary of "from, to" pairs

	Returns:
		a two dimensional list object. Each list element is a list of objects in sequence.

	Raises:
		None.
	"""
	# investigate all the elements
	DebugOut('transitionMatrixTo2DList: enter')
	if not tMatrixPairs:
		elemToElemListOut = []
		DebugOut('transitionMatrixTo2DList: Exit - input null')
		return elemToElemListOut
	fromSet = set([])
	toSet = set([])
	for pFrom, pTo in tMatrixPairs.iteritems():
		fromSet.add(pFrom)
		toSet.add(pTo)	
	# find elements with no precedent.
	noPrecedent = fromSet - toSet # subtract to from from
# 	if noPrecedent:
# 		DebugOut('Elements with no precedent:  %s' %list(noPrecedent))
	allSet = fromSet | toSet # Union of two sets represent all elements
	numUnique = len(allSet)
	# create a character string representation
	elemToElemListLen = []
	for anItem in noPrecedent:
		currObj = anItem # start at the beginning
# 		DebugOut('currObj:  %s' %currObj)
		consecutiveFromTo = [currObj]
		elementsInThisLine = [] # accumulate elements in this line to avoid infinite loop
		while True:
			try:
				toObj = tMatrixPairs[currObj]
				if toObj in elementsInThisLine:
					break # end the while loop, repeating element.
				elementsInThisLine.append(toObj)
				consecutiveFromTo.append(toObj)
				currObj = toObj
			except KeyError:
				break # ok. Just came to the end of the string
		setEtoE = set(consecutiveFromTo)
		# calculate the number of elements unique to this string
		numUInconsecutive = numUnique - len(allSet-setEtoE) # number of unique consecutive items in a line
		elemToElemListLen.append([numUInconsecutive,consecutiveFromTo])
	# Sort sublist lengths so that the longest is first.
	elemToElemListLen.sort(reverse=True)
	# Restructure the list
	elemToElemListOut = []
	previousElementsRefd = [] # a list of previous elements, going top to bottom
	# Identify the first (and longest) list.
	firstList = elemToElemListLen[0][1]
	
	elemToElemListOut.append(firstList) # start the output list
	previousElementsRefd.extend(firstList) # accumulate the list of unique elements
	# iterate on the remaining lists, if any, in elemToElemListLen
	if len(elemToElemListLen) > 1:
		for [ll,aList] in elemToElemListLen[1:]:
			# go through each element discarding elements already seen
			# with firstList, except for the first appearance of an element already seen
			# this logic shows where this sublist connects with one of the above sublists
			subListElems = []
			for anElm in aList:
				if anElm in previousElementsRefd: # special logic
					subListElems.append(anElm) # reconnects with prior sublist
					break # discard remaining elements, they must duplicate prior sublist
				else:
					subListElems.append(anElm) # add to the list of elements "seen"
					previousElementsRefd.append(anElm) # add to list of previous elements
			elemToElemListOut.append(subListElems)
	#else: # done
	DebugOut('transitionMatrixTo2DList: exit')
	return elemToElemListOut

def transitionMatrixToMultiLineDisplay(tMatrixPairs):
	"""Reformats a transition matrix in the form of a dictionary of "from, to" pairs into a
	set of lists with the objects in sequence. Objects must have a string representation
		
	Args:
		tMatrixPairs: a transition matrix in the form of a dictionary of "from, to" pairs

	Returns:
		a multi-line string. Each page is separated by commas.

	Raises:
		None.
	"""
	PToPTrans2DList = transitionMatrixTo2DList(tMatrixPairs)
	defaultPTList = ''
	for aLine in PToPTrans2DList:
		DebugOut('transitionMatrixToMultiLineDisplay: aLine: %s' %aLine)
		lineStr = ', '.join(aLine)+os.linesep
		DebugOut('transitionMatrixToMultiLineDisplay: lineStr: %s' %lineStr)
		defaultPTList = defaultPTList + lineStr
	DebugOut('transitionMatrixToMultiLineDisplay: defaultPTList: %s' %defaultPTList)
	return defaultPTList
	
def dirListFiles(theStartPath):
	"""Lists files in the directory indicated by theStartPath, with wildcards.
	Default start directory is directory containing manage.py
		
	Args:
		path to a directory

	Returns:
		a list of file names - no path

	Raises:
		None.
	"""
	fileList = glob.glob(theStartPath)
	return fileList

def flattenList(xx):
	"""Flatten all levels in a list of lists to one level."""
	result = []
	for el in xx:
		if type(el) == list:
			result.extend(flattenList(el))
		else:
			result.append(el)
	return result

def removeDupsFromBeginning(aList):
	"""Starting from the beginning of the list, remove duplicates following the original.
		
	Args:
		a list

	Returns:
		a list with duplicates removed

	Raises:
		None.
	"""
	bList = list(aList) # copies the list
	for ii, elm in enumerate(bList):
		if ii > 0: # accept the first element
			if elm in bList[0:ii-1]:
				del bList[ii]
	return bList
	
def removeDupsFromEnd(aList):
	"""Starting from the end of the list, remove duplicates.
		
	Args:
		a list

	Returns:
		a list with duplicates removed

	Raises:
		None.
	"""
	bList = list(aList) # copies the list
	seenList = [] # put elements "seen" here
	for ii, elm in reversed(list(enumerate(bList))):
		if elm in seenList: # remove the duplicate
			del bList[ii]
		else:
			seenList.append(elm) # now we've seen and checked it
	return bList
	
def getModelFieldList( theModel ):
	"""gets all of the fields in a model"""
	fieldList = theModel._meta.get_all_field_names() # returns as a list.
	# We are not done. The problem with fieldList is that it contains the name of tables
	# with foreign keys which point to theModel. Remove these.
	outField = []
	for aField in fieldList:
		try:
			theName = str(theModel._meta.get_field(aField).name) # uniformly string
			outField.append(theName)
		except: # name not in table
			continue
	# http://stackoverflow.com/questions/3106295/django-get-list-of-model-fields
	# https://django-model-internals-reference.readthedocs.org/en/latest/get_all_field_names.html
	return outField

def getModelFieldValueDict( theModel):
	"""Get fields and values from a model. Make a dictionary"""
	fieldList = getModelFieldList( theModel )
	qValueDict = {}
	for aFieldName in fieldList:
		try:
# 			qValueDict.update({aFieldName : unicode(getattr(theModel, aFieldName)).encode('utf-8')})
			qValueDict.update({aFieldName : getattr(theModel, aFieldName)}) # don't coerce!
		except AttributeError:
			pass # some fields (which ones?) will not be attributes of the model
	return qValueDict

def computertype(request): # identifies iPad or not!
	values = request.META.items()
	# tag needed is HTTP_USER_AGENT
	btype = dict(values)['HTTP_USER_AGENT']
	if 'Macintosh' in btype:
		currentComputer = 'Macintosh'
	elif 'iPad' in btype:
		currentComputer = 'iPad'
	elif 'Windows' in btype:
		currentComputer = 'Windows'
	else:
		currentComputer = 'computer'

	return currentComputer

def pagePerComputer( ct):
	DebugOut('pagePerComputer:  enter')
	DebugOut('ct:  %s' %ct)
	pageDetails = {}
	
	if ct == 'iPad':
		pageDetails['fontSize']='1.9em'
		pageDetails['fontSizeTextBox']='.9em'
	else:
		pageDetails['fontSize']='1.2em'
		pageDetails['fontSizeTextBox']='.8em'
	DebugOut('pagePerComputer:  enter')
	return pageDetails
	
def calculate_ptAge_now( bd):
	# convert all times to local timezone
	now = timezone.now()
	nowtz = make_aware(now, timezone.get_current_timezone())
	bdtz = make_aware(bd, timezone.get_current_timezone())
	age = 0
	return age
	
	# another algorithm
	# http://stackoverflow.com/questions/16613960/finding-out-age-in-months-and-years-given-dob-in-a-csv-using-python/16614616#16614616

def getage(now, dob):
	years = now.year - dob.year
	months = now.month - dob.month
	if now.day < dob.day:
		months -= 1
		while months < 0:
			months += 12
			years -= 1
	return '%sy%smo'% (years, months)

def makeUniqueTag( tagList, theTag, maxLength):
	"""Makes a unique tag with respect to "tagList".
	Args:
		tagList - list of character strings
		theTag - character string to test
		maxLength - output character string is not to exceed.
	"""
	# remove from the end of the tag anything like "_integer"
	theNewTag = str(theTag)
	splitTag = theTag.split('_')
	if len(splitTag) == 1:
		firstPart = theTag
	else: # > 1
		lastPart=splitTag[-1]
		try:
			# test for integer
			anInt=int(lastPart)
			# clip off the number
			firstPart=splitTag[0]
		except ValueError:
			# doesn't fit the profile
			firstPart = theTag
	for ii in range(1,100):
		if theNewTag in tagList:
			# conflict, so add the counter
			theNewTag = firstPart+'_'+str(ii)
		else:
			break
	return theNewTag
	
def makeUniqueList( listIn ):
	# output is a list of unique items in listIn with any duplicates following the first are deleted.
	# order is preserved
#	Reference: http://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order
	copyList = []
	copyList.extend(listIn)	# make a local copy of the list
	seen = set()
	return [ x for x in copyList if x not in seen and not seen.add(x)]

def makeUniqueListReverse( listIn ):
	# output is a list of unique items in listIn with any duplicates preceding the last are deleted.
	# order is preserved
#	Reference: http://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order
	copyList = []
	copyList.extend(listIn)	# make a local copy of the list
	copyList.reverse()
	seen = set()
	listOut = [ x for x in copyList if x not in seen and not seen.add(x)]
	listOut.reverse() # restore the original order
	return listOut

def appendToUniqueList( listIn, listAdd):
	# assume listIn consists of unique elements.
	# append listAdd to listIn removing previous duplicates, and appending unique listAdd to the end.
	# Remove duplicates in a list, then if the removed item is in listAdd it is added to the end of the list
	copyList = []
	copyList.extend(listIn)	# make a local copy of the list
	for item in listAdd: # check each element for a duplication # n^2 operation here
		copyList = [x for x in copyList if x != item] # remove all duplicates
	# we have removed all appearances of listAdd elements from copyList, now append listAdd
	copyList.extend(listAdd)
	return copyList

# debug tools ==================================
def display_meta(request):
	values = request.META.items()
	values.sort()
	html = []
	for k, v in values:
		html.append('<tr><td>%s</td><td>%s</td></tr>' % (k, v))
	return HttpResponse('<table>%s</table>' % '\n'.join(html))

def DebugOut( debugMessage):
	#now = timezone.now()
	# open a debug file
	if settings.DEBUG_1:
		try:
			fpage = open('debugInfo.txt','a')
			#fpage.write('mQuest:  Time: %s \n' % now)
			fpage.write( debugMessage + '\n')
			fpage.close()
		except:
#			settings.DEBUG_1 = False # persistent for this execution! No further failed opens
			pass
	return True

def transposeListMatrix(xx):
	"""Transpose matrix in two level list form"""
	tmat = map(list,zip(*xx)).copy()
	return tmat
	
def testU( debugMessage ):
	print( debugMessage )
	fpage = open('debugInfo.txt','a')
	#fpage.write('mQuest:  Time: %s \n' % now)
	fpage.write( debugMessage + '\n')
	fpage.close()
	
	return True
	
def repTChar( someText):
	"""Replaces troublesome characters. Replace commas and line feeds.
	"""
	# make the input text a string
	if type(someText) !=str:
#		someTextRepl = str(someText) # safe for "replace" function
		try: # Why is this required on a non-string??
			someTextRepl = unicode(someText) # safe for "replace" function
		except UnicodeEncodeError:
			someTextRepl = someText # so don't do it
	else:
		someTextRepl = someText
	pleasantText = someTextRepl.replace("\r","<lfeedr>").replace("\n","<lfeed>").replace(",","<aComma>")
	return pleasantText

def repPChar( someText):
	"""replace commas and line feeds
	"""
	troubleText = someText.replace("<aComma>",",").replace("<lfeedr>","\r").replace("<lfeed>",'\n')
	return troubleText

def dumpSelectedTable(fileOut, theTable):
	"""Dumps a table to a file
	1st line is "table separator" with table name
	2nd line is a list of fields starting with "id"
	3rd line and following are the field values
	"""
	print('dumpSelectedTable:  enter')
	tableName = theTable.__name__
	print('table name:  %s'%tableName)
	allRecs = theTable.objects.all()
	# write header field names
	allFieldNames = getModelFieldList( theTable )
	theHeaderToWrite = ",".join(allFieldNames)
	fileOut.write('<Table_separator>,'+tableName+os.linesep)
	fileOut.write("%s\n"%(theHeaderToWrite))
	for aRec in allRecs:
		print 'rec: %s' %aRec
		fieldsToDump=[]
		for aFieldName in allFieldNames:
			# make the characters fit on a comma delimited line with repTChar
			rawFieldValue = getattr(aRec, aFieldName)
			if isinstance(rawFieldValue.__class__,django.db.models.base.ModelBase):
				# is a class. Get record number
				print 'Is a class instance'
				fieldValue = str(rawFieldValue.id)
			else:
				fieldValue = repTChar(smart_str(rawFieldValue))
# 			print 'type %s'%str(type(fieldValue))
# 			fieldValue = unicode(getattr(aRec, aFieldName)).encode('utf-8')
			print '%s, %s'%(aFieldName, fieldValue)
			fieldsToDump.append(fieldValue)
		theLineToWrite = ",".join(fieldsToDump)
		fileOut.write("%s\n" %theLineToWrite)
	return

def dumpQueryTest():
	tableName = 'Page'
	fileName = 'test dump/%s.txt' %tableName
	fileOut = codecs.open(fileName,'w', encoding='utf-8')
	theQuerySet = Page.objects.filter(shortTag='P1')
	dumpQuerySet(fileOut, theQuerySet)
	fileOut.close()
	return
	

def dumpQuerySet(fileOut, theQuerySet):
	"""
	"""
	DebugOut('dumpQuerySet:  enter')
	# find the table name of the items in the queryset
	if theQuerySet:
		# has something in it
		theTableName = theQuerySet[0].__class__.__name__
		theTable = theQuerySet[0].__class__
	else:
		# nothing in the query set.
		# exit quietly
		return
	# write header field names
	fileOut.write('TableSeparator,'+theTableName+os.linesep)
	allFieldNames = getModelFieldList( theTable )
	theHeaderToWrite = ",".join(allFieldNames)
	fileOut.write("%s\n"%('HeaderLine,'+theHeaderToWrite))
	iRec=0
	for aRec in theQuerySet:
		iRec+=1
# 		print 'rec: %s' %aRec
		fieldsToDump=['Record']
		for aFieldName in allFieldNames:
			# make the characters fit on a comma delimited line with repTChar
			rawFieldValue = getattr(aRec, aFieldName)
			if isinstance(rawFieldValue.__class__,django.db.models.base.ModelBase):
				# is a class. Get record number
# 				print 'Is a class instance'
				fieldValue = str(rawFieldValue.id)
			else:
				fieldValue = repTChar(unicode(rawFieldValue))
# 			print 'type %s'%str(type(fieldValue))
# 			fieldValue = unicode(getattr(aRec, aFieldName)).encode('utf-8')
#			print '%s, %s'%(aFieldName, fieldValue)
			fieldsToDump.append(fieldValue)
		theLineToWrite = ",".join(fieldsToDump)
		fileOut.write(theLineToWrite+os.linesep)
	DebugOut('dumpQuerySet:  exit. recs: %s, fields: %s'%(iRec, len(allFieldNames)))
	return iRec
	
