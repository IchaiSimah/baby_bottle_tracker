# Baby Bottle Tracker Telegram Bot 🍼

A simple and convenient Telegram bot to track the amount and time of baby bottle feedings.  
Perfect for parents who want to keep a quick and easy history of their baby's meals.

---

## Features

- Add a new bottle with quantity (in ml) and time (option to use current time)  
- View the last recorded bottle feeding  
- Display the 4 most recent bottle feedings  
- Calculate the total milk given today  
- Delete the last bottle feeding entry in case of mistakes  
- Multi-user support (data isolated per user)  
- Built-in help commands

---

## Installation

1. Clone this repository:  
   ```bash
   git clone https://github.com/yourusername/baby-bottle-tracker.git
   cd baby-bottle-tracker
   ```

2. Create and activate a virtual environment (optional but recommended):  
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory and add your Telegram token:  
   ```
   TELEGRAM_TOKEN="your_telegram_token_here"
   ```

5. Run the bot:  
   ```bash
   python bot.py
   ```

---

## Usage

- `/start` or `/help` — Show available commands  
- `/add` — Start adding a new bottle feeding (quantity + time)  
- `/last` — Show the last recorded bottle feeding  
- `/list` — Show the 4 most recent bottle feedings  
- `/total` — Show total milk given today  
- `/delete` — Delete the last bottle feeding entry  
- `/cancel` — Cancel an ongoing entry

---

## Project Structure

- `bot.py` — Main Telegram bot code  
- `biberons.json` — JSON file storing data (one section per user)  
- `.env` — Environment variables (Telegram token)  
- `requirements.txt` — Python dependencies  

---

## Possible Improvements

- Switch to a database for better scalability and reliability   
- Automated notifications or reminders  


---


*Created with ❤️ by Ichai SIMAH