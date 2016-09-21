# Hangman game API

## Game Description:
Hangman is a game for one player. The player tries to guess a word by suggesting letters, within a certain number of guesses (length of the word plus error attempts is the maximum). Length of the word and error attempts can be defined by the client. Length of the word must be between 5 and 10. Error attempts also must be between 3 and 10

'Letters' are sent to the `make_move` endpoint which will reply
with an object result:

    urlsafe_key: String
    attempts_remaining: Integer
    message: String
    user_name: String
    status_word: String
    status_fails: Array of String, array of fails
    game_over: Boolean
    cancelled: Boolean

Many different Hangman games can be played by many different Users at any
given time. Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.

Scores are saved when a game ends saving the number of errors and the length of the word

User score and users ranking are calculated by the percentage of wins of total games (including cancelled games)

## Files Included:
 * api.py: Contains endpoints and game playing logic.
 * app.yaml: App configuration.
 * cron.yaml: Cronjob configuration.
 * main.py: Handler for taskqueue handler.
 * models.py: Entity and message definitions including helper methods.
 * utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.
 * game.py: Helper function for setup the game. Uses the Wordnik API.
 * appengine_config.py: used to make wordnik module available.
 * Design.txt: details the design decisions.

## Endpoints Included:
 * **create_user**
    * Path: 'user'
    * Method: POST
    * Parameters: user_name, email (optional)
    * Returns: Message confirming creation of the User.
    * Description: Creates a new User. user_name provided must be unique. Will
    raise a ConflictException if a User with that user_name already exists.

 * **new_game**
    * Path: 'game'
    * Method: POST
    * Parameters: user_name, min, max, attempts
    * Returns: GameForm with initial game state.
    * Description: Creates a new Game. user_name provided must correspond to an
    existing user -will raise a NotFoundException if not. Min must be less than
    max. Also adds a task to a task queue to update the average moves remaining
    for active games.

 * **get_game**
    * Path: 'game/{urlsafe_game_key}'
    * Method: GET
    * Parameters: urlsafe_game_key
    * Returns: GameForm with current game state.
    * Description: Returns the current state of a game.

 * **make_move**
    * Path: 'game/{urlsafe_game_key}'
    * Method: PUT
    * Parameters: urlsafe_game_key, guess
    * Returns: GameForm with new game state.
    * Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.

 * **get_scores**
    * Path: 'scores'
    * Method: GET
    * Parameters: None
    * Returns: ScoreForms.
    * Description: Returns all Scores in the database (unordered).

 * **get_user_scores**
    * Path: 'scores/user/{user_name}'
    * Method: GET
    * Parameters: user_name
    * Returns: ScoreForms.
    * Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.

 * **get_active_game_count**
    * Path: 'games/active'
    * Method: GET
    * Parameters: None
    * Returns: StringMessage
    * Description: Gets the average number of attempts remaining for all games
    from a previously cached memcache key.

 * **get_user_games** _(new)_ :star2:
    * Path: 'user/{user_name}/games'
    * Method: GET
    * Parameters: user_name
    * Returns: GamesForm
    * Description: Returns all of a User's games.

 * **cancel_game** _(new)_ :star2:
    * Path: 'game/{urlsafe_game_key}/cancel'
    * Method: POST
    * Parameters: urlsafe_game_key
    * Returns: GameForm
    * Description: This endpoint allows users to cancel a game in progress.

 * **get_high_scores** _(new)_ :star2:
    * Path: 'scores/high_scores'
    * Method: GET
    * Parameters: None
    * Returns: ScoreForms
    * Description: Generates a list of high scores in descending order.

 * **get_user_rankings** _(new)_ :star2:
    * Path: 'scores/ranking'
    * Method: GET
    * Parameters: None
    * Returns: LeaderBoardForm
    * Description: returns all players ranked by performance.

 * **get_game_history** _(new)_ :star2:
    * Path: 'game/{urlsafe_game_key}/history'
    * Method: GET
    * Parameters: urlsafe_game_key
    * Returns: GameHistoryForm
    * Description: returns the game history.


## Models Included:
 * **User**
    * Stores unique user_name and (optional) email address.
 * **Game**
    * Stores unique game states. Associated with User model via KeyProperty.
 * **Score**
    * Records completed games. Associated with Users model via KeyProperty.


## Forms Included:
 * **GameForm**
    * Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, message, user_name).
 * **NewGameForm**
    * Used to create a new game (user_name, min, max, attempts)
 * **MakeMoveForm**
    * Inbound make move form (guess).
 * **ScoreForm**
    * Representation of a completed game's Score (user_name, date, won flag,
    guesses).
 * **ScoreForms**
    * Multiple ScoreForm container.
 * **StringMessage**
    * General purpose String container.
 * **GameHistoryForm** _(new)_ :star2:
    * Representation of the game history.
 * **MoveForm** _(new)_ :star2:
    * Representation of a move
 * **GamesForm** _(new)_ :star2:
    * Multiple GameForm container.
 * **LeaderBoardForm** _(new)_ :star2:
    * Multiple RankingForm container
 * **UserRankForm** _(new)_ :star2:
    * Used to return a ranking item


## Configuration and Running

### Configuration
Create a `lib` folder and install the wordnik package on it.
```shell
mkdir lib
cd lib
pip install -t lib wordnik
```

Configure your wordnik API key in `game.py`
```python
WORDNIK_KEY = 'your-wordnik-api-key'
```

Configure your google app ID in `app.yaml`
```yaml
application: your-google-app-id
```

### Run
```shell
# run on localhost
dev_appserver.py app.yaml

# upload to appengine
appcfg.py update app.yaml
  ```

A live version of this API is running [here](https://udacityp4violeta.appspot.com/)
