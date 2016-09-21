# -*- coding: utf-8 -*-`
"""game.py - Generate target word from wordnik API."""

import wordnik
from wordnik import swagger, WordsApi

WORDNIK_API_URL = 'http://api.wordnik.com/v4'
WORDNIK_KEY = 'your-wordnik-api-key'
client = swagger.ApiClient(WORDNIK_KEY, WORDNIK_API_URL)
wordApi = WordsApi.WordsApi(client)

def get_target(length):
    """ Retuns the word for the game """
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
    print word
    return word.word
