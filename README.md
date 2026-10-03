# Discord Suggestions Bot

A community-focused Discord bot for collecting, discussing, voting on, and managing server suggestions.

## ✨ Features

- 💡 Submit suggestions directly in Discord
- 👍👎 Community voting
- 💬 Suggestion discussion threads
- 🛡️ Admin approval and rejection workflows
- 📚 Suggestion history and search
- 🏆 Popular/top suggestions
- 📊 Server suggestion statistics
- 🗂️ Suggestion categories
- ⏱️ Per-user rate limiting
- 📝 Configurable suggestion limits

## 🧰 Requirements

- Python 3.x
- Discord bot token
- MongoDB
- A Discord application with the required bot permissions

> Check the repository dependencies and configuration files before deployment; the project may evolve beyond the original setup documented here.

## 🚀 Installation

```bash
git clone https://github.com/feloony/Suggestions-Bot.git
cd Suggestions-Bot
pip install -r requirements.txt
```

Create a `.env` file with your bot configuration:

```env
DISCORD_TOKEN=
COMMAND_PREFIX=
MAX_SUGGESTION_LENGTH=
RATE_LIMIT_DURATION=
MAX_SUGGESTIONS_PER_USER=
```

Start the bot:

```bash
python bot.py
```

## 📋 Commands

### User

- `/suggest <text>` — submit a suggestion
- `/mysuggestions` — view your suggestions
- `/edit <suggestion_id> <new_text>` — edit a suggestion
- `/search <query>` — search suggestions
- `/top <timeframe>` — view popular suggestions
- `/categories` — list categories
- `/stats` — view suggestion statistics

Administrative actions are available through the suggestion management workflow.

## 🗄️ Data

MongoDB stores suggestion records, voting information, statuses, categories, and user suggestion history.

Never commit bot tokens, database credentials, or other secrets to the repository.

## 🤝 Contributing

Fork the repository, create a focused branch, test your changes, and open a pull request with a clear explanation.

## 📄 License

MIT License. See [`LICENSE`](LICENSE).

⭐ If this bot is useful for your community, consider starring the repository.
