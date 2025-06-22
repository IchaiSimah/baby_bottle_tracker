from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils import load_data, save_data, find_group_for_user

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = load_data()
    group = find_group_for_user(data, user_id)
    if not group:
        await query.edit_message_text(
            "❌ Vous n'êtes dans aucun groupe.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Annuler", callback_data="cancel")
            ]])
        )
        return
    
    # Get current settings
    bottles_to_show = data[group].get("bottles_to_show", 5)
    poops_to_show = data[group].get("poops_to_show", 1)
    
    message = "⚙️ **Paramètres:**\n\n"
    message += f"**Affichage principal:**\n"
    message += f"• 🍼 Biberons affichés: {bottles_to_show}\n"
    message += f"• 💩 Cacas affichés: {poops_to_show}\n\n"
    message += "**Modifier les paramètres:**"
    
    # Create keyboard for settings
    keyboard = [
        [
            InlineKeyboardButton(f"🍼 Biberons: {bottles_to_show}", callback_data="setting_bottles")
        ],
        [
            InlineKeyboardButton(f"💩 Cacas: {poops_to_show}", callback_data="setting_poops")
        ],
        [
            InlineKeyboardButton("👥 Groupes", callback_data="groups")
        ],
        [
            InlineKeyboardButton("🏠 Accueil", callback_data="refresh"),
            InlineKeyboardButton("❌ Annuler", callback_data="cancel")
        ]
    ]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE, setting: str = None):
    """Handle settings changes"""
    query = update.callback_query
    await query.answer()
    
    if not setting:
        # Extract setting from callback data
        setting = query.data.replace("setting_", "")
    
    user_id = update.effective_user.id
    data = load_data()
    group = find_group_for_user(data, user_id)
    
    if setting == "bottles":
        # Show bottle count options
        current = data[group].get("bottles_to_show", 5)
        keyboard = []
        
        # Create rows of 3 buttons each
        options = [3, 4, 5, 6, 7, 8, 9, 10]
        for i in range(0, len(options), 3):
            row = []
            for j in range(3):
                if i + j < len(options):
                    option = options[i + j]
                    text = f"{option} {'✅' if option == current else ''}"
                    row.append(InlineKeyboardButton(text, callback_data=f"set_bottles_{option}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="settings")])
        
        message = "🍼 **Choisissez le nombre de biberons à afficher:**"
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif setting == "poops":
        # Show poop count options
        current = data[group].get("poops_to_show", 1)
        keyboard = []
        
        # Create rows of 3 buttons each
        options = [1, 2, 3, 4, 5]
        for i in range(0, len(options), 3):
            row = []
            for j in range(3):
                if i + j < len(options):
                    option = options[i + j]
                    text = f"{option} {'✅' if option == current else ''}"
                    row.append(InlineKeyboardButton(text, callback_data=f"set_poops_{option}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="settings")])
        
        message = "💩 **Choisissez le nombre de cacas à afficher:**"
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif setting.startswith("set_bottles_"):
        # Set bottle count
        count = int(setting.replace("set_bottles_", ""))
        data[group]["bottles_to_show"] = count
        await save_data(data, context)
        
        # Show confirmation and return to settings
        await show_settings(update, context)
    
    elif setting.startswith("set_poops_"):
        # Set poop count
        count = int(setting.replace("set_poops_", ""))
        data[group]["poops_to_show"] = count
        await save_data(data, context)
        
        # Show confirmation and return to settings
        await show_settings(update, context) 