# Baby Bottle Tracker Telegram Bot 🍼

A modern and intuitive Telegram bot to track baby bottle feedings and diaper changes.  
Perfect for parents who want a clean, single-message interface to monitor their baby's daily activities.

---

## ✨ New Features (v2.1)

- **📄 PDF Reports** - Download detailed weekly/monthly reports with statistics and charts
- **🌍 Multilingual PDFs** - Generate reports in French, English, and Hebrew with AI-powered translation
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
- 📄 **PDF Reports** - Download detailed reports for any period
- ⚙️ **Settings** - Customize display preferences

### Smart Features
- **Time Suggestions** - Quick buttons for common feeding times
- **Amount Memory** - Remembers and suggests last used bottle amount
- **AI Analysis** - Gemini-powered insights about feeding patterns
- **Auto-refresh** - Message updates automatically after actions
- **PDF Generation** - Professional reports with charts and statistics

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
   SUPABASE_URL="your_supabase_url"
   SUPABASE_KEY="your_supabase_key"
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
- **Action buttons**: Add Bottle, Remove Bottle, Poop, Stats, PDF, Settings

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

### PDF Reports
- Click "📄 PDF" to access report generation
- Choose period: 7 days, 30 days, or custom
- Select language: 🇫🇷 French, 🇺🇸 English, 🇮🇱 Hebrew
- Download professional reports with:
  - Complete bottle and diaper change history
  - Daily statistics and trends
  - **📈 Daily consumption charts with values on curve**
  - Charts and visualizations
  - AI-powered insights (if available)
  - Professional formatting
  - Automatic translation of custom notes
  - **🔗 Clickable links to official baby nutrition information**

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
├── database.py          # Database operations (Supabase)
├── biberons.json        # Data storage (legacy)
├── requirements.txt     # Python dependencies
├── test_pdf.py          # PDF generation test script
├── handlers/            # Feature modules
│   ├── add.py          # Bottle addition logic
│   ├── poop.py         # Poop tracking logic
│   ├── delete.py       # Entry deletion
│   ├── stats.py        # Statistics and AI insights
│   ├── settings.py     # User preferences
│   ├── queries.py      # Main message generation
│   ├── pdf.py          # PDF report generation
│   └── groups.py       # Group management
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
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase API key

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

## 📄 PDF Reports

The bot generates professional PDF reports with:
- **Complete Data Export** - All bottles and diaper changes for the selected period
- **Statistical Analysis** - Daily averages, totals, and trends
- **Visual Charts** - Professional formatting with tables and graphs
- **AI Insights** - Gemini-powered analysis (if available)
- **Customizable Periods** - 7 days, 30 days, or custom date ranges
- **Multilingual Support** - Generate reports in French, English, and Hebrew

### PDF Features
- Professional layout with company branding
- Color-coded sections for easy reading
- Detailed daily breakdowns
- Summary statistics
- **📈 Daily consumption charts with clear axes and values**
- Complete data tables
- Medical-grade formatting
- **AI-Powered Translation** - Automatic translation of custom diaper change notes
- **Language Selection** - Choose your preferred language for the report
- **Cultural Adaptation** - Proper terminology for each language
- **Chronological Mixed Table** - Combined bottle and diaper change timeline with color coding
- **Hebrew Font Support** - Proper RTL text rendering for Hebrew reports

### Supported Languages
- 🇫🇷 **French** - Default language with complete terminology
- 🇺🇸 **English** - Professional English medical terminology
- 🇮🇱 **Hebrew** - Right-to-left layout with Hebrew medical terms and automatic font download

### Translation Features
- **Automatic Note Translation** - Custom diaper change notes are translated using AI
- **Medical Terminology** - Appropriate medical terms for each language
- **Cultural Sensitivity** - Respects cultural differences in baby care terminology
- **Fallback System** - Original text preserved if translation fails
- **Automatic Hebrew Font Download** - Downloads Noto Sans Hebrew font for proper Hebrew rendering

### Chronological Mixed Table
- **Combined Timeline** - All bottles and diaper changes in chronological order
- **Color Coding** - Blue background for bottles, orange background for diaper changes
- **Easy Reading** - Clear visual distinction between different types of entries
- **Complete History** - All activities sorted by date and time for easy reference
- **Professional Layout** - Clean table design with proper spacing and alignment

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
- [ ] Custom PDF templates
- [ ] Email report delivery

---

*Created with ❤️ by Ichai SIMAH*