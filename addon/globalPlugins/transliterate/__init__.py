# *-* coding: utf-8 *-*
# transliterate/__init__.py
#Much of this code adopted from the NVDA Translate add-on:
#Copyright (C) 2018 Yannick PLASSIARD
#This file is covered by the GNU General Public License.
#See the file LICENSE for more details.


import os, sys, time, codecs, re
import globalVars
import globalPluginHandler, logHandler, scriptHandler
try:
	import api, controlTypes
	import ui, wx, gui
	import core, config
	import speech
	from speech import *
	import json
	curDir = os.path.abspath(os.path.dirname(__file__))

	sys.path.insert(0, curDir)
	sys.path.insert(0, os.path.join(curDir, "html"))
	import addonHandler, languageHandler

except Exception as e:
	logHanaler.log.exception("Failed to initialize transliterate addon", e)
	raise e

addonHandler.initTranslation()
#
# Global variables
#

_translationCache = {}
_nvdaSpeak = None
_nvdaGetPropertiesSpeech = None
_gpObject = None
_lastError = 0
_enableTranslation = False
_lastTranslatedText = None
_lastTranslatedTextTime = 0


def transliterate(text):
	"""transliterates Old English text
	"""
	global _enableTransliteration

	try:
		appName = globalVars.focusObject.appModule.appName
	except:
		appName = "__global__"

	try:
		logHandler.log.info(text + '--__--__--__--__--')
		prepared = text.encode('utf8', ':/')
		#translated = mtranslate.translate(prepared, _gpObject.language)
	except Exception as e:
		return text

	return text


#
## Extracted and adapted from nvda/sources/speech/__init__.py
#

def speak(speechSequence: SpeechSequence,
					priority: Optional[Spri] = None):
	global _enableTranslation, _lastTranslatedText

	if _enableTranslation is False:
		return _nvdaSpeak(speechSequence=speechSequence, priority=priority)
	newSpeechSequence = []
	for val in speechSequence:
		if isinstance(val, str):
			v = transliterate(val)
			newSpeechSequence.append(v if v is not None else val)
		else:
			newSpeechSequence.append(val)
	_nvdaSpeak(speechSequence=newSpeechSequence, priority=priority)
	_lastTranslatedText = " ".join(x if isinstance(x, str) else ""	for x in newSpeechSequence)

#
## This is overloaded as well because the generated text may contain already translated text by
## the NVDA's locale system. In this overloaded function, we only translate text which is not
## already localized, such as object's name, value, or description
#

def getPropertiesSpeech(	# noqa: C901
		reason = controlTypes.REASON_QUERY,
		**propertyValues
):
	global oldTreeLevel, oldTableID, oldRowNumber, oldRowSpan, oldColumnNumber, oldColumnSpan
	textList: List[str] = []
	name: Optional[str] = propertyValues.get('name')
	if name:
		textList.append(transliterate(name))
	if 'role' in propertyValues:
		role=propertyValues['role']
		speakRole=True
	elif '_role' in propertyValues:
		speakRole=False
		role=propertyValues['_role']
	else:
		speakRole=False
		role=controlTypes.ROLE_UNKNOWN
	value: Optional[str] = propertyValues.get('value') if role not in controlTypes.silentValuesForRoles else None
	cellCoordsText: Optional[str] = propertyValues.get('cellCoordsText')
	rowNumber = propertyValues.get('rowNumber')
	columnNumber = propertyValues.get('columnNumber')
	includeTableCellCoords = propertyValues.get('includeTableCellCoords', True)

	if role == controlTypes.ROLE_CHARTELEMENT:
		speakRole = False
	roleText: Optional[str] = propertyValues.get('roleText')
	if (
		speakRole
		and (
			roleText
			or reason not in (
				controlTypes.REASON_SAYALL,
				controlTypes.REASON_CARET,
				controlTypes.REASON_FOCUS
			)
			or not (
				name
				or value
				or cellCoordsText
				or rowNumber
				or columnNumber
			)
			or role not in controlTypes.silentRolesOnFocus
		)
		and (
			role != controlTypes.ROLE_MATH
			or reason not in (
				controlTypes.REASON_CARET,
				controlTypes.REASON_SAYALL
			)
	)):
		textList.append(transliterate(roleText) if roleText else controlTypes.roleLabels[role])
	if value:
		textList.append(transliterate(value))
	states=propertyValues.get('states',set())
	realStates=propertyValues.get('_states',states)
	negativeStates=propertyValues.get('negativeStates',set())
	if states or negativeStates:
		labelStates = controlTypes.processAndLabelStates(role, realStates, reason, states, negativeStates)
		textList.extend(labelStates)
	# sometimes description key is present but value is None
	description: Optional[str] = propertyValues.get('description')
	if description:
		textList.append(transliterate(description))
	# sometimes keyboardShortcut key is present but value is None
	keyboardShortcut: Optional[str] = propertyValues.get('keyboardShortcut')
	if keyboardShortcut:
		textList.append(keyboardShortcut)
	if includeTableCellCoords and cellCoordsText:
		textList.append(cellCoordsText)
	if cellCoordsText or rowNumber or columnNumber:
		tableID = propertyValues.get("_tableID")
		# Always treat the table as different if there is no tableID.
		sameTable = (tableID and tableID == oldTableID)
		# Don't update the oldTableID if no tableID was given.
		if tableID and not sameTable:
			oldTableID = tableID
		# When fetching row and column span
		# default the values to 1 to make further checks a lot simpler.
		# After all, a table cell that has no rowspan implemented is assumed to span one row.
		rowSpan = propertyValues.get("rowSpan") or 1
		columnSpan = propertyValues.get("columnSpan") or 1
		if rowNumber and (not sameTable or rowNumber != oldRowNumber or rowSpan != oldRowSpan):
			rowHeaderText: Optional[str] = propertyValues.get("rowHeaderText")
			if rowHeaderText:
				textList.append(rowHeaderText)
			if includeTableCellCoords and not cellCoordsText: 
				# Translators: Speaks current row number (example output: row 3).
				rowNumberTranslation: str = _("row %s") % rowNumber
				textList.append(rowNumberTranslation)
				if rowSpan>1 and columnSpan<=1:
					# Translators: Speaks the row span added to the current row number (example output: through 5).
					rowSpanAddedTranslation: str = _("through %s") % (rowNumber + rowSpan - 1)
					textList.append(rowSpanAddedTranslation)
			oldRowNumber = rowNumber
			oldRowSpan = rowSpan
		if columnNumber and (not sameTable or columnNumber != oldColumnNumber or columnSpan != oldColumnSpan):
			columnHeaderText: Optional[str] = propertyValues.get("columnHeaderText")
			if columnHeaderText:
				textList.append(transliterate(columnHeaderText))
			if includeTableCellCoords and not cellCoordsText:
				# Translators: Speaks current column number (example output: column 3).
				colNumberTranslation: str = _("column %s") % columnNumber
				textList.append(colNumberTranslation)
				if columnSpan>1 and rowSpan<=1:
					# Translators: Speaks the column span added to the current column number (example output: through 5).
					colSpanAddedTranslation: str = _("through %s") % (columnNumber + columnSpan - 1)
					textList.append(colSpanAddedTranslation)
			oldColumnNumber = columnNumber
			oldColumnSpan = columnSpan
		if includeTableCellCoords and not cellCoordsText and rowSpan>1 and columnSpan>1:
			# Translators: Speaks the row and column span added to the current row and column numbers
			#			(example output: through row 5 column 3).
			rowColSpanTranslation: str = _("through row {row} column {column}").format(
				row=rowNumber + rowSpan - 1,
				column=columnNumber + columnSpan - 1
			)
			textList.append(rowColSpanTranslation)
	rowCount=propertyValues.get('rowCount',0)
	columnCount=propertyValues.get('columnCount',0)
	if rowCount and columnCount:
		# Translators: Speaks number of columns and rows in a table (example output: with 3 rows and 2 columns).
		rowAndColCountTranslation: str = _("with {rowCount} rows and {columnCount} columns").format(
			rowCount=rowCount,
			columnCount=columnCount
		)
		textList.append(rowAndColCountTranslation)
	elif columnCount and not rowCount:
		# Translators: Speaks number of columns (example output: with 4 columns).
		columnCountTransation: str = _("with %s columns") % columnCount
		textList.append(columnCountTransation)
	elif rowCount and not columnCount:
		# Translators: Speaks number of rows (example output: with 2 rows).
		rowCountTranslation: str = _("with %s rows") % rowCount
		textList.append(rowCountTranslation)
	if rowCount or columnCount:
		# The caller is entering a table, so ensure that it is treated as a new table, even if the previous table was the same.
		oldTableID = None
	ariaCurrent = propertyValues.get('current', False)
	if ariaCurrent:
		try:
			ariaCurrentLabel = controlTypes.isCurrentLabels[ariaCurrent]
			textList.append(ariaCurrentLabel)
		except KeyError:
			log.debugWarning("Aria-current value not handled: %s"%ariaCurrent)
			ariaCurrentLabel = controlTypes.isCurrentLabels[True]
			textList.append(ariaCurrentLabel)
	placeholder: Optional[str] = propertyValues.get('placeholder', None)
	if placeholder:
		textList.append(transliterate(placeholder))
	indexInGroup=propertyValues.get('positionInfo_indexInGroup',0)
	similarItemsInGroup=propertyValues.get('positionInfo_similarItemsInGroup',0)
	if 0<indexInGroup<=similarItemsInGroup:
		# Translators: Spoken to indicate the position of an item in a group of items (such as a list).
		# {number} is replaced with the number of the item in the group.
		# {total} is replaced with the total number of items in the group.
		itemPosTranslation: str = _("{number} of {total}").format(
			number=indexInGroup,
			total=similarItemsInGroup
		)
		textList.append(itemPosTranslation)
	if 'positionInfo_level' in propertyValues:
		level=propertyValues.get('positionInfo_level',None)
		role=propertyValues.get('role',None)
		if level is not None:
			# Translators: Speaks the item level in treeviews (example output: level 2).
			levelTranslation: str = _('level %s') % level
			if role in (controlTypes.ROLE_TREEVIEWITEM,controlTypes.ROLE_LISTITEM) and level!=oldTreeLevel:
				textList.insert(0, levelTranslation)
				oldTreeLevel=level
			else:
				textList.append(levelTranslation)
	types.logBadSequenceTypes(textList)
	global _lastTranslatedText
	_lastTranslatedText = " ".join(e for e in textList)
	return textList

#
## End of NVDA sources/speech.py functions.
#

#
## Main global plugin class
#

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("Transliterate")
	language = None

	def __init__(self):
		"""Initializes the global plugin object."""
		super(globalPluginHandler.GlobalPlugin, self).__init__()
		global _nvdaGetPropertiesSpeech, _nvdaSpeak, _gpObject
		
		# if on a secure Desktop, disable the Add-on
		if globalVars.appArgs.secure: return
		_gpObject = self
		try:
			self.language = config.conf["general"]["language"]
		except:
			self.language = None
			pass
		if self.language is None or self.language == 'Windows':
			try:
				self.language = languageHandler.getWindowsLanguage()[:2]
			except:
				self.language = 'en'
				
		logHandler.log.info("Translate module initialized, translating to %s" %(self.language))

		_nvdaSpeak = speech._manager.speak
		_nvdaGetPropertiesSpeech = speech.getPropertiesSpeech
		speech._manager.speak = speak
		speech.getPropertiesSpeech = _nvdaGetPropertiesSpeech
		

	def terminate(self):
		"""Called when this plugin is terminated, restoring all NVDA's methods."""
		global _nvdaGetPropertiesSpeech, _nvdaSpeak
		speech._manager.speak = _nvdaSpeak
		speech.getPropertiesSpeech = _nvdaGetPropertiesSpeech


	def script_toggleTranslate(self, gesture):
		global _enableTransliteration
		
		_enableTranslation = not _enableTransliteration
		if _enableTranslation:
			ui.message(_("OE Transliteration enabled."))
		else:
			ui.message(_("OE Transliteration disabled."))

	script_toggleTranslate.__doc__ = _("Enables Old English transliteration.")

	__gestures = {
		"kb:nvda+shift+control+t": "toggleTranslate",
	}
