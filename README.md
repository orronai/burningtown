# Burning Town Telegram-Bot Game

Welcome to Burning Town game with telegram bot

## Creating development environment
Steps to do:
1. Clone this repository.
2. Message in the telegram @BotFather in order to create a telegram bot and get an access token.
3. Add the bot to a telegram "supergroup".
4. Put your access token in the file: `application/bot.py`.
5. Run the application.

### Setup
```bash
git clone https://github.com/orronai/burningtown
cd burningtown

python app.py
```

### Starting a game
1. Type in the "supergroup" chat - !game.
2. In order to join the game - players need to send the bot one-time message.
3. type !join in order to join the game.
4. When there are enough players (default is 4 players), type !start

Enjoy!
