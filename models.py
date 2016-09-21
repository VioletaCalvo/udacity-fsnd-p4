"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb
from game import get_target
from utils import get_by_urlsafe

DEFAULT_WORD_LENGTH = 7
DEFAULT_ATTEMPT_ERRORS = 5
ATTEMPTS_MIN = 3
ATTEMPTS_MAX = 10
LENGTH_MIN = 5
LENGTH_MAX = 10

def get_score(self):
    """ Calculate user score """
    score = 0
    if self.total_games > 0:
        score = int(round(100 * self.wins / self.total_games))
    return score

class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    wins = ndb.IntegerProperty(required=True, default=0)
    total_games = ndb.IntegerProperty(required=True, default=0)
    score = ndb.ComputedProperty(get_score)

    def to_rank_form(self):
        """Returns a UserRankForm representation of the User"""
        form = UserRankForm()
        form.user_name = self.name
        form.score = self.score
        return form

class Game(ndb.Model):
    """Game object"""
    target = ndb.StringProperty(required=True)
    status_word = ndb.StringProperty(required=True)
    status_fails = ndb.StringProperty(repeated=True)
    attempts_allowed = ndb.IntegerProperty(required=True)
    attempts_remaining = ndb.IntegerProperty(required=True, default=DEFAULT_ATTEMPT_ERRORS)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    cancelled = ndb.BooleanProperty(required=True, default=False)
    moves = ndb.JsonProperty(repeated=True)

    @classmethod
    def new_game(cls, user, length, attempts):
        """Creates and returns a new game"""
        if (attempts < ATTEMPTS_MIN) or (attempts > ATTEMPTS_MAX):
            raise ValueError('Attempts value error!')
        elif (length < LENGTH_MIN) or (length > LENGTH_MAX):
            raise ValueError('Length value error!')
        game = Game(user=user,
                    target=get_target(length),
                    status_word='*'*length,
                    status_fails=[],
                    attempts_allowed=attempts,
                    attempts_remaining=attempts,
                    game_over=False,
                    cancelled=False,
                    moves=[])
        game.put()
        # Update user total_games
        # we count also cancelled games for total_games
        user = user.get()
        user.total_games += 1
        user.put()
        return game

    def to_form(self, *args):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.attempts_remaining = self.attempts_remaining
        form.game_over = self.game_over
        form.cancelled = self.cancelled
        if args:
            form.message = args[0]
        form.status_word = self.status_word
        form.status_fails = self.status_fails
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), won=won,
                      errors=self.attempts_allowed - self.attempts_remaining,
                      length=len(self.target))
        score.put()
        # Update user score
        user = self.user.get()
        if won:
            user.wins += 1
        user.put()

class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    errors = ndb.IntegerProperty(required=True)
    length = ndb.IntegerProperty(required=True)

    def to_form(self):
        """ Score form """
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), errors=self.errors,
                         length=self.length)

class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    attempts_remaining = messages.IntegerField(2, required=True)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4)
    user_name = messages.StringField(5, required=True)
    status_word = messages.StringField(6, required=True)
    status_fails = messages.StringField(7, repeated=True)
    cancelled = messages.BooleanField(8, required=True)

class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    length = messages.IntegerField(2, default=DEFAULT_WORD_LENGTH)
    attempts = messages.IntegerField(3, default=DEFAULT_ATTEMPT_ERRORS)

class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess = messages.StringField(1, required=True)

# New move form (used for game history form)
class MoveForm(messages.Message):
    """ MoveForm from outbound GameHIstory information"""
    guess = messages.StringField(1, required=True)
    success = messages.BooleanField(2, required=True)
    attempts_remaining = messages.IntegerField(3, required=True)
    result_status = messages.StringField(4, required=True)
    result_fails = messages.StringField(5, repeated=True)

# New game history form
class GameHistoryForm(messages.Message):
    """ Used to return the game history """
    urlsafe_game_key = messages.StringField(1, required=True)
    game_over = messages.BooleanField(2, required=True)
    game_cancelled = messages.BooleanField(3, required=True)
    moves = messages.MessageField(MoveForm, 4, repeated=True)

# New Games User Form
class GamesForm(messages.Message):
    """ Used to return the active games for a user"""
    items = messages.MessageField(GameForm, 1, repeated=True)

class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    errors = messages.IntegerField(4, required=True)
    length = messages.IntegerField(5, required=True)

class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)

# New LeaderBoard
class UserRankForm(messages.Message):
    """ LeaderBoard for outbound ranking information"""
    user_name = messages.StringField(1, required=True)
    score = messages.IntegerField(2, required=True)

# New RankingForms
class LeaderBoardForm(messages.Message):
    """Return multiple UserRankForm"""
    items = messages.MessageField(UserRankForm, 1, repeated=True)

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
