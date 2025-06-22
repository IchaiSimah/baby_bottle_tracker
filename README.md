# Baby Bottle Tracker Telegram Bot 🍼

A modern and intuitive Telegram bot to track baby bottle feedings and diaper changes.  
Perfect for parents who want a clean, single-message interface to monitor their baby's daily activities.

---

## ✨ New Features (v2.0)

- **Single Message Interface** - Everything happens in one message that updates dynamically
- **Inline Keyboards** - No more command-based interactions, just click buttons
- **Smart Defaults** - Remembers last bottle amount and suggests common times
- **Statistics Dashboard** - 5-day overview with AI-powered insights (Gemini integration)
- **Customizable Display** - Choose how many bottles and poops to show
- **Modern UI** - Clean, organized interface with emojis and markdown formatting

---

## 🚀 Features

### Core Functionality
- 🍼 **Add Bottles** - Quick time selection with smart suggestions
- ❌ **Remove Bottles** - One-click removal of last entry
- 💩 **Track Poop** - Record diaper changes with optional notes
- 📊 **Statistics** - 5-day overview with consumption trends
- ⚙️ **Settings** - Customize display preferences

### Smart Features
- **Time Suggestions** - Quick buttons for common feeding times
- **Amount Memory** - Remembers and suggests last used bottle amount
- **AI Analysis** - Gemini-powered insights about feeding patterns
- **Auto-refresh** - Message updates automatically after actions

---

## 🛠️ Installation

1. **Clone this repository:**  
   ```bash
   git clone https://github.com/yourusername/baby-bottle-tracker.git
   cd baby-bottle-tracker
   ```

2. **Create and activate a virtual environment:**  
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**  
   Create a `.env` file in the root directory:
   ```
   TELEGRAM_TOKEN="your_telegram_token_here"
   TEST_TOKEN="your_test_token_here"  # Optional
   BACKUP_CHANNEL_ID="your_backup_channel_id"
   TELEGRAM_API_ID="your_telegram_api_id"
   TELEGRAM_API_HASH="your_telegram_api_hash"
   STRING_SESSION="your_session_string"
   GEMINI_API_KEY="your_gemini_api_key"  # Optional for AI insights
   ```

5. **Run the bot:**  
   ```bash
   python main.py
   ```

---

## 📱 Usage

### Getting Started
1. Send `/start` to the bot
2. A main message will appear with your current data and action buttons
3. Use the inline buttons to interact with the bot

### Main Interface
The bot shows:
- **Last 5 bottles** (configurable)
- **Last poop entry** (configurable)
- **Action buttons**: Add Bottle, Remove Bottle, Poop, Stats, Settings

### Adding a Bottle
1. Click "🍼 Ajouter"
2. Select time from suggestions or "Maintenant"
3. Choose amount (last amount is highlighted)
4. Bottle is added and message updates automatically

### Adding Poop
1. Click "💩 Caca"
2. Select time from suggestions or "Maintenant"
3. Add optional information or click "Terminer"
4. Entry is saved and message updates

### Statistics
- Click "📊 Stats" to see 5-day overview
- Includes total consumption, averages, and AI insights
- Shows daily breakdown with trends

### Settings
- Click "⚙️ Paramètres" to customize display
- Choose how many bottles to show (3-10)
- Choose how many poops to show (1-5)

---

## 🏗️ Project Structure

```
baby_bottle_tracker/
├── main.py              # Main bot entry point
├── config.py            # Configuration settings
├── utils.py             # Utility functions and data management
├── biberons.json        # Data storage
├── requirements.txt     # Python dependencies
├── handlers/            # Feature modules
│   ├── add.py          # Bottle addition logic
│   ├── poop.py         # Poop tracking logic
│   ├── delete.py       # Entry deletion
│   ├── stats.py        # Statistics and AI insights
│   ├── settings.py     # User preferences
│   └── queries.py      # Main message generation
└── README.md           # This file
```

---

## 🔧 Configuration

### Environment Variables
- `TELEGRAM_TOKEN` - Your main bot token
- `TEST_TOKEN` - Test bot token (optional)
- `BACKUP_CHANNEL_ID` - Channel for automatic backups
- `TELEGRAM_API_ID` - Telegram API credentials
- `TELEGRAM_API_HASH` - Telegram API credentials
- `STRING_SESSION` - Telethon session string
- `GEMINI_API_KEY` - Google Gemini API key (optional)

### Data Structure
```json
{
  "group_name": {
    "users": [user_ids],
    "entries": [
      {"amount": 120, "time": "20-06-2025 15:30"}
    ],
    "poop": [
      {"time": "20-06-2025 16:00", "info": "Normal"}
    ],
    "time_difference": 3,
    "last_bottle": 120,
    "bottles_to_show": 5,
    "poops_to_show": 1
  }
}
```

---

## 🤖 AI Integration

The bot includes optional Gemini AI integration for intelligent insights:
- Analyzes feeding patterns over 5 days
- Provides encouraging summaries
- Identifies trends in consumption
- Requires `GEMINI_API_KEY` environment variable

---

## 🔄 Migration from v1.0

If you're upgrading from the previous version:
1. Your existing data in `biberons.json` will be preserved
2. New settings fields will be added automatically
3. The bot will work with both old and new data formats
4. All existing functionality is maintained

---

## 🚀 Future Improvements

- [ ] Database migration for better scalability
- [ ] Automated notifications and reminders
- [ ] Multi-language support
- [ ] Advanced analytics and charts
- [ ] Integration with health apps
- [ ] Family sharing features

---

*Created with ❤️ by Ichai SIMAH*