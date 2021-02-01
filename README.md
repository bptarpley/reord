# Reord

## About

This is an add-on for the [NVDA Screen Reader](https://www.nvaccess.org/download/) intended to serve as a learning aid for those who would wish to hear the pronunciation of Old English words. The add-on was developed as the outcome of a [Summer Technical Assistance Grant](http://codhr.dh.tamu.edu/summer-digital-humanities-technical-assistance-grants/) provided by the Center of Digital Humanities Research (CoDHR) at Texas A&M University. Much of the code (particularly as it concerned the add-on) was written by Dr. Bryan Tarpley (Software Developer III at CoDHR). Algorithms for detecting whether a word is Old English, separating prefixes for such words, and breaking such words into discrete syllables were developed by Dr. Britt Mize. All syllables were painstakingly transliterated by Rebecca Baumgarten (graduate student in English).

Due to time constraints, it was determined that developing a full-fledged language module for NVDA was outside the scope of the project. As such, the approach of this add-on is to take all text fed through the NVDA Screen Reader, determine whether any of the words in that text are Old English words, and if so, to separate prefixes, syllabify, and then transliterate the syllables for a given word such that NVDA might more accurately pronounce the word. Given this approach, for instance, upon encountering the word "swylċe," NVDA will pronounce "swuil-cheh."

## Installation

At present, the NVDA Screen Reader is only available for the Windows operating system. Upon installing NVDA, a user can then download [this packaged add-on file](https://github.com/bptarpley/reord/raw/master/transliterate-oe-2020.00.nvda-addon). Once downloaded, most of the time a user can double-click on the file, prompting NVDA to ask whether to trust and install the add-on. Occasionally, however, the .nvda-addon file extension is not associated with NVDA. If this is the case, the user can manually install the add-on by bringing up the NVDA menu (assuming the default "NVDA key" is the Insert key, you can bring it up by pressing Insert+n), going to Tools->Manage Add-ons->Install and choosing the downloaded file.

## Using the Add-On

Once the add-on is installed, NVDA will ask to restart itself. Upon restarting, the add-on can be enabled by pressing Insert+Cntrl+Shift+t (you should hear the phrase "Old English Transliteration Enabled"). At that point, the user can simply use the screen reader as normal--only words detected to be Old English words will be transliterated and pronounced differently.

## Customization

The transliterations of specific Old English Syllables can be customized. To do this, create a file called "old_english_transliterations.txt" in the Windows user directory. For instance, if your Windows username is "sally," then you'd create this file at C:\Users\sally\old_english_transliterations.txt.

In this file, you can put a syllable and its transliteration, separated by a space, on its own line in the file. So, for instance, if instead of pronouncing the Old English word "swylċe" as "swuil-cheh," you could have the following two lines in the old_english_transliterations.txt file:

```
swyl sole
ċe chair
```

Once you've edited the old_english_transliterations.txt file accordingly and restarted NVDA, the screen reader would then pronounce "swylċe" as "sole-chair."

You can have as many lines (syllable + transliteration pairs) in the file as you'd like, though you must restart NVDA for them to take effect.

## Technical Details

This repo is a fork of https://github.com/yplassiard/nvda-translate, an add-on developed by Yannick Plassiard for speaking translated versions of text. We chose to fork the above repository since it was doing similar things to what we intended, and while we have done our best to understand how NVDA add-ons work, we appreciated not having to start from scratch.

The algorithms (written in Python) for detecting whether a word is an Old English word, for separating prefixes, and for syllabifying can all be found in [this file](https://github.com/bptarpley/reord/blob/master/addon/globalPlugins/transliterate/__init__.py), and could easily be adapted for other purposes.

The default transliterations of syllables can be found in [this file](https://github.com/bptarpley/reord/blob/master/addon/globalPlugins/transliterate/transliterations.json) (stored in JSON format).


