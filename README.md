# 🍼 Baby Bottle Tracker Bot

A comprehensive Telegram bot for tracking baby feeding and diaper changes, designed for families and caregivers. The bot provides an intuitive interface for logging bottles, diaper changes, and generating detailed reports.

## 🌟 Features

### Core Functionality
- **🍼 Bottle Tracking**: Log bottle feedings with amount and time
- **💩 Diaper Changes**: Track diaper changes with optional notes
- **📊 Statistics**: View detailed feeding and diaper statistics
- **👥 Group Management**: Share tracking with family members or caregivers
- **📱 Interactive Interface**: Clean, button-based navigation
- **🕐 Timezone Support**: Automatic timezone handling for accurate tracking

### Advanced Features
- **📄 PDF Reports**: Generate comprehensive PDF reports for medical visits
- **⚙️ Customizable Settings**: Adjust display preferences and timezone
- **🔄 Real-time Updates**: Instant synchronization across all group members
- **📈 Performance Monitoring**: Built-in performance tracking and optimization
- **🛡️ Data Persistence**: SQLite database with automatic backups

### Special Features
- **🕯️ Shabbat Mode**: Special tracking mode for religious observance
- **🎨 Hebrew Font Support**: Full support for Hebrew text in reports
- **📊 Advanced Analytics**: Detailed statistics and trend analysis

## 🏗️ Architecture

### Technology Stack
- **Backend**: Python 3.11
- **Telegram API**: python-telegram-bot v21.2
- **Database**: SQLite with optimized queries
- **Containerization**: Docker & Docker Compose
- **PDF Generation**: ReportLab with custom fonts
- **AI Integration**: Google Gemini API for enhanced features

### Project Structure
```
├── main.py              # Main bot application entry point
├── database.py          # Database operations and SQLite management
├── utils.py             # Utility functions and caching system
├── config.py            # Configuration and environment variables
├── handlers/            # Feature-specific handlers
│   ├── add.py          # Bottle addition logic
│   ├── poop.py         # Diaper change tracking
│   ├── delete.py       # Data deletion functionality
│   ├── stats.py        # Statistics and analytics
│   ├── settings.py     # User settings management
│   ├── groups.py       # Group management features
│   ├── pdf.py          # PDF report generation
│   ├── shabbat.py      # Shabbat mode functionality
│   └── queries.py      # Message content generation
├── data/               # SQLite database storage
├── logs/               # Application logs
├── assets/             # Static assets (fonts, images)
├── docker-compose.yml  # Docker orchestration
├── Dockerfile          # Container configuration
└── requirements.txt    # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Optional: Google Gemini API key for enhanced features

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bottle-track-server-version
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Configure environment variables**
   ```env
   TELEGRAM_TOKEN=your_telegram_bot_token
   TEST_TOKEN=your_test_token_if_needed
   GEMINI_API_KEY=your_gemini_api_key
   ADMIN_ID=your_admin_user_id
   TEST_MODE=false
   ```

4. **Start the bot**
   ```bash
   chmod +x start_docker.sh
   ./start_docker.sh
   ```

### Manual Setup (without Docker)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**
   ```bash
   export TELEGRAM_TOKEN=your_token
   export GEMINI_API_KEY=your_key
   export ADMIN_ID=your_id
   ```

3. **Run the bot**
   ```bash
   python main.py
   ```

## 📖 Usage

### Getting Started
1. Start a chat with your bot on Telegram
2. Send `/start` to initialize your personal tracking space
3. Use the interactive buttons to navigate features

### Basic Commands
- `/start` - Initialize or refresh the main interface
- `/help` - Show help information

### Key Features

#### Adding a Bottle
1. Click "🍼 Add Bottle" in the main menu
2. Enter the amount (in ml)
3. Enter the time (HH:MM format)
4. Confirm the entry

#### Tracking Diaper Changes
1. Click "💩 Add Poop" in the main menu
2. Enter the time
3. Optionally add notes about consistency
4. Confirm the entry

#### Group Management
- **Create Group**: Set up a shared tracking space for family members
- **Join Group**: Join an existing group with an invitation code
- **Group Settings**: Manage group members and preferences

#### PDF Reports
- Generate comprehensive reports for medical appointments
- Includes feeding patterns, diaper changes, and statistics
- Available in multiple languages with Hebrew support

## 🔧 Configuration

### Environment Variables
 `TELEGRAM_TOKEN` Your Telegram bot token 
| `GEMINI_API_KEY`  Google Gemini API key 
| `ADMIN_ID`  Admin user ID for special commands 
| `TEST_MODE`  Enable test mode 
| `DATABASE_PATH`  SQLite database path 

### Database Configuration
The bot uses SQLite with the following tables:
- `groups`: Group information and settings
- `entries`: Bottle feeding records
- `poop`: Diaper change records
- `user_messages`: Message tracking for UI management

## 🐳 Docker Management

### Common Commands
```bash
# Start the bot
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop the bot
docker-compose down

# Restart the bot
docker-compose restart bot

# Rebuild after code changes
docker-compose up --build -d
```

### Database Access
```bash
# Access database shell
docker exec -it baby_bottle_tracker_db sqlite3 /data/baby_bottle_tracker.db

# View tables
.tables

# View recent entries
SELECT * FROM entries ORDER BY time DESC LIMIT 10;
```

## 📊 Performance Features

### Caching System
- Intelligent caching reduces database calls
- 5-minute cache TTL for optimal performance
- Automatic cache invalidation on data changes

### Database Optimization
- Indexed queries for fast data retrieval
- Connection pooling for concurrent access
- Automatic cleanup of old data

### Monitoring
- Built-in performance tracking
- Response time monitoring
- Cache hit/miss statistics

## 🔒 Security & Privacy

- **Data Privacy**: All data stored locally in SQLite database
- **User Isolation**: Each user has their own personal group
- **Secure Communication**: Uses Telegram's encrypted API
- **No External Storage**: No data sent to third-party services

## 🛠️ Development

### Code Structure
The project follows a modular architecture:
- **Handlers**: Feature-specific logic separated into modules
- **Database Layer**: Abstracted database operations
- **Utility Functions**: Shared functionality and caching
- **Configuration**: Centralized environment management

### Adding New Features
1. Create a new handler in the `handlers/` directory
2. Add the handler to `main.py`
3. Update the message content in `queries.py`
4. Add any necessary database operations in `database.py`

### Testing
```bash
# Run in test mode
export TEST_MODE=true
python main.py
```

## 📝 API Reference

### Database Functions
- `get_user_group_id(user_id)`: Get group ID for user
- `add_entry_to_group(group_id, amount, time)`: Add bottle entry
- `add_poop_to_group(group_id, time, info)`: Add diaper change
- `get_group_stats_for_user(user_id, days)`: Get user statistics

### Utility Functions
- `load_user_data(user_id)`: Load user-specific data
- `find_group_for_user(data, user_id)`: Find user's group
- `create_personal_group(data, user_id)`: Create personal group

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 🆘 Support

For support and questions:
- Check the logs: `docker-compose logs bot`
- Review the configuration in `.env`
- Ensure all environment variables are set correctly

## 🔄 Changelog

### Version 2.0
- Migrated to SQLite database
- Added Docker support
- Implemented caching system
- Added PDF report generation
- Enhanced group management
- Added Shabbat mode
- Improved performance and reliability

---

**Note**: This bot is designed for personal use and should not be used for medical purposes. Always consult healthcare professionals for medical advice regarding infant feeding and care. 