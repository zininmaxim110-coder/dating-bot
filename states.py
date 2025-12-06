from aiogram.dispatcher.filters.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_for_language = State()  # Выбор языка
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_city = State()
    waiting_for_gender = State()
    waiting_for_target_gender = State()
    waiting_for_photo = State()
    waiting_for_bio = State()

class SearchStates(StatesGroup):
    viewing = State()
    viewing_likes = State()

class LikeStates(StatesGroup):
    waiting_for_valentine = State()

class EditStates(StatesGroup):
    """Редактирование профиля"""
    select_field = State()
    edit_name = State()
    edit_age = State()
    edit_city = State()
    edit_gender = State()
    edit_target = State()
    edit_photo = State()
    edit_bio = State()
    edit_language = State()

class AdminStates(StatesGroup):
    waiting_for_delete_id = State()
    waiting_for_search_term = State()
    create_name = State()
    create_age = State()
    create_city = State()
    create_gender = State()
    create_target = State()
    create_photo = State()
    create_bio = State()
    create_username = State()
    admin_viewing = State()
    edit_username = State()
    # Рассылка
    broadcast_select = State()
    broadcast_text_ru = State()
    broadcast_text_uz = State()
    broadcast_text_uk = State()
    broadcast_text_kz = State()
    broadcast_name = State()
    broadcast_confirm = State()