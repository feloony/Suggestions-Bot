# Discord Suggestions Bot

A feature-rich Discord bot that enables users to submit, discuss, and vote on suggestions, helping create a more community-driven server experience.

## Features

- **Suggestion Submissions**: Users can submit suggestions, optionally categorized or anonymous, directly within Discord.
- **Voting and Discussion**: Each suggestion has its own voting (👍/👎) and discussion thread.
- **Suggestion Management**: Admins can review, accept, or reject suggestions.
- **User Commands**: Users can view their suggestion history, search suggestions, and edit their past suggestions.
- **Top Suggestions**: Displays the most popular suggestions based on upvotes within a specified timeframe.
- **Statistics**: Provides statistics on the number of suggestions, including counts of accepted, pending, and rejected suggestions.
- **Categories**: List available suggestion categories for organized submissions.
- **Rate Limiting**: Ensures users don’t spam suggestions, with cooldowns managed per user.

## Installation

### Prerequisites

- Node.js (v16 or higher)
- Python (for Discord bot code)
- Discord Bot Token
- MongoDB database (for suggestion data storage)

### Setting Up

1. Clone the repository:
   ```bash
   git clone https://github.com/feloony/Suggestions-Bot.git
   cd Suggestions-Bot
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables in a `.env` file:
   ```env
   DISCORD_TOKEN=
   COMMAND_PREFIX=
   MAX_SUGGESTION_LENGTH=
   RATE_LIMIT_DURATION=
   MAX_SUGGESTIONS_PER_USER=
   ```

4. Start the bot:
   ```bash
   python bot.py
   ```

## Commands Overview

### User Commands

- `/suggest <text>` - Submit a new suggestion. Options for category and anonymity.
- `/mysuggestions` - View your past suggestions.
- `/edit <suggestion_id> <new_text>` - Edit a previous suggestion.
- `/search <query>` - Search suggestions by text query.
- `/top <timeframe>` - View top suggestions within a specified timeframe (e.g., day, week, all).
- `/categories` - View available categories for suggestions.
- `/stats` - View suggestion statistics for the server.

### Admin Commands

- Suggestion management options available through direct interaction with suggestion embeds (approve/reject).

## Configuration

- **Rate Limiting**: Configure the maximum number of suggestions per user and time limits in the `Config` file.
- **Suggestion Length**: Define maximum suggestion length in `Config`.
- **Category Management**: Add, remove, and manage suggestion categories in the database.

## Database Structure

- Stores suggestion details, voting counts, user suggestion history, and channels for suggestion threads.
- Tracks suggestion status (pending, approved, rejected) and user voting history.

## Contributing

Contributions are welcome! Please open an issue or pull request for any bug fixes, feature additions, or improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Support

For issues or questions, open an issue on this repository, or reach out on Discord.
