                                                                     בס"ד
# 🍼 Baby Bottle Tracker Bot

A comprehensive Telegram bot for tracking baby feeding and diaper changes with multi-language support (French, English, Hebrew).

## 🌟 Features

- **🍼 Bottle Tracking**: Log feedings with amount and time
- **💩 Diaper Changes**: Track changes with optional notes
- **📊 Statistics**: View detailed stats with AI analysis
- **👥 Group Management**: Share tracking with family members
- **📄 PDF Reports**: Generate reports for medical visits
- **🕯️ Shabbat Mode**: Special tracking for religious observance
- **🌍 Multi-language**: French, English, and Hebrew support

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Optional: Google Gemini API key for AI features

### Installation

1. **Clone and configure**
   ```bash
   git clone <repository-url>
   cd bottle-track-server-version
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Environment variables**
   ```env
   TELEGRAM_TOKEN=your_telegram_bot_token
   GEMINI_API_KEY=your_gemini_api_key
   ADMIN_ID=your_admin_user_id
   DATABASE_PATH=data/baby_bottle_tracker.db
   ```

3. **Start the bot**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

### Manual Setup
```bash
pip install -r requirements.txt
export TELEGRAM_TOKEN=your_token
export GEMINI_API_KEY=your_key
python main.py
```

## 📖 Usage

1. Start chat with bot on Telegram
2. Send `/start` and choose language
3. Use interactive buttons to track bottles and diaper changes
4. Generate PDF reports for medical visits
5. Share tracking with family through groups

### Key Features
- **Add Bottle**: Select time and amount with smart suggestions
- **Track Changes**: Log diaper changes with optional notes
- **Statistics**: View 5-day stats with AI insights
- **PDF Reports**: Generate comprehensive reports (7/14/30 days)
- **Group Management**: Create/join groups for family sharing
- **Shabbat Mode**: Pre-enter data for religious observance

## 🏗️ Architecture

- **Backend**: Python 3.11 + python-telegram-bot v21.2
- **Database**: SQLite with optimized queries
- **Containerization**: Docker & Docker Compose
- **AI**: Google Gemini API for intelligent analysis
- **PDF**: ReportLab with Hebrew font support

## 🐳 Docker Commands

```bash
# Start
docker-compose up -d

# Logs
docker-compose logs -f bot

# Stop
docker-compose down

# Restart
docker-compose restart bot
```

## 🔧 Configuration

### Environment Variables
|      Variable      |      Description      | Required |
|--------------------|-----------------------|----------|
|  `TELEGRAM_TOKEN`  |   Telegram bot token  |    Yes   |
|  `GEMINI_API_KEY`  | Google Gemini API key |    No    |
|     `ADMIN_ID`     |     Admin user ID     |    No    |
|    `TEST_MODE`     |    Enable test mode   |    No    |
|   `DATABASE_PATH`  |  SQLite database path |    No    |

## 🔒 Security & Privacy

- All data stored locally in SQLite database
- No data sent to third-party services (except optional AI)
- Automatic database backups
- User isolation with personal groups

## 🛠️ Development

### Project Structure
```
├── main.py              # Main application
├── database.py          # Database operations
├── utils.py             # Utility functions
├── translations.py      # Multi-language support
├── handlers/            # Feature handlers
├── data/               # Database storage
└── requirements.txt    # Dependencies
```

### Adding Features
1. Create handler in `handlers/` directory
2. Add to `main.py`
3. Update translations in `translations.py`
4. Add database operations in `database.py`

## 🌍 Multi-language Support

Supports French (fr), English (en), and Hebrew (he) with:
- Complete interface translations
- Hebrew RTL text handling
- PDF reports in all languages
- User language preferences

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Add translations for new text
4. Test with multiple languages
5. Submit pull request

## 🆘 Support

- Check logs: `docker-compose logs bot`
- Verify environment variables
- Check database connectivity

---

**Note**: For personal use only. Not for medical purposes. Consult healthcare professionals for medical advice. 

"Created wit love by Ichai SIMAH ❤️"