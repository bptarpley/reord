# *-* coding: utf-8 *-*
# transliterate/__init__.py
#Much of this code adopted from the NVDA Translate add-on:
#Copyright (C) 2018 Yannick PLASSIARD
#This file is covered by the GNU General Public License.
#See the file LICENSE for more details.


import os, sys, time, codecs, re
import globalVars
import globalPluginHandler, logHandler, scriptHandler
from string import punctuation

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
_nvdaSpeakSpelling = None
_nvdaGetSpellingSpeech = None
_gpObject = None
_lastError = 0
_enableTransliteration = False
_lastTranslatedText = None
_lastTranslatedTextTime = 0
_transliterations = {}


def _contains(obj, items):
	items_in_obj = False
	for item in items:
		if item in obj:
			items_in_obj = True
			break
	return items_in_obj


def find_all(a_str, sub):
	start = 0
	while True:
		start = a_str.find(sub, start)
		if start == -1: return
		yield start
		start += len(sub)


def medial_indexes(word, sub):
	sub_indexes = list(find_all(word, sub))
	return [i for i in sub_indexes if i in list(range(1, len(word) - 1))]


def is_oe_word(word):
	probability = 0
	oe_vowels = ["a", "ā", "æ", "ǣ", "e", "ē", "i", "ī", "o", "ō", "u", "ū", "y", "ȳ"]
	oe_consonants = ["b", "c", "ċ", "d", "f", "g", "ġ", "h", "k", "l", "m", "n", "p", "r", "s", "t", "þ", "ð", "w", "x", "z"]

	# DEFINITELY OE RULES:
	if _contains(word, ["ā", "æ", "ǣ", "ē", "ī", "ō", "ȳ", "Ā", "Æ", "Ǣ", "Ē", "Ī", "Ō", "Ū", "Ȳ", "ċ", "ġ", "þ", "ð", "Ċ", "Ġ", "Þ", "Ð"]) or \
			"cg" in word or \
			word[0:2] in ["hl", "hr", "hw", "eo"] or \
			(word[-2:] in ["eo"] and word != "stereo"):
		return True

	for medial_index in medial_indexes(word, 'x'):
		if word[medial_index - 1] in oe_consonants:
			return True

	for medial_index in medial_indexes(word, 'h'):
		if word[medial_index - 1] in oe_vowels and word[medial_index + 1] in oe_consonants:
			return True

	if word.endswith('h') and len(word) > 1 and word[-2] not in ["c", "g", "p", "s", "t"]:
		return True

	# DEFINITELY ModE RULES:
	if _contains(word, ['j', 'q', "'"]):
		return False

	elif _contains(['ch', 'ph', 'sh', 'th'], [word[0:2], word[-2:]]):
		return False

	if 'gh' in word:
		gh_indexes = list(find_all(word, 'gh'))
		for gh_index in gh_indexes:
			if gh_index < len(word) - 2 and word[gh_index + 2] not in ['a', 'e', 'i', 'o', 'u', 'l', 'r', 'w']:
				return False

	# PROBABLY OE RULES:
	if _contains(word, ["hl", "hr", "hw"]):
		for pair in ["hl", "hr", "hw"]:
			if medial_indexes(word, pair):
				probability += 60

	if medial_indexes(word, 'eo'):
		probability += 60

	if word[-2:] in ['ic', 'ig']:
		probability += 60

	if len(word) > 1 and word.endswith('u') and word[-2] in oe_consonants:
		probability += 60

	if len(word) > 2 and word.endswith('ne') and word[-3] in oe_consonants:
		probability += 60

	if len(word) > 4 and word.endswith('um') and word[-3] in oe_consonants:
		probability += 60

	if 'ng' in word:
		ng_indexes = list(find_all(word, 'ng'))
		for ng_index in ng_indexes:
			if ng_index < len(word) - 2 and word[ng_index + 2] in oe_vowels:
				probability += 60

	if 'sc' in word:
		sc_indexes = list(find_all(word, 'sc'))
		for sc_index in sc_indexes:
			if sc_index < len(word) - 2 and word[sc_index + 2] in oe_vowels:
				probability += 60

	# PROBABLY ModE RULES:
	if _contains(word, ['k', 'z']):
		probability -= 60

	return probability > 50


def separate_prefix(word):
	prefixes = ["ā", "æt", "be", "bi", "for", "ge", "ġe", "of", "on", "oð", "oþ", "tō"]
	# Did not include geond, ofer, under, wið, wiþ, ymb, and 1 or 2 others likely to create as many
	# false positives as correct identifications for purposes of assigning word stress.

	exceptions = ["ācs", "āct", "ādl", "āfor", "āgan", "āgen", "āgon", "āht", "āhw", "ān",
		"ætr", "ætt",
		"bea", "bedd", "bedef", "bedre", "belt", "benc", "benċ", "bend", "benn", "beo", "bera", "bere",
		"bers", "betl", "betr", "bets",
		"bicg", "bidd", "biel", "bifi", "bifod", "bilew", "bill", "bilw", "bind", "binn", "bire",
		"bisc", "bisg", "bism",
		"fora", "ford", "forht", "forhw", "form", "foro", "forðb", "forðf", "forðg", "forðġ", "forðw",
		"forðȳ", "forþb", "forþf", "forþg", "forþġ", "forþw", "forþȳ", "forwyrd",
		"gea", "ġea", "geār", "ġeār", "gegn", "ġegn", "geo", "ġeo", "geō", "ġeō",
		"ofer", "off", "ofo", "ofstl",
		"onds", "onemn", "ongel", "onġel" "ongem", "onġem", "onsȳn",
		"oððo", "oððe", "oþþo", "oþþe", "oðþo", "oðþe", "oþðo", "oþðe",
		"tōcym", "tōdāl", "tōð", "tōþ", "tōweard"]

	# "for" is going to produce a few more false results than the others because I can't
	# separate it from "ford(-)", "fore(-)", "forst(-)" without
	# excluding too many legitimate for- instances. "of" will create some problems because
	# it will try to segment "ofst." "ofer" has to be among exclusions to prevent
	# every instance of the preposition being treated as "of- ER", but this also means that
	# every instance of the prefix "ofer-" will go unidentified (about a 50% error for ofer-,
	# in terms of stress assignment, but less disruptive than capturing them all with "of-").
	# For "on," "onga" will be a problem. For "tō", "tōl" will be.
	# I don't know how to account for double-prefixation (like tōætȳcan, tōġeþēodan). Rare but occurs.

	# Many of the above can be fixed by starting with len(word) > 4, as I've done now. Was 3. What's lost?

	word_prefix_detached = None

	if len(word) > 4:
		if word[:1] in prefixes and word[:2] not in exceptions and word[:3] not in exceptions and word[:4] not in exceptions and word[:5] not in exceptions:
			word_prefix_detached = word.replace(word[:1], word[:1] + " ")
		elif word[:2] in prefixes and word[:3] not in exceptions and word[:4] not in exceptions and word[:5] not in exceptions and word[:6] and word[:7] not in exceptions:
			word_prefix_detached = word.replace(word[:2], word[:2] + " ")
		elif word[:3] in prefixes and word[:4] not in exceptions and word[:5] not in exceptions and word[:6] not in exceptions and word[:7] not in exceptions:
			word_prefix_detached = word.replace(word[:3], word[:3] + " ")

	if word_prefix_detached:
		word = word_prefix_detached

	return word


def syllabify_word(word):
	vowels = ["a", "ā", "æ", "ǣ", "e", "ē", "i", "ī",
		"o", "ō", "u", "ū", "y", "ȳ",
		"ea", "ēa", "eo", "ēo", "ie", "īe",
		"A", "Ā", "Æ", "Ǣ", "E", "Ē", "I", "Ī",
		"O", "Ō", "U", "Ū", "Y", "Ȳ",
		"Ea", "Ēa", "Eo", "Ēo", "Ie", "Īe"]
	consonants = ["b", "c", "ċ", "d", "f", "g", "ġ",
		"h", "k", "l", "m", "n", "p", "r",
		"s", "t", "þ", "ð", "w", "x", "z",
		"cg", "ng", "sc",
		"B", "C", "Ċ", "D", "F", "G", "Ġ",
		"H", "K", "L", "M", "N", "P", "R",
		"S", "T", "Þ", "Ð", "W", "X", "Z",
		"Sc"]

	syllables_of_word = []
	cursor = len(word) - 1
	syllable_end_marker = len(word)

	while cursor > -1:

		syllable_start_marker = None

		if cursor == 0:  # This block catches 1- and 2-letter words & makes sure 0 is always syllable start.
			syllable_start_marker = cursor  # adjustment + 1
		elif cursor == 1 and len(word) == 2:  # combined 2 if statements
			cursor = 0
			syllable_start_marker = cursor  # adjustment + 1

		elif word[cursor] in vowels:  # This block moves cursor to start of diphthongs and digraphs.
			if word[cursor - 1:cursor + 1] in vowels:
				cursor -= 1
		elif word[cursor] in consonants:
			if word[cursor - 1:cursor + 1] in consonants:
				cursor -= 1

		if word[cursor] in vowels:
			if word[cursor - 1] in vowels:
				syllable_start_marker = cursor  # adjustment + 1
			elif word[cursor - 1] in consonants:
				if cursor > 3:
					if word[cursor - 2:cursor] in consonants:
						cursor -= 2
					else:
						cursor -= 1
					syllable_start_marker = cursor  # adjustment + 1
				elif cursor == 3:  # changed if to elif
					if word[cursor - 2:cursor] in consonants:
						cursor -= 2
					elif word[1] in consonants and word[0] in consonants:
						cursor = 0
					else:
						cursor -= 1
					syllable_start_marker = cursor  # adjustment + 1

		elif word[cursor] in consonants:  # changed elif to if
			if cursor == 2:
				if word[1] and word[0] in consonants:
					cursor = 0
				elif word[1] in vowels:
					if word[0] in consonants:
						cursor = 0
					elif word[0:2] in vowels:
						cursor = 0
				syllable_start_marker = cursor  # adjustment + 1
			if cursor == 1:
				if word[0] in consonants:
					cursor = 0
					syllable_start_marker = cursor  # adjustment + 1
				if word[0] and word[2] in vowels:
					syllable_start_marker = cursor  # adjustment + 1

		if syllable_start_marker is not None:
			syllable_of_word = word[syllable_start_marker:syllable_end_marker]  # adjustment - 1
			syllables_of_word.append(syllable_of_word)
			if syllable_start_marker > 0:  # adjustment 1
				syllable_end_marker = syllable_start_marker  # adjustment - 1

		cursor -= 1

	syllables_of_word.reverse()
	return syllables_of_word


def transliterate(text):
	"""transliterates Old English text
	"""
	global _enableTransliteration, _transliterations

	try:
		appName = globalVars.focusObject.appModule.appName
	except:
		appName = "__global__"

	debug_log = None
	if 'debug_transliterations' in _transliterations:
		debug_log = "Transliteration debug info: "

	try:
		new_text = ""
		oe_text = text.lower()

		# going to try to keep a list of tuples where
		# first item is a "clause" (any text preceding punctuation)
		# and second item is the punctuation following the clause.
		# the idea is to transliterate these clauses and then stitch
		# them back together using original punctuation.
		clause_tuples = []

		# building list of punctuation marks
		punct_list = list(punctuation)
		punct_list.extend(["“", "”"])

		starting_clause_index = 0
		for char_cursor in range(0, len(oe_text)):
			if oe_text[char_cursor] in punct_list:
				clause_tuples.append(
					(
						oe_text[starting_clause_index:char_cursor],
						oe_text[char_cursor]
					)
				)
				starting_clause_index = char_cursor + 1
			elif char_cursor == len(oe_text) - 1:
				clause_tuples.append(
					(
						oe_text[starting_clause_index:],
						""
					)
				)

		for clause_tuple in clause_tuples:
			oe_clause = clause_tuple[0]
			oe_punct = clause_tuple[1]
			oe_words = [oe_word for oe_word in oe_clause.split() if oe_word]

			for oe_word in oe_words:
				if debug_log:
					debug_log += " " + oe_word + "["

				if is_oe_word(oe_word):
					if debug_log:
						debug_log += "Y "

					syllables = []

					oe_word = separate_prefix(oe_word)
					if debug_log:
						debug_log += oe_word + " ("

					if ' ' in oe_word:
						subwords = [subword for subword in oe_word.split() if subword]
						for subword in subwords:
							syllables.extend(syllabify_word(subword))
					else:
						syllables = syllabify_word(oe_word)

					transliterated_word = ""
					for syllable in syllables:
						if syllable in _transliterations:
							transliterated_word += _transliterations[syllable]
						else:
							transliterated_word += syllable

						if not transliterated_word.endswith('-'):
							transliterated_word += "-"

					if transliterated_word.endswith('-'):
						transliterated_word = transliterated_word[:-1]

					if debug_log:
						debug_log += transliterated_word + ")]"
					new_text += transliterated_word + " "
				else:
					if debug_log:
						debug_log += "N]"
					new_text += oe_word + " "

			if debug_log:
				debug_log += oe_punct
			new_text = new_text.strip() + oe_punct + " "

		text = new_text.strip()
	except Exception as e:
		if debug_log:
			logHandler.log.info("An error occurred while attempting to transliterate, so original text was spoken. Original text: " + text + " [OE DEBUG LOG]: " + debug_log)
		return text

	if debug_log:
		logHandler.log.info("[OE DEBUG LOG]: " + debug_log)
	return text


#
## Extracted and adapted from nvda/sources/speech/__init__.py
#
def speak(speechSequence: SpeechSequence,
					priority: Optional[Spri] = None):
	global _enableTransliteration

	if _enableTransliteration is False:
		return _nvdaSpeak(speechSequence=speechSequence, priority=priority)
	newSpeechSequence = []
	for val in speechSequence:
		if isinstance(val, str):
			v = transliterate(val)
			newSpeechSequence.append(v if v is not None else val)
		else:
			newSpeechSequence.append(val)
	_nvdaSpeak(speechSequence=newSpeechSequence, priority=priority)


# Overriding this guy too to prevent transliteration while spelling!
def speakSpelling(
		text: str,
		locale: Optional[str] = None,
		useCharacterDescriptions: bool = False,
		priority: Optional[Spri] = None
) -> None:
	global _enableTransliteration, _nvdaGetSpellingSpeech, _nvdaSpeak
	do_toggling = _enableTransliteration

	if do_toggling:
		_enableTransliteration = False

	# This could be a very large list. In future we could convert this into chunks.
	seq = list(_nvdaGetSpellingSpeech(
		text,
		locale=locale,
		useCharacterDescriptions=useCharacterDescriptions
	))

	_nvdaSpeak(speechSequence=seq, priority=priority)

	if do_toggling:
		_enableTransliteration = True

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
		global _nvdaSpeak, _nvdaSpeakSpelling, _nvdaGetSpellingSpeech, _transliterations, _gpObject
		
		# if on a secure Desktop, disable the Add-on
		if globalVars.appArgs.secure: return
		_gpObject = self

		_nvdaSpeak = speech._manager.speak
		_nvdaSpeakSpelling = speech.speakSpelling
		_nvdaGetSpellingSpeech = speech.getSpellingSpeech
		speech._manager.speak = speak
		speech.speakSpelling = speakSpelling

		transliterations_file = os.path.join(os.path.dirname(__file__), "transliterations.json")
		if os.path.exists(transliterations_file):
			with open(transliterations_file, 'r', encoding='utf-8') as trans_in:
				_transliterations = json.load(trans_in)

		user_transliterations_file = "{0}/old_english_transliterations.txt".format(os.path.expanduser('~'))
		if os.path.exists(user_transliterations_file):
			with open(user_transliterations_file, 'r', encoding='utf-8') as trans_in:
				user_transliterations = trans_in.readlines()
				for user_transliteration in user_transliterations:
					syllable_transliteration = user_transliteration.split()
					if len(syllable_transliteration) == 2:
						_transliterations[syllable_transliteration[0].lower()] = syllable_transliteration[1].lower()

		logHandler.log.info("Old English Transliteration add-on enabled.")
		

	def terminate(self):
		"""Called when this plugin is terminated, restoring all NVDA's methods."""
		global _nvdaSpeak, _nvdaSpeakSpelling
		speech._manager.speak = _nvdaSpeak
		speech.speakSpelling = _nvdaSpeakSpelling
		speech.getSpellingSpeech = _nvdaGetSpellingSpeech


	def script_toggleTranslate(self, gesture):
		global _enableTransliteration
		
		_enableTransliteration = not _enableTransliteration
		if _enableTransliteration:
			ui.message(_("Old English Transliteration enabled."))
		else:
			ui.message(_("Old English Transliteration disabled."))

	script_toggleTranslate.__doc__ = _("Enables Old English transliteration.")

	__gestures = {
		"kb:nvda+shift+control+t": "toggleTranslate",
	}
