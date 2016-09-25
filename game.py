# -*- coding: utf-8 -*-`
"""game.py - Generate target word from wordnik API."""

from wordnik import swagger, WordsApi

WORDNIK_API_URL = 'http://api.wordnik.com/v4'
WORDNIK_KEY = 'your-wordnik-api-key'
client = swagger.ApiClient(WORDNIK_KEY, WORDNIK_API_URL)
wordApi = WordsApi.WordsApi(client)

def get_target(length):
    """ Retuns the word for the game """
    isValid = False
    # get a word from Wordnik API
    # avoid to return a non-valid word (with non alpha characters)
    while not isValid:
        word = wordApi.getRandomWord(
            hasDictionaryDef=True,
            includePartOfSpeech='noun',
            minCorpusCount=0,
            maxCorpusCount=-1,
            minDictionaryCount=1,
            maxDictionaryCount=-1,
            minLength=length,
            maxLength=length
            )
        isValid = word.word.isalpha()
    print '-------------------------'
    print word.word.lower()
    print '-------------------------'
    return word.word.lower()
