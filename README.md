# Miraplexity Autonomous Bot

A Telegram bot for managing marketplace pool game tournaments with automated matchmaking, skill-based progression, and prize pool distribution.

## Features

- 🎱 **Tournament Management**: Join tournaments and compete with other players
- 🏆 **Leaderboards**: Real-time rankings based on skill ratings
- 💰 **Prize Pools**: Automatic prize distribution for top 10 players (75% of pool)
- 🎮 **Auto-Matchmaking**: Automated tournament rounds every 60 seconds
- 📊 **Player Progression**: XP, levels, and skill ratings that grow with wins
- 🤖 **Telegram Integration**: Easy-to-use bot commands

## Setup

### Prerequisites

- Python 3.8 or higher
- A Telegram Bot Token (get one from [@BotFather](https://t.me/botfather))
- A Supabase account and project

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/mikewthornton1988-glitch/miraplexity-autonomous-bot.git
   cd miraplexity-autonomous-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and fill in your credentials:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_KEY`: Your Supabase anon/public key
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token

4. Set up the database:
   - Follow the instructions in [DATABASE.md](DATABASE.md) to create the required tables in Supabase

5. Run the bot:
   ```bash
   python bot.py
   ```

## Usage

### Bot Commands

- `/start` - Display welcome message and available commands
- `/join <TournamentName>` - Join a tournament and add entry fee to prize pool
- `/leaderboard <TournamentName>` - View top 3 players and their stats
- `/payouts <TournamentName>` - View projected payouts for top 10 players
- `/auto <TournamentName>` - Start automated tournament rounds (every 60s)

### Example

```
/join Championship Pool
/leaderboard Championship Pool
/auto Championship Pool
```

## How It Works

### Prize Pool Distribution

- **Entry Fee**: Each player pays an entry fee when joining (default: $10)
- **Prize Pool**: 75% of the total pool is distributed to top 10 players
- **Weighted Distribution**: Higher ranks get larger shares (1st place gets the most)

### Player Progression

- **XP**: Winners gain +10 XP per match
- **Levels**: Level up every 100 XP
- **Skill Rating**: Winners gain +5 skill rating per match
- **Matchmaking**: Players are randomly paired, with outcomes influenced by skill rating

### Auto Mode

When auto mode is enabled:
1. Every 60 seconds, a new round begins
2. Players are randomly shuffled and paired
3. Matches are simulated using skill ratings + random factors
4. Winners gain XP, levels, and skill rating
5. Updated leaderboard and payouts are posted automatically

## Database Schema

See [DATABASE.md](DATABASE.md) for complete database schema and setup instructions.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License