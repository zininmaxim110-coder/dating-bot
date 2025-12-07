from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from translations import t

def get_language_keyboard():
    """Выбор языка"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz")
    )
    keyboard.add(
        InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk"),
        InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kz")
    )
    return keyboard

def get_main_keyboard(lang: str = 'ru'):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)
    keyboard.add(
        KeyboardButton(t('btn_profile', lang)),
        KeyboardButton(t('btn_search', lang))
    )
    keyboard.add(
        KeyboardButton(t('btn_likes', lang)),
        KeyboardButton(t('btn_mutual', lang))
    )
    keyboard.add(
        KeyboardButton(t('btn_edit', lang)),
        KeyboardButton(t('btn_help', lang))
    )
    return keyboard

def get_search_keyboard(lang: str = 'ru'):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)
    keyboard.add(
        KeyboardButton(t('btn_like', lang)),
        KeyboardButton(t('btn_valentine', lang))
    )
    keyboard.add(
        KeyboardButton(t('btn_dislike', lang)),
        KeyboardButton(t('btn_stop', lang))
    )
    return keyboard

def get_like_response_keyboard(user_id: int, lang: str = 'ru'):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(t('btn_like', lang), callback_data=f"respond_like_{user_id}"),
        InlineKeyboardButton(t('btn_dislike', lang), callback_data=f"respond_skip_{user_id}")
    )
    return keyboard

def get_city_keyboard(lang: str = 'ru'):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton(t('btn_location', lang), request_location=True))
    return keyboard

def get_gender_keyboard(lang: str = 'ru'):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton(t('btn_male', lang)), KeyboardButton(t('btn_female', lang)))
    keyboard.add(KeyboardButton(t('btn_other', lang)))
    return keyboard

def get_target_gender_keyboard(lang: str = 'ru'):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton(t('btn_search_female', lang)), KeyboardButton(t('btn_search_male', lang)))
    keyboard.add(KeyboardButton(t('btn_search_all', lang)))
    return keyboard

def get_photo_keyboard(lang: str = 'ru'):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton(t('btn_done', lang)), KeyboardButton(t('btn_skip', lang)))
    return keyboard

def get_bio_keyboard(lang: str = 'ru'):
    """Клавиатура для био с кнопкой пропуска"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton(t('btn_skip_bio', lang)))
    return keyboard

def get_edit_keyboard(lang: str = 'ru'):
    """Клавиатура редактирования профиля"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton(t('edit_name', lang)),
        KeyboardButton(t('edit_age', lang))
    )
    keyboard.add(
        KeyboardButton(t('edit_city', lang)),
        KeyboardButton(t('edit_gender', lang))
    )
    keyboard.add(
        KeyboardButton(t('edit_target', lang)),
        KeyboardButton(t('edit_photo', lang))
    )
    keyboard.add(
        KeyboardButton(t('edit_bio', lang)),
        KeyboardButton(t('edit_lang', lang))
    )
    keyboard.add(KeyboardButton(t('btn_back', lang)))
    return keyboard

def get_cancel_keyboard(lang: str = 'ru'):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton(t('btn_cancel', lang)))
    return keyboard

def get_back_keyboard(lang: str = 'ru'):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton(t('btn_back', lang)))
    return keyboard

def get_skip_keyboard(lang: str = 'ru'):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton(t('btn_skip', lang)))
    keyboard.add(KeyboardButton(t('btn_cancel', lang)))
    return keyboard

# ========== АДМИН КЛАВИАТУРЫ (всегда на русском) ==========

def get_admin_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)
    keyboard.add(KeyboardButton("📊 Статистика"), KeyboardButton("👥 Пользователи"))
    keyboard.add(KeyboardButton("🔍 Поиск"), KeyboardButton("➕ Создать анкету"))
    keyboard.add(KeyboardButton("🤖 Мои анкеты"), KeyboardButton("🗑️ Удалить"))
    keyboard.add(KeyboardButton("👁️ Смотреть анкеты"), KeyboardButton("🚫 Теневые баны"))
    keyboard.add(KeyboardButton("📝 Ключевые слова"), KeyboardButton("📨 Рассылка"))
    keyboard.add(KeyboardButton("◀️ На главную"))
    return keyboard

def get_admin_search_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)
    keyboard.add(KeyboardButton("❤️ Лайк"), KeyboardButton("👎 Дизлайк"))
    keyboard.add(KeyboardButton("🚫 Теневой бан"), KeyboardButton("🛑 Выход"))
    return keyboard

def get_user_actions_keyboard(user_id: int, is_bot: bool = False):
    keyboard = InlineKeyboardMarkup(row_width=2)
    if is_bot:
        keyboard.add(
            InlineKeyboardButton("✏️ Username", callback_data=f"edit_username_{user_id}"),
            InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_user_{user_id}")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("🚫 Бан", callback_data=f"ban_user_{user_id}"),
            InlineKeyboardButton("✅ Разбан", callback_data=f"unban_user_{user_id}")
        )
        keyboard.add(InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_user_{user_id}"))
    return keyboard

def get_broadcast_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    keyboard.add(KeyboardButton("📝 Новая рассылка"), KeyboardButton("📋 Шаблоны"))
    keyboard.add(KeyboardButton("◀️ Назад"))
    return keyboard

def get_skip_photo_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton("✅ Готово"), KeyboardButton("⏭️ Без фото"))
    keyboard.add(KeyboardButton("❌ Отмена"))
    return keyboard

def get_yes_no_keyboard(callback_prefix: str, target_id: int = None):
    keyboard = InlineKeyboardMarkup(row_width=2)
    if target_id:
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data=f"{callback_prefix}_yes_{target_id}"),
            InlineKeyboardButton("❌ Нет", callback_data=f"{callback_prefix}_no_{target_id}")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data=f"{callback_prefix}_yes"),
            InlineKeyboardButton("❌ Нет", callback_data=f"{callback_prefix}_no")
        )
    return keyboard

def get_template_keyboard(templates: list):
    """Клавиатура с шаблонами рассылки"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    for tpl in templates:
        keyboard.add(InlineKeyboardButton(f"📄 {tpl.name}", callback_data=f"tpl_send_{tpl.id}"))
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="tpl_back"))
    return keyboard

def remove_keyboard():
    return ReplyKeyboardRemove()