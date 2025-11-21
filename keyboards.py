from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import INTERESTS
from locales import get_text

def get_main_menu_keyboard(lang='en'):
    keyboard = [
        [InlineKeyboardButton(get_text(lang, 'start_chatting'), callback_data='start_search')],
        [InlineKeyboardButton(get_text(lang, 'set_interest'), callback_data='set_interest')],
        [InlineKeyboardButton(get_text(lang, 'language_btn'), callback_data='set_language')],
        [InlineKeyboardButton(get_text(lang, 'help_btn'), callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_interest_keyboard(lang='en'):
    keyboard = []
    row = []
    for interest in INTERESTS:
        row.append(InlineKeyboardButton(interest, callback_data=f'interest_{interest}'))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(get_text(lang, 'back'), callback_data='main_menu')])
    return InlineKeyboardMarkup(keyboard)

def get_chat_keyboard(lang='en'):
    keyboard = [
        [InlineKeyboardButton(get_text(lang, 'end_chat'), callback_data='stop_chat'),
         InlineKeyboardButton(get_text(lang, 'next_partner'), callback_data='next_partner')],
        [InlineKeyboardButton(get_text(lang, 'report'), callback_data='report_menu'),
         InlineKeyboardButton(get_text(lang, 'block'), callback_data='block_partner')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_queue_keyboard(lang='en'):
    keyboard = [
        [InlineKeyboardButton(get_text(lang, 'cancel_search'), callback_data='cancel_search')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_captcha_keyboard(lang='en'):
    keyboard = [
        [InlineKeyboardButton(get_text(lang, 'i_am_human'), callback_data='captcha_solved')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_report_keyboard(lang='en'):
    reasons = ["Spam", "Abuse", "Inappropriate", "Other"]
    keyboard = []
    for reason in reasons:
        keyboard.append([InlineKeyboardButton(reason, callback_data=f'report_{reason}')])
    keyboard.append([InlineKeyboardButton(get_text(lang, 'back'), callback_data='back_to_chat')])
    return InlineKeyboardMarkup(keyboard)

def get_language_keyboard():
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')],
        [InlineKeyboardButton("🇱🇰 සිංහල", callback_data='lang_si')],
        [InlineKeyboardButton("🔙 Back", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)
