# nvda-transliterate-oe

## About

This is an add-on for the [NVDA Screen Reader](https://www.nvaccess.org/download/) intended to serve as a learning aid for those who would wish to hear the pronunciation of Old English words. The add-on was developed as the outcome of a [Summer Technical Assistance Grant](http://codhr.dh.tamu.edu/summer-digital-humanities-technical-assistance-grants/) provided by the Center of Digital Humanities Research (CoDHR) at Texas A&M University. Much of the code (particularly as it concerned the add-on) was written by Dr. Bryan Tarpley (Software Developer III at CoDHR). Algorithms for detecting whether a word is Old English, separating prefixes for such words, and breaking such words into discrete syllables were developed by Dr. Britt Mize (Associate Professor of English). All syllables were painstakingly transliterated by Rebecca Baumgarten (Graduate Assistant Researcher in English).

Due to time constraints, it was determined that developing a full-fledged language module for NVDA was outside the scope of the project. As such, the approach of this add-on is to take all text fed through the NVDA Screen Reader, determine whether any of the words in that text are Old English words, and if so, to separate prefixes, syllabify, and then transliterate the syllables for a given word such that NVDA might more accurately pronounce the word. Given this approach, for instance, upon encountering the word "swylċe," NVDA will pronounce "swuil-cheh."

##Installation

At present, the NVDA Screen Reader is only available for the Windows operating system. Upon installing NVDA, a user can then download [this packaged add-on file](https://github.com/bptarpley/nvda-transliterate-oe/raw/master/transliterate-oe-2020.00.nvda-addon). Once downloaded, most of the time a user can double-click on the file, prompting NVDA to ask whether to trust and install the add-on. Occasionally, however, the .nvda-addon file extension is not associated with NVDA. If this is the case, the user can manually install the add-on by bringing up the NVDA menu (assuming the default "NVDA key" is the Insert key, you can bring it up by pressing Insert+n), going to Tools->Manage Add-ons->Install and choosing the downloaded file.

Once the add-on installs, NVDA will ask to restart itself. Upon restarting, the add-on can be enabled by pressing Insert+Cntrl+Shift+t (you should hear the phrase "Old English Transliteration Enabled"). 

##Customization

The transliterations of specific Old English Syllables can be customized

This repo is a fork of https://github.com/yplassiard/nvda-translate. Instead of translating spoken text, however, it attempts to recognize whether a word is an Old English word, and if it is, it tells NVDA to pronounce a transliterated version of the word in order to make it sound more like the Old English pronunciation.
