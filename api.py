# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Hangman API, contains the game logic ."""

import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    ScoreForms, GamesForm, GameHistoryForm, LeaderBoardForm
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm, urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))
GET_HIGH_SCORES = endpoints.ResourceContainer(number_of_results=messages.IntegerField(1))

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'

@endpoints.api(name='hangman', version='v1')
class HangmanApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        try:
            game = Game.new_game(user.key, request.length, request.attempts)
        except ValueError:
            raise endpoints.BadRequestException('Attempts must be between 3 and'
                                               '10 and length between 5 and 10')

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Hangman!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        # manage game_over and cancelled games
        if game.game_over:
            return game.to_form('Game already over!')
        if game.cancelled:
            return game.to_form('Game already cancelled!')

        guess = request.guess.lower()
        # manage ilegal movements
        if (len(guess) != 1) or (re.match('[a-z]', guess) is None):
            return game.to_form('Guess must be one letter!')
        if game.status_word.find(request.guess) > 0:
            return game.to_form('Already played.')
        if request.guess in game.status_fails:
            return game.to_form('Already failed.')

        # MAKE MOVE
        indexes = [i for i, c in enumerate(game.target) if c == guess]
        end = False
        # if char found in word
        if len(indexes) > 0:
            success = True
            # calculate new status_word
            newStatus = game.status_word
            for i in indexes:
                newStatus = newStatus[:i] + newStatus[i:].replace('*', guess, 1)
            game.status_word = newStatus
            # check if user has won
            if newStatus.find('*') < 0:
                end = True
                game.end_game(True)
                msg = 'You win!, word is: -{0}-.'.format(game.status_word)
            # otherwise return status_word
            else:
                msg = 'Good, -{0}- is in word: -{1}-.'.format(guess, game.status_word)
        # unless char found in word, manage attempt errors
        else:
            success = False
            game.status_fails.append(request.guess)
            game.attempts_remaining -= 1
            msg = 'Oh, oh, -{0}- not found.'.format(guess)
            # manage game over
            if game.attempts_remaining < 1:
                end = True
                msg = msg + ' GAME OVER! word was: {0}'.format(game.target)
        # insert move
        move = {'guess': guess,
                'success': success,
                'attempts_remaining': game.attempts_remaining,
                'result_status': game.status_word,
                'result_fails': game.status_fails}
        game.moves.append(move)
        # return result
        if end:
            game.end_game(success)
            return game.to_form(msg)
        game.put()
        return game.to_form(msg)

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(message=memcache.get(MEMCACHE_MOVES_REMAINING) or '')

### NEW API ENDPOINTS ###
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GamesForm,
                      path='user/{user_name}/games',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """ This returns all of a User's active games. """
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        games = Game.query(Game.user == user.key,
                           Game.game_over == False,
                           Game.cancelled == False)
        return GamesForm(items=[game.to_form() for game in games])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}/cancel',
                      name='cancel_game',
                      http_method='PUT')
    def cancel_game(self, request):
        """ Cancel a game in progress. """
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            msg = 'Game already over!'
        elif game.cancelled:
            msg = 'Game already cancelled!'
        else:
            msg = 'Game cancelled!'
            game.cancelled = True
            game.put()
        return game.to_form(msg)

    @endpoints.method(request_message=GET_HIGH_SCORES,
                      response_message=ScoreForms,
                      path='scores/high_scores',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """ Generates a lists of high scores in descending order. """
        scores = Score.query().order(Score.errors, -Score.length).fetch(request.number_of_results)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=LeaderBoardForm,
                      path='scores/rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """ This returns all players ranked by performance """
        users = User.query().order(-User.score)
        return LeaderBoardForm(items=[user.to_rank_form() for user in users])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameHistoryForm,
                      path='game/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """ This returns the history of the game """
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        return GameHistoryForm(urlsafe_game_key=request.urlsafe_game_key,
                               game_cancelled=game.cancelled,
                               game_over=game.game_over,
                               moves=game.moves)

    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves remaining of Games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_attempts_remaining = sum([game.attempts_remaining
                                        for game in games])
            average = float(total_attempts_remaining)/count
            memcache.set(MEMCACHE_MOVES_REMAINING,
                         'The average moves remaining is {:.2f}'.format(average))


api = endpoints.api_server([HangmanApi])
