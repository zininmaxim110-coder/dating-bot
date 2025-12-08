import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from config import BOT_TOKEN, ADMIN_ID
import database
from geo_utils import normalize_city, get_city_from_coords, format_distance
from translations import t, get_lang_list
from states import RegistrationStates, LikeStates, AdminStates, SearchStates, EditStates
from keyboards import (
    get_main_keyboard, get_gender_keyboard, get_target_gender_keyboard,
    get_photo_keyboard, get_search_keyboard, get_yes_no_keyboard,
    get_admin_keyboard, get_cancel_keyboard, get_skip_photo_keyboard,
    get_city_keyboard, get_bio_keyboard, remove_keyboard,
    get_like_response_keyboard, get_admin_search_keyboard,
    get_user_actions_keyboard, get_skip_keyboard, get_language_keyboard,
    get_edit_keyboard, get_back_keyboard, get_broadcast_keyboard,
    get_template_keyboard
)

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

user_photos = {}
admin_photos = {}
current_viewing = {}

async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    
    def is_admin(user_id: int) -> bool:
        try:
            return int(user_id) == ADMIN_ID
        except:
            return False
    
    def get_lang(user_id: int) -> str:
        return database.get_user_language(user_id) or 'ru'
    
    def is_btn(text: str, key: str, lang: str) -> bool:
        """Проверить, соответствует ли текст кнопке на любом языке"""
        for lng in ['ru', 'uz', 'uk', 'kz']:
            if text == t(key, lng):
                return True
        return False
    async def send_like_notification(to_user_id: int, from_user_id: int, valentine_message: str = None):
        from_user = database.get_user(from_user_id)
        to_user = database.get_user(to_user_id)
        
        if not from_user or not to_user:
            return
        
        if to_user.is_bot_profile:
            await send_admin_like_notification(to_user, from_user, valentine_message)
            return
        
        lang = to_user.language or 'ru'
        city_text = f"📍 {from_user.city}" if from_user.city else ""
        bio_text = f"\n📝 {from_user.bio}" if from_user.bio else ""
        
        profile = (
            f"{t('like_from', lang)}\n\n"
            f"👤 <b>{from_user.name}</b>, {from_user.age}\n"
            f"{city_text}\n"
            f"🚻 {from_user.gender}"
            f"{bio_text}"
        )
        
        if valentine_message:
            profile += f"\n\n💝 {valentine_message}"
        
        try:
            if from_user.photo_ids and len(from_user.photo_ids) > 0:
                await bot.send_photo(to_user_id, from_user.photo_ids[0], caption=profile, 
                                    parse_mode='HTML', reply_markup=get_like_response_keyboard(from_user_id, lang))
            else:
                await bot.send_message(to_user_id, profile, parse_mode='HTML', 
                                      reply_markup=get_like_response_keyboard(from_user_id, lang))
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
    
    async def send_mutual_like_notification(user1_id: int, user2_id: int):
        user1 = database.get_user(user1_id)
        user2 = database.get_user(user2_id)
        
        if not user1 or not user2:
            return
        
        # User1
        lang1 = user1.language or 'ru'
        username2 = f"@{user2.username}" if user2.username else "(username скрыт)"
        try:
            await bot.send_message(user1_id, t('mutual_like', lang1, name=user2.name, username=username2),
                                  parse_mode='HTML', reply_markup=get_main_keyboard(lang1))
        except:
            pass
        
        # User2
        lang2 = user2.language or 'ru'
        username1 = f"@{user1.username}" if user1.username else "(username скрыт)"
        try:
            await bot.send_message(user2_id, t('mutual_like', lang2, name=user1.name, username=username1),
                                  parse_mode='HTML', reply_markup=get_main_keyboard(lang2))
        except:
            pass
    
    async def send_admin_like_notification(bot_profile, from_user, valentine_message: str = None):
        username_text = f"@{from_user.username}" if from_user.username else "(нет)"
        text = (
            f"💌 <b>ЛАЙК НА АНКЕТУ!</b>\n\n"
            f"🤖 <b>Анкета:</b> {bot_profile.name}, {bot_profile.age}\n"
            f"📍 {bot_profile.city or '?'}\n\n"
            f"👤 <b>От:</b> {from_user.name}, {from_user.age}\n"
            f"🆔 <code>{from_user.telegram_id}</code>\n"
            f"📍 {from_user.city or '?'}\n"
            f"📱 {username_text}"
        )
        if from_user.bio:
            text += f"\n📝 {from_user.bio}"
        if valentine_message:
            text += f"\n\n💝 {valentine_message}"
        
        try:
            if from_user.photo_ids and len(from_user.photo_ids) > 0:
                await bot.send_photo(ADMIN_ID, from_user.photo_ids[0], caption=text, parse_mode='HTML')
            else:
                await bot.send_message(ADMIN_ID, text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"❌ {e}")
    async def show_candidate(message: types.Message, user_id: int, candidate, is_admin_view: bool = False):
        lang = get_lang(user_id) if not is_admin_view else 'ru'
        city_text = f"📍 {candidate.city}" if candidate.city else ""
        
        distance_text = ""
        if hasattr(candidate, '_distance') and candidate._distance < 9000:
            dist = format_distance(candidate._distance)
            if dist:
                distance_text = f" ({dist})"
        
        bio_text = f"\n\n📝 {candidate.bio}" if candidate.bio else ""
        ban_text = "\n\n🚫 <b>ТЕНЕВОЙ БАН</b>" if candidate.is_shadow_banned else ""
        
        profile = (
            f"👤 <b>{candidate.name}</b>, {candidate.age}\n"
            f"{city_text}{distance_text}\n"
            f"🚻 {candidate.gender}\n"
            f"💑 {candidate.target_gender}"
            f"{bio_text}{ban_text}"
        )
        
        if user_id not in current_viewing:
            current_viewing[user_id] = {}
        current_viewing[user_id]['current_candidate'] = candidate.telegram_id
        
        database.add_viewed_profile(user_id, candidate.telegram_id)
        
        keyboard = get_admin_search_keyboard() if is_admin_view else get_search_keyboard(lang)
        
        if candidate.photo_ids and len(candidate.photo_ids) > 0:
            try:
                await message.answer_photo(candidate.photo_ids[0], caption=profile, parse_mode='HTML', reply_markup=keyboard)
            except:
                await message.answer(profile, parse_mode='HTML', reply_markup=keyboard)
        else:
            await message.answer(profile, parse_mode='HTML', reply_markup=keyboard)
    
    async def show_next_candidate(message: types.Message, user_id: int, is_admin_view: bool = False):
        lang = get_lang(user_id)
        
        if is_admin_view:
            candidates = database.get_all_candidates_for_admin(user_id, limit=10)
        else:
            candidates = database.get_potential_matches(user_id, limit=10)
        
        if not candidates:
            keyboard = get_admin_keyboard() if is_admin_view else get_main_keyboard(lang)
            text = "😔 Анкет пока нет" if is_admin_view else t('no_profiles', lang)
            await message.answer(text, parse_mode='HTML', reply_markup=keyboard)
            if user_id in current_viewing:
                del current_viewing[user_id]
            return False
        
        await show_candidate(message, user_id, candidates[0], is_admin_view)
        return True
    # ========== CALLBACK HANDLERS ==========
    
    @dp.callback_query_handler(lambda c: c.data.startswith('lang_'), state='*')
    async def cb_select_language(callback_query: types.CallbackQuery, state: FSMContext):
        lang = callback_query.data.split('_')[1]
        await state.update_data(language=lang)
        
        # Если пользователь уже есть - обновляем язык
        user = database.get_user(callback_query.from_user.id)
        if user:
            database.update_user_language(callback_query.from_user.id, lang)
            await callback_query.message.answer(t('updated', lang), reply_markup=get_main_keyboard(lang))
            await state.finish()
        else:
            # Новый пользователь - продолжаем регистрацию
            await callback_query.message.answer(t('enter_name', lang), parse_mode='HTML', reply_markup=remove_keyboard())
            await RegistrationStates.waiting_for_name.set()
        
        await callback_query.answer()
    
    @dp.callback_query_handler(lambda c: c.data.startswith('respond_like_'))
    async def cb_respond_like(callback_query: types.CallbackQuery):
        target_id = int(callback_query.data.split('_')[2])
        user_id = callback_query.from_user.id
        lang = get_lang(user_id)
        
        like, is_new, is_mutual = database.add_like(user_id, target_id)
        
        if is_mutual:
            await send_mutual_like_notification(user_id, target_id)
            await callback_query.message.edit_caption(
                callback_query.message.caption + f"\n\n✅ {t('mutual_like', lang, name='', username='').split('!')[0]}!",
                parse_mode='HTML'
            )
        else:
            await callback_query.message.edit_caption(
                callback_query.message.caption + f"\n\n✅ {t('btn_like', lang)}!",
                parse_mode='HTML'
            )
        await callback_query.answer()
    
    @dp.callback_query_handler(lambda c: c.data.startswith('respond_skip_'))
    async def cb_respond_skip(callback_query: types.CallbackQuery):
        lang = get_lang(callback_query.from_user.id)
        await callback_query.message.edit_caption(
            callback_query.message.caption + f"\n\n👎 {t('btn_dislike', lang)}",
            parse_mode='HTML'
        )
        await callback_query.answer()
    # ========== ОСНОВНЫЕ КОМАНДЫ ==========
    
    @dp.message_handler(Command('start'), state='*')
    async def cmd_start(message: types.Message, state: FSMContext):
        await state.finish()
        user = database.get_user(message.from_user.id)
        
        if user:
            database.update_last_active(message.from_user.id)
            lang = user.language or 'ru'
            await message.answer(t('welcome_back', lang, name=user.name), parse_mode='HTML', reply_markup=get_main_keyboard(lang))
        else:
            await message.answer(
                "👋 <b>Привет!</b> / <b>Salom!</b> / <b>Привіт!</b> / <b>Сәлем!</b>\n\n"
                "🌐 Выбери язык / Tilni tanlang / Обери мову / Тілді таңдаңыз:",
                parse_mode='HTML',
                reply_markup=get_language_keyboard()
            )
            await RegistrationStates.waiting_for_language.set()
    
    @dp.message_handler(Command('myid'))
    async def cmd_myid(message: types.Message):
        await message.answer(f"🆔 <code>{message.from_user.id}</code>", parse_mode='HTML')
    # ========== КНОПКИ МЕНЮ ==========
    
    @dp.message_handler(lambda m: is_btn(m.text, 'btn_help', get_lang(m.from_user.id)))
    async def btn_help(message: types.Message):
        lang = get_lang(message.from_user.id)
        await message.answer(t('help_text', lang), parse_mode='HTML', reply_markup=get_main_keyboard(lang))
    
    @dp.message_handler(lambda m: is_btn(m.text, 'btn_profile', get_lang(m.from_user.id)))
    async def btn_profile(message: types.Message):
        user = database.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ /start")
            return
        
        database.update_last_active(message.from_user.id)
        lang = user.language or 'ru'
        
        profile = t('profile_text', lang,
            name=user.name,
            age=user.age,
            city=user.city or '-',
            gender=user.gender,
            target=user.target_gender
        )
        
        if user.bio:
            profile += f"\n📝 <b>О себе:</b> {user.bio}"
        
        if user.photo_ids and len(user.photo_ids) > 0:
            try:
                await message.answer_photo(user.photo_ids[0], caption=profile, parse_mode='HTML', reply_markup=get_main_keyboard(lang))
            except:
                await message.answer(profile, parse_mode='HTML', reply_markup=get_main_keyboard(lang))
        else:
            await message.answer(profile, parse_mode='HTML', reply_markup=get_main_keyboard(lang))
    
    @dp.message_handler(lambda m: is_btn(m.text, 'btn_search', get_lang(m.from_user.id)))
    async def btn_search(message: types.Message, state: FSMContext):
        user = database.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ /start")
            return
        
        database.update_last_active(message.from_user.id)
        await SearchStates.viewing.set()
        
        if not await show_next_candidate(message, message.from_user.id):
            await state.finish()
    
    @dp.message_handler(lambda m: is_btn(m.text, 'btn_likes', get_lang(m.from_user.id)))
    async def btn_likes(message: types.Message, state: FSMContext):
        user = database.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ /start")
            return
        
        database.update_last_active(message.from_user.id)
        lang = user.language or 'ru'
        likes = database.get_likes_to_user(message.from_user.id)
        
        if not likes:
            await message.answer(t('no_likes', lang), parse_mode='HTML', reply_markup=get_main_keyboard(lang))
            return
        
        await message.answer(t('likes_count', lang, count=len(likes)), parse_mode='HTML')
        await SearchStates.viewing_likes.set()
        await state.update_data(likes=likes, like_index=0)
        
        like = likes[0]
        from_user = database.get_user(like.from_user_id)
        
        if from_user:
            if message.from_user.id not in current_viewing:
                current_viewing[message.from_user.id] = {}
            current_viewing[message.from_user.id]['current_candidate'] = from_user.telegram_id
            
            city_text = f"📍 {from_user.city}" if from_user.city else ""
            bio_text = f"\n📝 {from_user.bio}" if from_user.bio else ""
            
            profile = f"{t('like_from', lang)}\n\n👤 <b>{from_user.name}</b>, {from_user.age}\n{city_text}\n🚻 {from_user.gender}{bio_text}"
            if like.message:
                profile += f"\n\n💝 {like.message}"
            
            if from_user.photo_ids and len(from_user.photo_ids) > 0:
                try:
                    await message.answer_photo(from_user.photo_ids[0], caption=profile, parse_mode='HTML', reply_markup=get_search_keyboard(lang))
                except:
                    await message.answer(profile, parse_mode='HTML', reply_markup=get_search_keyboard(lang))
            else:
                await message.answer(profile, parse_mode='HTML', reply_markup=get_search_keyboard(lang))
            
            database.mark_like_as_read(like.id)
    
    @dp.message_handler(lambda m: is_btn(m.text, 'btn_mutual', get_lang(m.from_user.id)))
    async def btn_mutual(message: types.Message):
        user = database.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ /start")
            return
        
        lang = user.language or 'ru'
        mutual = database.get_mutual_likes_for_user(message.from_user.id)
        
        if not mutual:
            await message.answer(t('no_mutual', lang), parse_mode='HTML', reply_markup=get_main_keyboard(lang))
            return
        
        text = t('mutual_title', lang)
        for like in mutual[:20]:
            other = database.get_user(like.to_user_id)
            if other:
                username = f"@{other.username}" if other.username else "(скрыт)"
                text += f"👤 <b>{other.name}</b>, {other.age} — {username}\n"
        
        await message.answer(text, parse_mode='HTML', reply_markup=get_main_keyboard(lang))
    
    @dp.message_handler(lambda m: is_btn(m.text, 'btn_edit', get_lang(m.from_user.id)))
    async def btn_edit(message: types.Message, state: FSMContext):
        user = database.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ /start")
            return
        
        lang = user.language or 'ru'
        await message.answer(t('edit_prompt', lang), parse_mode='HTML', reply_markup=get_edit_keyboard(lang))
        await EditStates.select_field.set()
    # ========== РЕДАКТИРОВАНИЕ ПРОФИЛЯ ==========
    
    @dp.message_handler(state=EditStates.select_field)
    async def edit_select_field(message: types.Message, state: FSMContext):
        lang = get_lang(message.from_user.id)
        
        if is_btn(message.text, 'btn_back', lang):
            await state.finish()
            await message.answer(t('menu', lang), parse_mode='HTML', reply_markup=get_main_keyboard(lang))
            return
        
        field_map = {
            t('edit_name', lang): 'name',
            t('edit_age', lang): 'age',
            t('edit_city', lang): 'city',
            t('edit_gender', lang): 'gender',
            t('edit_target', lang): 'target',
            t('edit_photo', lang): 'photo',
            t('edit_bio', lang): 'bio',
            t('edit_lang', lang): 'language'
        }
        
        field = field_map.get(message.text)
        
        if not field:
            await message.answer(t('error', lang))
            return
        
        await state.update_data(edit_field=field)
        
        if field == 'name':
            await message.answer(t('enter_new_name', lang), reply_markup=get_cancel_keyboard(lang))
            await EditStates.edit_name.set()
        elif field == 'age':
            await message.answer(t('enter_new_age', lang), reply_markup=get_cancel_keyboard(lang))
            await EditStates.edit_age.set()
        elif field == 'city':
            await message.answer(t('enter_new_city', lang), reply_markup=get_city_keyboard(lang))
            await EditStates.edit_city.set()
        elif field == 'gender':
            await message.answer(t('enter_gender', lang), reply_markup=get_gender_keyboard(lang))
            await EditStates.edit_gender.set()
        elif field == 'target':
            await message.answer(t('enter_target', lang), reply_markup=get_target_gender_keyboard(lang))
            await EditStates.edit_target.set()
        elif field == 'photo':
            await message.answer(t('enter_photo', lang), reply_markup=get_photo_keyboard(lang))
            user_photos[message.from_user.id] = []
            await EditStates.edit_photo.set()
        elif field == 'bio':
            await message.answer(t('enter_new_bio', lang), reply_markup=get_bio_keyboard(lang))
            await EditStates.edit_bio.set()
        elif field == 'language':
            await message.answer("🌐", reply_markup=get_language_keyboard())
            await EditStates.edit_language.set()
    
    @dp.message_handler(state=EditStates.edit_name)
    async def edit_name(message: types.Message, state: FSMContext):
        lang = get_lang(message.from_user.id)
        if is_btn(message.text, 'btn_cancel', lang):
            await state.finish()
            await message.answer(t('cancelled', lang), reply_markup=get_main_keyboard(lang))
            return
        
        name = message.text.strip()
        if len(name) < 2 or len(name) > 50:
            await message.answer(t('name_error', lang))
            return
        
        database.update_user_field(message.from_user.id, 'name', name)
        await state.finish()
        await message.answer(t('updated', lang), reply_markup=get_main_keyboard(lang))
    
    @dp.message_handler(state=EditStates.edit_age)
    async def edit_age(message: types.Message, state: FSMContext):
        lang = get_lang(message.from_user.id)
        if is_btn(message.text, 'btn_cancel', lang):
            await state.finish()
            await message.answer(t('cancelled', lang), reply_markup=get_main_keyboard(lang))
            return
        
        if not message.text.isdigit():
            await message.answer(t('age_error', lang))
            return
        
        age = int(message.text)
        if age < 16 or age > 100:
            await message.answer(t('age_error', lang))
            return
        
        database.update_user_field(message.from_user.id, 'age', age)
        await state.finish()
        await message.answer(t('updated', lang), reply_markup=get_main_keyboard(lang))
    
    @dp.message_handler(content_types=['location'], state=EditStates.edit_city)
    async def edit_city_location(message: types.Message, state: FSMContext):
        lang = get_lang(message.from_user.id)
        lat, lon = message.location.latitude, message.location.longitude
        city_name, country, _ = get_city_from_coords(lat, lon)
        
        database.update_user_field(message.from_user.id, 'city', city_name)
        database.update_user_field(message.from_user.id, 'city_normalized', city_name)
        database.update_user_field(message.from_user.id, 'country', country)
        database.update_user_field(message.from_user.id, 'latitude', lat)
        database.update_user_field(message.from_user.id, 'longitude', lon)
        
        await state.finish()
        await message.answer(t('updated', lang), reply_markup=get_main_keyboard(lang))
    
    @dp.message_handler(state=EditStates.edit_city)
    async def edit_city_text(message: types.Message, state: FSMContext):
        lang = get_lang(message.from_user.id)
        if is_btn(message.text, 'btn_cancel', lang):
            await state.finish()
            await message.answer(t('cancelled', lang), reply_markup=get_main_keyboard(lang))
            return
        
        city_normalized, country, lat, lon = normalize_city(message.text)
        
        database.update_user_field(message.from_user.id, 'city', message.text)
        database.update_user_field(message.from_user.id, 'city_normalized', city_normalized)
        database.update_user_field(message.from_user.id, 'country', country)
        if lat:
            database.update_user_field(message.from_user.id, 'latitude', lat)
        if lon:
            database.update_user_field(message.from_user.id, 'longitude', lon)
        
        await state.finish()
        await message.answer(t('updated', lang), reply_markup=get_main_keyboard(lang))
    
    @dp.message_handler(state=EditStates.edit_gender)
    async def edit_gender(message: types.Message, state: FSMContext):
        lang = get_lang(message.from_user.id)
        valid = [t('btn_male', l) for l in ['ru', 'uz', 'uk', 'kz']] + \
                [t('btn_female', l) for l in ['ru', 'uz', 'uk', 'kz']] + \
                [t('btn_other', l) for l in ['ru', 'uz', 'uk', 'kz']]
        
        if message.text not in valid:
            await message.answer(t('error', lang))
            return
        
        database.update_user_field(message.from_user.id, 'gender', message.text)
        await state.finish()
        await message.answer(t('updated', lang), reply_markup=get_main_keyboard(lang))
    
    @dp.message_handler(state=EditStates.edit_target)
    async def edit_target(message: types.Message, state: FSMContext):
        lang = get_lang(message.from_user.id)
        
        target_map = {}
        for l in ['ru', 'uz', 'uk', 'kz']:
            target_map[t('btn_search_female', l)] = 'девушек'
            target_map[t('btn_search_male', l)] = 'парней'
            target_map[t('btn_search_all', l)] = 'всех'
        
        if message.text not in target_map:
            await message.answer(t('error', lang))
            return
        
        database.update_user_field(message.from_user.id, 'target_gender', target_map[message.text])
        await state.finish()
        await message.answer(t('updated', lang), reply_markup=get_main_keyboard(lang))
    
    @dp.message_handler(content_types=['photo'], state=EditStates.edit_photo)
    async def edit_photo(message: types.Message, state: FSMContext):
        if message.from_user.id not in user_photos:
            user_photos[message.from_user.id] = []
        user_photos[message.from_user.id].append(message.photo[-1].file_id)
        
        lang = get_lang(message.from_user.id)
        await message.answer(t('photo_added', lang, count=len(user_photos[message.from_user.id])), reply_markup=get_photo_keyboard(lang))
    
    @dp.message_handler(state=EditStates.edit_photo)
    async def edit_photo_done(message: types.Message, state: FSMContext):
        lang = get_lang(message.from_user.id)
        
        if is_btn(message.text, 'btn_skip', lang):
            user_photos[message.from_user.id] = []
        elif is_btn(message.text, 'btn_done', lang):
            pass
        else:
            return
        
        photos = user_photos.get(message.from_user.id, [])
        if photos:
            database.update_user_field(message.from_user.id, 'photo_ids', photos)
        
        user_photos.pop(message.from_user.id, None)
        await state.finish()
        await message.answer(t('updated', lang), reply_markup=get_main_keyboard(lang))
    
    @dp.message_handler(state=EditStates.edit_bio)
    async def edit_bio(message: types.Message, state: FSMContext):
        lang = get_lang(message.from_user.id)
        
        if is_btn(message.text, 'btn_skip_bio', lang):
            database.update_user_field(message.from_user.id, 'bio', None)
        else:
            database.update_user_field(message.from_user.id, 'bio', message.text[:500])
        
        await state.finish()
        await message.answer(t('updated', lang), reply_markup=get_main_keyboard(lang))
    
    @dp.callback_query_handler(lambda c: c.data.startswith('lang_'), state=EditStates.edit_language)
    async def edit_language_cb(callback_query: types.CallbackQuery, state: FSMContext):
        lang = callback_query.data.split('_')[1]
        database.update_user_language(callback_query.from_user.id, lang)
        await state.finish()
        await callback_query.message.answer(t('updated', lang), reply_markup=get_main_keyboard(lang))
        await callback_query.answer()
    # ========== ПОИСК ==========
    
    @dp.message_handler(lambda m: is_btn(m.text, 'btn_like', get_lang(m.from_user.id)), state=SearchStates.viewing)
    async def search_like(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        if user_id not in current_viewing:
            await state.finish()
            return
        
        target_id = current_viewing[user_id]['current_candidate']
        like, is_new, is_mutual = database.add_like(user_id, target_id)
        
        if is_new:
            if is_mutual:
                await send_mutual_like_notification(user_id, target_id)
            else:
                await send_like_notification(target_id, user_id)
        
        if not await show_next_candidate(message, user_id):
            await state.finish()
    
    @dp.message_handler(lambda m: is_btn(m.text, 'btn_like', get_lang(m.from_user.id)), state=SearchStates.viewing_likes)
    async def likes_like(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        lang = get_lang(user_id)
        
        if user_id not in current_viewing:
            await state.finish()
            return
        
        target_id = current_viewing[user_id]['current_candidate']
        like, is_new, is_mutual = database.add_like(user_id, target_id)
        
        if is_mutual:
            await send_mutual_like_notification(user_id, target_id)
        
        # Следующий лайк
        data = await state.get_data()
        likes = data.get('likes', [])
        index = data.get('like_index', 0) + 1
        
        if index >= len(likes):
            await message.answer(t('all_viewed', lang), parse_mode='HTML', reply_markup=get_main_keyboard(lang))
            await state.finish()
            return
        
        await state.update_data(like_index=index)
        like = likes[index]
        from_user = database.get_user(like.from_user_id)
        
        if from_user:
            current_viewing[user_id]['current_candidate'] = from_user.telegram_id
            city_text = f"📍 {from_user.city}" if from_user.city else ""
            bio_text = f"\n📝 {from_user.bio}" if from_user.bio else ""
            profile = f"{t('like_from', lang)}\n\n👤 <b>{from_user.name}</b>, {from_user.age}\n{city_text}{bio_text}"
            
            if from_user.photo_ids:
                try:
                    await message.answer_photo(from_user.photo_ids[0], caption=profile, parse_mode='HTML', reply_markup=get_search_keyboard(lang))
                except:
                    await message.answer(profile, parse_mode='HTML', reply_markup=get_search_keyboard(lang))
            else:
                await message.answer(profile, parse_mode='HTML', reply_markup=get_search_keyboard(lang))
            database.mark_like_as_read(like.id)
    
    @dp.message_handler(lambda m: is_btn(m.text, 'btn_valentine', get_lang(m.from_user.id)), state=[SearchStates.viewing, SearchStates.viewing_likes])
    async def btn_valentine(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        lang = get_lang(user_id)
        
        if user_id not in current_viewing:
            await state.finish()
            return
        
        target_id = current_viewing[user_id]['current_candidate']
        current_state = await state.get_state()
        await state.update_data(valentine_to=target_id, previous_state=current_state)
        await message.answer(t('valentine_prompt', lang), parse_mode='HTML', reply_markup=get_cancel_keyboard(lang))
        await LikeStates.waiting_for_valentine.set()
    
    @dp.message_handler(lambda m: is_btn(m.text, 'btn_dislike', get_lang(m.from_user.id)), state=SearchStates.viewing)
    async def search_dislike(message: types.Message, state: FSMContext):
        if not await show_next_candidate(message, message.from_user.id):
            await state.finish()
    
    @dp.message_handler(lambda m: is_btn(m.text, 'btn_dislike', get_lang(m.from_user.id)), state=SearchStates.viewing_likes)
    async def likes_dislike(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        lang = get_lang(user_id)
        
        data = await state.get_data()
        likes = data.get('likes', [])
        index = data.get('like_index', 0) + 1
        
        if index >= len(likes):
            await message.answer(t('all_viewed', lang), parse_mode='HTML', reply_markup=get_main_keyboard(lang))
            await state.finish()
            return
        
        await state.update_data(like_index=index)
        like = likes[index]
        from_user = database.get_user(like.from_user_id)
        
        if from_user:
            current_viewing[user_id]['current_candidate'] = from_user.telegram_id
            city_text = f"📍 {from_user.city}" if from_user.city else ""
            bio_text = f"\n📝 {from_user.bio}" if from_user.bio else ""
            profile = f"{t('like_from', lang)}\n\n👤 <b>{from_user.name}</b>, {from_user.age}\n{city_text}{bio_text}"
            
            if from_user.photo_ids:
                try:
                    await message.answer_photo(from_user.photo_ids[0], caption=profile, parse_mode='HTML', reply_markup=get_search_keyboard(lang))
                except:
                    await message.answer(profile, parse_mode='HTML', reply_markup=get_search_keyboard(lang))
            else:
                await message.answer(profile, parse_mode='HTML', reply_markup=get_search_keyboard(lang))
            database.mark_like_as_read(like.id)
    
    @dp.message_handler(lambda m: is_btn(m.text, 'btn_stop', get_lang(m.from_user.id)), state=[SearchStates.viewing, SearchStates.viewing_likes])
    async def btn_stop(message: types.Message, state: FSMContext):
        lang = get_lang(message.from_user.id)
        if message.from_user.id in current_viewing:
            del current_viewing[message.from_user.id]
        await state.finish()
        await message.answer(t('menu', lang), parse_mode='HTML', reply_markup=get_main_keyboard(lang))
    
    # ========== ВАЛЕНТИНКА ==========
    
    @dp.message_handler(state=LikeStates.waiting_for_valentine)
    async def process_valentine(message: types.Message, state: FSMContext):
        lang = get_lang(message.from_user.id)
        
        if is_btn(message.text, 'btn_cancel', lang):
            data = await state.get_data()
            prev = data.get('previous_state', '')
            if 'viewing' in prev:
                await SearchStates.viewing.set()
                await message.answer(t('cancelled', lang), reply_markup=get_search_keyboard(lang))
            else:
                await state.finish()
                await message.answer(t('cancelled', lang), reply_markup=get_main_keyboard(lang))
            return
        
        data = await state.get_data()
        target_id = data.get('valentine_to')
        prev_state = data.get('previous_state', '')
        user_id = message.from_user.id
        
        like, is_new, is_mutual = database.add_like(user_id, target_id, message=message.text)
        
        if is_mutual:
            await send_mutual_like_notification(user_id, target_id)
        else:
            await message.answer(t('valentine_sent', lang), parse_mode='HTML')
            await send_like_notification(target_id, user_id, message.text)
        
        if 'viewing' in prev_state:
            await SearchStates.viewing.set()
            if not await show_next_candidate(message, user_id):
                await state.finish()
        else:
            await state.finish()
            await message.answer("👍", reply_markup=get_main_keyboard(lang))        
    # ========== РЕГИСТРАЦИЯ ==========
    
    @dp.message_handler(state=RegistrationStates.waiting_for_name)
    async def reg_name(message: types.Message, state: FSMContext):
        data = await state.get_data()
        lang = data.get('language', 'ru')
        
        name = message.text.strip()
        if len(name) < 2 or len(name) > 50:
            await message.answer(t('name_error', lang))
            return
        
        await state.update_data(name=name)
        await message.answer(t('enter_age', lang), reply_markup=remove_keyboard())
        await RegistrationStates.waiting_for_age.set()
    
    @dp.message_handler(state=RegistrationStates.waiting_for_age)
    async def reg_age(message: types.Message, state: FSMContext):
        data = await state.get_data()
        lang = data.get('language', 'ru')
        
        if not message.text.isdigit():
            await message.answer(t('age_error', lang))
            return
        
        age = int(message.text)
        if age < 16 or age > 100:
            await message.answer(t('age_error', lang))
            return
        
        await state.update_data(age=age)
        await message.answer(t('enter_city', lang), parse_mode='HTML', reply_markup=get_city_keyboard(lang))
        await RegistrationStates.waiting_for_city.set()
    
    @dp.message_handler(content_types=['location'], state=RegistrationStates.waiting_for_city)
    async def reg_city_location(message: types.Message, state: FSMContext):
        data = await state.get_data()
        lang = data.get('language', 'ru')
        
        lat, lon = message.location.latitude, message.location.longitude
        city_name, country, _ = get_city_from_coords(lat, lon)
        
        await state.update_data(city=city_name, city_normalized=city_name, country=country, latitude=lat, longitude=lon)
        await message.answer(t('enter_gender', lang), reply_markup=get_gender_keyboard(lang))
        await RegistrationStates.waiting_for_gender.set()
    
    @dp.message_handler(state=RegistrationStates.waiting_for_city)
    async def reg_city_text(message: types.Message, state: FSMContext):
        data = await state.get_data()
        lang = data.get('language', 'ru')
        
        city_input = message.text.strip()
        if len(city_input) < 2:
            await message.answer(t('error', lang))
            return
        
        city_normalized, country, lat, lon = normalize_city(city_input)
        await state.update_data(city=city_input, city_normalized=city_normalized, country=country, latitude=lat, longitude=lon)
        await message.answer(t('enter_gender', lang), reply_markup=get_gender_keyboard(lang))
        await RegistrationStates.waiting_for_gender.set()
    
    @dp.message_handler(state=RegistrationStates.waiting_for_gender)
    async def reg_gender(message: types.Message, state: FSMContext):
        data = await state.get_data()
        lang = data.get('language', 'ru')
        
        valid = [t('btn_male', l) for l in ['ru', 'uz', 'uk', 'kz']] + \
                [t('btn_female', l) for l in ['ru', 'uz', 'uk', 'kz']] + \
                [t('btn_other', l) for l in ['ru', 'uz', 'uk', 'kz']]
        
        if message.text not in valid:
            await message.answer(t('error', lang), reply_markup=get_gender_keyboard(lang))
            return
        
        await state.update_data(gender=message.text)
        await message.answer(t('enter_target', lang), reply_markup=get_target_gender_keyboard(lang))
        await RegistrationStates.waiting_for_target_gender.set()
    
    @dp.message_handler(state=RegistrationStates.waiting_for_target_gender)
    async def reg_target(message: types.Message, state: FSMContext):
        data = await state.get_data()
        lang = data.get('language', 'ru')
        
        target_map = {}
        for l in ['ru', 'uz', 'uk', 'kz']:
            target_map[t('btn_search_female', l)] = 'девушек'
            target_map[t('btn_search_male', l)] = 'парней'
            target_map[t('btn_search_all', l)] = 'всех'
        
        if message.text not in target_map:
            await message.answer(t('error', lang), reply_markup=get_target_gender_keyboard(lang))
            return
        
        await state.update_data(target_gender=target_map[message.text])
        await message.answer(t('enter_photo', lang), reply_markup=get_photo_keyboard(lang))
        user_photos[message.from_user.id] = []
        await RegistrationStates.waiting_for_photo.set()
    
    @dp.message_handler(content_types=['photo'], state=RegistrationStates.waiting_for_photo)
    async def reg_photo(message: types.Message, state: FSMContext):
        data = await state.get_data()
        lang = data.get('language', 'ru')
        
        if message.from_user.id not in user_photos:
            user_photos[message.from_user.id] = []
        user_photos[message.from_user.id].append(message.photo[-1].file_id)
        await message.answer(t('photo_added', lang, count=len(user_photos[message.from_user.id])), reply_markup=get_photo_keyboard(lang))
    
    @dp.message_handler(state=RegistrationStates.waiting_for_photo)
    async def reg_photo_done(message: types.Message, state: FSMContext):
        data = await state.get_data()
        lang = data.get('language', 'ru')
        
        if is_btn(message.text, 'btn_skip', lang):
            user_photos[message.from_user.id] = []
        elif is_btn(message.text, 'btn_done', lang):
            pass
        else:
            return
        
        await message.answer(t('enter_bio', lang), reply_markup=get_bio_keyboard(lang))
        await RegistrationStates.waiting_for_bio.set()
    
    @dp.message_handler(state=RegistrationStates.waiting_for_bio)
    async def reg_bio(message: types.Message, state: FSMContext):
        data = await state.get_data()
        lang = data.get('language', 'ru')
        
        bio = None
        if not is_btn(message.text, 'btn_skip_bio', lang):
            bio = message.text.strip()[:500]
        
        photos = user_photos.get(message.from_user.id, [])
        
        database.create_user(
            telegram_id=message.from_user.id,
            name=data['name'],
            age=data['age'],
            city=data.get('city'),
            city_normalized=data.get('city_normalized'),
            country=data.get('country'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            gender=data['gender'],
            target_gender=data['target_gender'],
            bio=bio,
            username=message.from_user.username,
            photo_ids=photos,
            language=lang
        )
        
        user_photos.pop(message.from_user.id, None)
        await state.finish()
        await message.answer(t('profile_created', lang), parse_mode='HTML', reply_markup=get_main_keyboard(lang))
    
    # ========== УДАЛЕНИЕ ==========
    
    @dp.message_handler(Command('delete'))
    async def cmd_delete(message: types.Message):
        user = database.get_user(message.from_user.id)
        if not user:
            await message.answer("❌")
            return
        lang = user.language or 'ru'
        await message.answer(t('confirm_delete', lang), parse_mode='HTML', reply_markup=get_yes_no_keyboard("del_profile"))
    
    @dp.callback_query_handler(lambda c: c.data.startswith('del_profile_'))
    async def cb_delete(callback_query: types.CallbackQuery):
        lang = get_lang(callback_query.from_user.id)
        if callback_query.data.split('_')[2] == "yes":
            database.delete_user(callback_query.from_user.id)
            await callback_query.message.answer(t('deleted', lang))
        else:
            await callback_query.message.answer(t('saved', lang), reply_markup=get_main_keyboard(lang))
        await callback_query.answer()
    # ========== АДМИН ==========
    
    @dp.message_handler(Command('admin'))
    async def cmd_admin(message: types.Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            return
        await state.finish()
        await message.answer("⚙️ <b>Админ-панель</b>", parse_mode='HTML', reply_markup=get_admin_keyboard())
    
    @dp.message_handler(lambda m: m.text == "◀️ На главную")
    async def admin_back_main(message: types.Message, state: FSMContext):
        await state.finish()
        lang = get_lang(message.from_user.id)
        await message.answer(t('menu', lang), parse_mode='HTML', reply_markup=get_main_keyboard(lang))
    
    @dp.message_handler(lambda m: m.text == "📊 Статистика")
    async def admin_stats(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        s = database.get_admin_stats()
        await message.answer(
            f"📊 <b>Статистика</b>\n\n"
            f"👥 Пользователей: {s['total_users']}\n"
            f"🤖 Бот-анкет: {s['bot_profiles']}\n"
            f"🚫 Забанено: {s['shadow_banned']}\n"
            f"💌 Лайков: {s['total_likes']}\n"
            f"💕 Мэтчей: {s['mutual_likes']}\n"
            f"📨 Шаблонов: {s['templates']}",
            parse_mode='HTML', reply_markup=get_admin_keyboard()
        )
    
    @dp.message_handler(lambda m: m.text == "👥 Пользователи")
    async def admin_users(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        users = database.get_all_users(limit=20, include_bots=False)
        if not users:
            await message.answer("📭 Пусто", reply_markup=get_admin_keyboard())
            return
        text = "👥 <b>Пользователи:</b>\n\n"
        for u in users:
            ban = "🚫" if u.is_shadow_banned else ""
            lang_flag = {'ru': '🇷🇺', 'uz': '🇺🇿', 'uk': '🇺🇦', 'kz': '🇰🇿'}.get(u.language, '🌐')
            text += f"{ban}{lang_flag} <b>{u.name}</b>, {u.age} | {u.city or '?'} (<code>{u.telegram_id}</code>)\n"
        text += "\n💡 Введите ID в «🔍 Поиск» для просмотра"
        await message.answer(text, parse_mode='HTML', reply_markup=get_admin_keyboard())
    
    @dp.message_handler(lambda m: m.text == "🔍 Поиск")
    async def admin_search(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        await message.answer(
            "🔍 <b>Поиск</b>\n\nВведите ID, имя или @username:",
            parse_mode='HTML', reply_markup=get_cancel_keyboard('ru')
        )
        await AdminStates.waiting_for_search_term.set()
    
    async def show_user_profile_admin(message: types.Message, user):
        """Показать полную анкету для админа"""
        city_text = f"📍 {user.city}" if user.city else "📍 Не указан"
        bio_text = f"\n📝 {user.bio}" if user.bio else ""
        username_text = f"@{user.username}" if user.username else "(нет)"
        lang_flag = {'ru': '🇷🇺', 'uz': '🇺🇿', 'uk': '🇺🇦', 'kz': '🇰🇿'}.get(user.language, '🌐')
        
        ban_status = ""
        if user.is_shadow_banned:
            ban_status = f"\n\n🚫 <b>ТЕНЕВОЙ БАН</b>"
            if user.shadow_ban_reason:
                ban_status += f"\n↳ {user.shadow_ban_reason}"
        
        bot_mark = "🤖 " if user.is_bot_profile else ""
        
        profile = (
            f"{bot_mark}<b>Анкета</b>\n\n"
            f"🆔 <code>{user.telegram_id}</code>\n"
            f"👤 <b>{user.name}</b>, {user.age}\n"
            f"{city_text}\n"
            f"🌍 {user.country or '?'}\n"
            f"🚻 {user.gender}\n"
            f"💑 Ищет: {user.target_gender}\n"
            f"📱 {username_text}\n"
            f"{lang_flag} Язык: {user.language or 'ru'}"
            f"{bio_text}{ban_status}"
        )
        
        keyboard = get_user_actions_keyboard(user.telegram_id, user.is_bot_profile)
        
        if user.photo_ids and len(user.photo_ids) > 0:
            try:
                await message.answer_photo(user.photo_ids[0], caption=profile, parse_mode='HTML', reply_markup=keyboard)
            except:
                await message.answer(profile, parse_mode='HTML', reply_markup=keyboard)
        else:
            await message.answer(profile, parse_mode='HTML', reply_markup=keyboard)
    
    @dp.message_handler(state=AdminStates.waiting_for_search_term)
    async def admin_search_process(message: types.Message, state: FSMContext):
        if message.text == "❌ Отмена":
            await state.finish()
            await message.answer("❌", reply_markup=get_admin_keyboard())
            return
        
        search_text = message.text.strip()
        
        # Проверяем ID
        try:
            user_id = int(search_text)
            user = database.get_user(user_id)
            if user:
                await state.finish()
                await show_user_profile_admin(message, user)
                return
            else:
                await message.answer(f"❌ ID <code>{user_id}</code> не найден", parse_mode='HTML')
                await state.finish()
                await message.answer("⚙️", reply_markup=get_admin_keyboard())
                return
        except ValueError:
            pass
        
        # Ищем по имени/username
        users = database.search_users(search_text, 10)
        
        if not users:
            await message.answer("🔍 Не найдено", reply_markup=get_admin_keyboard())
            await state.finish()
            return
        
        if len(users) == 1:
            await state.finish()
            await show_user_profile_admin(message, users[0])
            return
        
        text = "🔍 <b>Найдено:</b>\n\n"
        for u in users:
            ban = "🚫" if u.is_shadow_banned else ""
            bot = "🤖" if u.is_bot_profile else ""
            text += f"{ban}{bot}<b>{u.name}</b> (<code>{u.telegram_id}</code>)\n"
        text += "\n💡 Введите ID"
        await message.answer(text, parse_mode='HTML')
    
    # ========== CALLBACK ДЛЯ АДМИНА ==========
    
    @dp.callback_query_handler(lambda c: c.data.startswith('edit_username_'))
    async def cb_edit_username(callback_query: types.CallbackQuery, state: FSMContext):
        if not is_admin(callback_query.from_user.id):
            await callback_query.answer("❌")
            return
        
        user_id = int(callback_query.data.split('_')[2])
        await state.update_data(edit_user_id=user_id)
        await callback_query.message.answer(
            "✏️ <b>Введите username</b> (с @ или без)\nИли «⏭️ Пропустить» чтобы удалить",
            parse_mode='HTML', reply_markup=get_skip_keyboard('ru')
        )
        await AdminStates.edit_username.set()
        await callback_query.answer()
    
    @dp.message_handler(state=AdminStates.edit_username)
    async def process_edit_username(message: types.Message, state: FSMContext):
        if message.text == "❌ Отмена":
            await state.finish()
            await message.answer("❌", reply_markup=get_admin_keyboard())
            return
        
        data = await state.get_data()
        user_id = data.get('edit_user_id')
        
        new_username = None if message.text == "⏭️ Пропустить" else message.text.strip().lstrip('@')
        
        if database.update_user_username(user_id, new_username):
            await message.answer(f"✅ Username: @{new_username}" if new_username else "✅ Username удалён", reply_markup=get_admin_keyboard())
        else:
            await message.answer("❌ Ошибка", reply_markup=get_admin_keyboard())
        
        await state.finish()
    
    @dp.callback_query_handler(lambda c: c.data.startswith('ban_user_'))
    async def cb_ban_user(callback_query: types.CallbackQuery):
        if not is_admin(callback_query.from_user.id):
            return
        user_id = int(callback_query.data.split('_')[2])
        database.apply_shadow_ban(user_id, "Ручной бан")
        await callback_query.message.answer(f"🚫 <code>{user_id}</code> забанен", parse_mode='HTML')
        await callback_query.answer("🚫")
    
    @dp.callback_query_handler(lambda c: c.data.startswith('unban_user_'))
    async def cb_unban_user(callback_query: types.CallbackQuery):
        if not is_admin(callback_query.from_user.id):
            return
        user_id = int(callback_query.data.split('_')[2])
        database.remove_shadow_ban(user_id)
        await callback_query.message.answer(f"✅ <code>{user_id}</code> разбанен", parse_mode='HTML')
        await callback_query.answer("✅")
    
    @dp.callback_query_handler(lambda c: c.data.startswith('delete_user_'))
    async def cb_delete_user(callback_query: types.CallbackQuery):
        if not is_admin(callback_query.from_user.id):
            return
        user_id = int(callback_query.data.split('_')[2])
        user = database.get_user(user_id)
        if user:
            await callback_query.message.answer(
                f"⚠️ Удалить <b>{user.name}</b>?",
                parse_mode='HTML', reply_markup=get_yes_no_keyboard("confirm_del", user_id)
            )
        await callback_query.answer()
    
    @dp.callback_query_handler(lambda c: c.data.startswith('confirm_del_'))
    async def cb_confirm_delete(callback_query: types.CallbackQuery):
        if not is_admin(callback_query.from_user.id):
            return
        parts = callback_query.data.split('_')
        if parts[2] == "yes":
            database.delete_user(int(parts[3]))
            await callback_query.message.answer("✅ Удалено", reply_markup=get_admin_keyboard())
        else:
            await callback_query.message.answer("❌", reply_markup=get_admin_keyboard())
        await callback_query.answer()
    
    # ========== ПРОСМОТР АНКЕТ АДМИНОМ ==========
    
    @dp.message_handler(lambda m: m.text == "👁️ Смотреть анкеты")
    async def admin_view(message: types.Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            return
        await AdminStates.admin_viewing.set()
        if not await show_next_candidate(message, message.from_user.id, is_admin_view=True):
            await state.finish()
    
    @dp.message_handler(lambda m: m.text == "❤️ Лайк", state=AdminStates.admin_viewing)
    async def admin_like(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        if user_id in current_viewing:
            target_id = current_viewing[user_id]['current_candidate']
            database.add_like(user_id, target_id)
        if not await show_next_candidate(message, user_id, is_admin_view=True):
            await state.finish()
    
    @dp.message_handler(lambda m: m.text == "👎 Дизлайк", state=AdminStates.admin_viewing)
    async def admin_dislike(message: types.Message, state: FSMContext):
        if not await show_next_candidate(message, message.from_user.id, is_admin_view=True):
            await state.finish()
    
    @dp.message_handler(lambda m: m.text == "🚫 Теневой бан", state=AdminStates.admin_viewing)
    async def admin_ban_current(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        if user_id in current_viewing:
            target_id = current_viewing[user_id]['current_candidate']
            database.apply_shadow_ban(target_id, "Ручной бан")
            await message.answer(f"🚫 <code>{target_id}</code> забанен", parse_mode='HTML')
        if not await show_next_candidate(message, user_id, is_admin_view=True):
            await state.finish()
    
    @dp.message_handler(lambda m: m.text == "🛑 Выход", state=AdminStates.admin_viewing)
    async def admin_exit_view(message: types.Message, state: FSMContext):
        await state.finish()
        await message.answer("⚙️", reply_markup=get_admin_keyboard())
    
    # ========== ТЕНЕВЫЕ БАНЫ ==========
    
    @dp.message_handler(lambda m: m.text == "🚫 Теневые баны")
    async def admin_bans(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        users = database.get_shadow_banned_users()
        if not users:
            await message.answer("🚫 Нет забаненных", reply_markup=get_admin_keyboard())
            return
        text = "🚫 <b>Забаненные:</b>\n\n"
        for u in users:
            text += f"<b>{u.name}</b> (<code>{u.telegram_id}</code>)\n"
            if u.shadow_ban_reason:
                text += f"   ↳ {u.shadow_ban_reason}\n"
        text += "\n💡 Введите ID в «🔍 Поиск» для разбана"
        await message.answer(text, parse_mode='HTML', reply_markup=get_admin_keyboard())
    
    # ========== КЛЮЧЕВЫЕ СЛОВА ==========
    
    @dp.message_handler(lambda m: m.text == "📝 Ключевые слова")
    async def admin_keywords(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        keywords = database.get_banned_keywords()
        text = "📝 <b>Ключевые слова для бана:</b>\n\n"
        text += "\n".join([f"• {kw}" for kw in keywords]) if keywords else "(пусто)"
        text += "\n\n/addkw [слово] — добавить\n/delkw [слово] — удалить"
        await message.answer(text, parse_mode='HTML', reply_markup=get_admin_keyboard())
    
    @dp.message_handler(Command('addkw'))
    async def cmd_addkw(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("❌ /addkw [слово]")
            return
        if database.add_banned_keyword(parts[1]):
            await message.answer(f"✅ «{parts[1]}» добавлено")
        else:
            await message.answer(f"❌ Уже есть")
    
    @dp.message_handler(Command('delkw'))
    async def cmd_delkw(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("❌ /delkw [слово]")
            return
        if database.remove_banned_keyword(parts[1]):
            await message.answer(f"✅ «{parts[1]}» удалено")
        else:
            await message.answer(f"❌ Не найдено")
    
    # ========== УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ ==========
    
    @dp.message_handler(lambda m: m.text == "🗑️ Удалить")
    async def admin_delete_start(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        await message.answer("🗑️ Введите ID:", reply_markup=get_cancel_keyboard('ru'))
        await AdminStates.waiting_for_delete_id.set()
    
    @dp.message_handler(state=AdminStates.waiting_for_delete_id)
    async def admin_delete_process(message: types.Message, state: FSMContext):
        if message.text == "❌ Отмена":
            await state.finish()
            await message.answer("❌", reply_markup=get_admin_keyboard())
            return
        try:
            tid = int(message.text)
            user = database.get_user(tid)
            if user:
                await state.finish()
                await show_user_profile_admin(message, user)
            else:
                await message.answer("❌ Не найден", reply_markup=get_admin_keyboard())
                await state.finish()
        except:
            await message.answer("❌ Введите число")
    # ========== РАССЫЛКА ==========
    
    @dp.message_handler(lambda m: m.text == "📨 Рассылка")
    async def admin_broadcast_menu(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        await message.answer(
            "📨 <b>Рассылка</b>\n\n"
            "📝 <b>Новая рассылка</b> — создать и отправить\n"
            "📋 <b>Шаблоны</b> — сохранённые шаблоны",
            parse_mode='HTML', reply_markup=get_broadcast_keyboard()
        )
    
    @dp.message_handler(lambda m: m.text == "◀️ Назад")
    async def broadcast_back(message: types.Message, state: FSMContext):
        await state.finish()
        if is_admin(message.from_user.id):
            await message.answer("⚙️", reply_markup=get_admin_keyboard())
    
    @dp.message_handler(lambda m: m.text == "📝 Новая рассылка")
    async def broadcast_new(message: types.Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            return
        await message.answer(
            "📝 <b>Создание рассылки</b>\n\n"
            "Введите текст на <b>русском</b> 🇷🇺:\n\n"
            "<i>Поддерживается HTML разметка</i>",
            parse_mode='HTML', reply_markup=get_cancel_keyboard('ru')
        )
        await state.update_data(broadcast_texts={})
        await AdminStates.broadcast_text_ru.set()
    
    @dp.message_handler(state=AdminStates.broadcast_text_ru)
    async def broadcast_text_ru(message: types.Message, state: FSMContext):
        if message.text == "❌ Отмена":
            await state.finish()
            await message.answer("❌", reply_markup=get_admin_keyboard())
            return
        
        data = await state.get_data()
        texts = data.get('broadcast_texts', {})
        texts['ru'] = message.text
        await state.update_data(broadcast_texts=texts)
        
        await message.answer(
            "Введите текст на <b>узбекском</b> 🇺🇿:\n\n"
            "Или «⏭️ Пропустить» для пропуска",
            parse_mode='HTML', reply_markup=get_skip_keyboard('ru')
        )
        await AdminStates.broadcast_text_uz.set()
    
    @dp.message_handler(state=AdminStates.broadcast_text_uz)
    async def broadcast_text_uz(message: types.Message, state: FSMContext):
        if message.text == "❌ Отмена":
            await state.finish()
            await message.answer("❌", reply_markup=get_admin_keyboard())
            return
        
        data = await state.get_data()
        texts = data.get('broadcast_texts', {})
        
        if message.text != "⏭️ Пропустить":
            texts['uz'] = message.text
        await state.update_data(broadcast_texts=texts)
        
        await message.answer(
            "Введите текст на <b>украинском</b> 🇺🇦:\n\n"
            "Или «⏭️ Пропустить»",
            parse_mode='HTML', reply_markup=get_skip_keyboard('ru')
        )
        await AdminStates.broadcast_text_uk.set()
    
    @dp.message_handler(state=AdminStates.broadcast_text_uk)
    async def broadcast_text_uk(message: types.Message, state: FSMContext):
        if message.text == "❌ Отмена":
            await state.finish()
            await message.answer("❌", reply_markup=get_admin_keyboard())
            return
        
        data = await state.get_data()
        texts = data.get('broadcast_texts', {})
        
        if message.text != "⏭️ Пропустить":
            texts['uk'] = message.text
        await state.update_data(broadcast_texts=texts)
        
        await message.answer(
            "Введите текст на <b>казахском</b> 🇰🇿:\n\n"
            "Или «⏭️ Пропустить»",
            parse_mode='HTML', reply_markup=get_skip_keyboard('ru')
        )
        await AdminStates.broadcast_text_kz.set()
    
    @dp.message_handler(state=AdminStates.broadcast_text_kz)
    async def broadcast_text_kz(message: types.Message, state: FSMContext):
        if message.text == "❌ Отмена":
            await state.finish()
            await message.answer("❌", reply_markup=get_admin_keyboard())
            return
        
        data = await state.get_data()
        texts = data.get('broadcast_texts', {})
        
        if message.text != "⏭️ Пропустить":
            texts['kz'] = message.text
        await state.update_data(broadcast_texts=texts)
        
        await message.answer(
            "📛 <b>Название шаблона</b>\n\n"
            "Введите название для сохранения или «⏭️ Пропустить» чтобы отправить без сохранения:",
            parse_mode='HTML', reply_markup=get_skip_keyboard('ru')
        )
        await AdminStates.broadcast_name.set()
    
    @dp.message_handler(state=AdminStates.broadcast_name)
    async def broadcast_name(message: types.Message, state: FSMContext):
        if message.text == "❌ Отмена":
            await state.finish()
            await message.answer("❌", reply_markup=get_admin_keyboard())
            return
        
        data = await state.get_data()
        texts = data.get('broadcast_texts', {})
        
        template_name = None if message.text == "⏭️ Пропустить" else message.text
        
        # Сохраняем шаблон если указано имя
        if template_name:
            database.create_broadcast_template(
                name=template_name,
                text_ru=texts.get('ru', ''),
                text_uz=texts.get('uz'),
                text_uk=texts.get('uk'),
                text_kz=texts.get('kz')
            )
            await message.answer(f"💾 Шаблон «{template_name}» сохранён")
        
        # Показываем превью
        preview = f"📨 <b>Превью рассылки:</b>\n\n🇷🇺: {texts.get('ru', '-')[:100]}..."
        if texts.get('uz'):
            preview += f"\n\n🇺🇿: {texts['uz'][:100]}..."
        if texts.get('uk'):
            preview += f"\n\n🇺🇦: {texts['uk'][:100]}..."
        if texts.get('kz'):
            preview += f"\n\n🇰🇿: {texts['kz'][:100]}..."
        
        users = database.get_all_active_users_for_broadcast()
        preview += f"\n\n👥 Получателей: {len(users)}"
        
        await state.update_data(broadcast_texts=texts)
        await message.answer(preview, parse_mode='HTML', reply_markup=get_yes_no_keyboard("broadcast_send"))
        await AdminStates.broadcast_confirm.set()
    
    @dp.callback_query_handler(lambda c: c.data.startswith('broadcast_send_'), state=AdminStates.broadcast_confirm)
    async def broadcast_confirm(callback_query: types.CallbackQuery, state: FSMContext):
        if callback_query.data == "broadcast_send_no":
            await state.finish()
            await callback_query.message.answer("❌ Отменено", reply_markup=get_admin_keyboard())
            await callback_query.answer()
            return
        
        data = await state.get_data()
        texts = data.get('broadcast_texts', {})
        
        await callback_query.message.answer("📨 Начинаю рассылку...")
        
        users = database.get_all_active_users_for_broadcast()
        success = 0
        failed = 0
        
        for user in users:
            user_lang = user.language or 'ru'
            text = texts.get(user_lang) or texts.get('ru', '')
            
            if not text:
                continue
            
            try:
                await bot.send_message(user.telegram_id, text, parse_mode='HTML')
                success += 1
                await asyncio.sleep(0.05)  # Защита от флуда
            except Exception as e:
                failed += 1
                logger.error(f"Ошибка рассылки {user.telegram_id}: {e}")
        
        await state.finish()
        await callback_query.message.answer(
            f"✅ <b>Рассылка завершена</b>\n\n"
            f"✅ Успешно: {success}\n"
            f"❌ Ошибок: {failed}",
            parse_mode='HTML', reply_markup=get_admin_keyboard()
        )
        await callback_query.answer()
    
    # ========== ШАБЛОНЫ ==========
    
    @dp.message_handler(lambda m: m.text == "📋 Шаблоны")
    async def broadcast_templates(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        
        templates = database.get_broadcast_templates()
        
        if not templates:
            await message.answer("📋 Нет сохранённых шаблонов", reply_markup=get_broadcast_keyboard())
            return
        
        await message.answer("📋 <b>Шаблоны:</b>\n\nВыберите для отправки:", 
                            parse_mode='HTML', reply_markup=get_template_keyboard(templates))
    
    @dp.callback_query_handler(lambda c: c.data.startswith('tpl_send_'))
    async def send_template(callback_query: types.CallbackQuery):
        if not is_admin(callback_query.from_user.id):
            return
        
        tpl_id = int(callback_query.data.split('_')[2])
        template = database.get_broadcast_template(tpl_id)
        
        if not template:
            await callback_query.answer("❌ Шаблон не найден")
            return
        
        await callback_query.message.answer(
            f"📄 <b>{template.name}</b>\n\n"
            f"🇷🇺: {template.text_ru[:100]}...\n\n"
            f"Отправить?",
            parse_mode='HTML',
            reply_markup=get_yes_no_keyboard("tpl_confirm", tpl_id)
        )
        await callback_query.answer()
    
    @dp.callback_query_handler(lambda c: c.data.startswith('tpl_confirm_'))
    async def confirm_template(callback_query: types.CallbackQuery):
        if not is_admin(callback_query.from_user.id):
            return
        
        parts = callback_query.data.split('_')
        decision = parts[2]
        
        if decision == "no":
            await callback_query.message.answer("❌", reply_markup=get_admin_keyboard())
            await callback_query.answer()
            return
        
        tpl_id = int(parts[3])
        template = database.get_broadcast_template(tpl_id)
        
        if not template:
            await callback_query.answer("❌")
            return
        
        await callback_query.message.answer("📨 Начинаю рассылку...")
        
        users = database.get_all_active_users_for_broadcast()
        success = 0
        failed = 0
        
        texts = {
            'ru': template.text_ru,
            'uz': template.text_uz,
            'uk': template.text_uk,
            'kz': template.text_kz
        }
        
        for user in users:
            user_lang = user.language or 'ru'
            text = texts.get(user_lang) or texts.get('ru', '')
            
            if not text:
                continue
            
            try:
                await bot.send_message(user.telegram_id, text, parse_mode='HTML')
                success += 1
                await asyncio.sleep(0.05)
            except:
                failed += 1
        
        await callback_query.message.answer(
            f"✅ <b>Рассылка завершена</b>\n\n✅ {success} | ❌ {failed}",
            parse_mode='HTML', reply_markup=get_admin_keyboard()
        )
        await callback_query.answer()
    
    @dp.callback_query_handler(lambda c: c.data == "tpl_back")
    async def tpl_back(callback_query: types.CallbackQuery):
        await callback_query.message.answer("📨", reply_markup=get_broadcast_keyboard())
        await callback_query.answer()
    # ========== СОЗДАНИЕ БОТ-АНКЕТЫ ==========
    
    @dp.message_handler(lambda m: m.text == "➕ Создать анкету")
    async def admin_create(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        await message.answer("➕ <b>Имя:</b>", parse_mode='HTML', reply_markup=get_cancel_keyboard('ru'))
        admin_photos[message.from_user.id] = []
        await AdminStates.create_name.set()
    
    @dp.message_handler(state=AdminStates.create_name)
    async def create_name(message: types.Message, state: FSMContext):
        if message.text == "❌ Отмена":
            await state.finish()
            await message.answer("❌", reply_markup=get_admin_keyboard())
            return
        await state.update_data(name=message.text)
        await message.answer("Возраст:", reply_markup=remove_keyboard())
        await AdminStates.create_age.set()
    
    @dp.message_handler(state=AdminStates.create_age)
    async def create_age(message: types.Message, state: FSMContext):
        if message.text == "❌ Отмена":
            await state.finish()
            await message.answer("❌", reply_markup=get_admin_keyboard())
            return
        if not message.text.isdigit():
            await message.answer("❌ Число!")
            return
        await state.update_data(age=int(message.text))
        await message.answer("📍 Город:", reply_markup=get_city_keyboard('ru'))
        await AdminStates.create_city.set()
    
    @dp.message_handler(content_types=['location'], state=AdminStates.create_city)
    async def create_city_loc(message: types.Message, state: FSMContext):
        lat, lon = message.location.latitude, message.location.longitude
        city_name, country, _ = get_city_from_coords(lat, lon)
        await state.update_data(city=city_name, city_normalized=city_name, country=country, latitude=lat, longitude=lon)
        await message.answer("Пол:", reply_markup=get_gender_keyboard('ru'))
        await AdminStates.create_gender.set()
    
    @dp.message_handler(state=AdminStates.create_city)
    async def create_city_text(message: types.Message, state: FSMContext):
        if message.text == "❌ Отмена":
            await state.finish()
            await message.answer("❌", reply_markup=get_admin_keyboard())
            return
        city_normalized, country, lat, lon = normalize_city(message.text)
        await state.update_data(city=message.text, city_normalized=city_normalized, country=country, latitude=lat, longitude=lon)
        await message.answer("Пол:", reply_markup=get_gender_keyboard('ru'))
        await AdminStates.create_gender.set()
    
    @dp.message_handler(state=AdminStates.create_gender)
    async def create_gender(message: types.Message, state: FSMContext):
        if message.text not in ["👨 Мужской", "👩 Женский", "🤷 Другое"]:
            return
        await state.update_data(gender=message.text)
        await message.answer("Кого ищет:", reply_markup=get_target_gender_keyboard('ru'))
        await AdminStates.create_target.set()
    
    @dp.message_handler(state=AdminStates.create_target)
    async def create_target(message: types.Message, state: FSMContext):
        target_map = {"👩 Девушек": "девушек", "👨 Парней": "парней", "👫 Не важно": "всех"}
        if message.text not in target_map:
            return
        await state.update_data(target_gender=target_map[message.text])
        await message.answer("📸 Фото:", reply_markup=get_skip_photo_keyboard())
        await AdminStates.create_photo.set()
    
    @dp.message_handler(content_types=['photo'], state=AdminStates.create_photo)
    async def create_photo(message: types.Message, state: FSMContext):
        if message.from_user.id not in admin_photos:
            admin_photos[message.from_user.id] = []
        admin_photos[message.from_user.id].append(message.photo[-1].file_id)
        await message.answer(f"📸 ({len(admin_photos[message.from_user.id])})", reply_markup=get_skip_photo_keyboard())
    
    @dp.message_handler(state=AdminStates.create_photo)
    async def create_photo_done(message: types.Message, state: FSMContext):
        if message.text == "❌ Отмена":
            await state.finish()
            admin_photos.pop(message.from_user.id, None)
            await message.answer("❌", reply_markup=get_admin_keyboard())
            return
        if message.text == "⏭️ Без фото":
            admin_photos[message.from_user.id] = []
        elif message.text != "✅ Готово":
            return
        await message.answer("📝 Описание (или «📝 Без описания»):", reply_markup=get_bio_keyboard('ru'))
        await AdminStates.create_bio.set()
    
    @dp.message_handler(state=AdminStates.create_bio)
    async def create_bio(message: types.Message, state: FSMContext):
        if message.text == "❌ Отмена":
            await state.finish()
            admin_photos.pop(message.from_user.id, None)
            await message.answer("❌", reply_markup=get_admin_keyboard())
            return
        
        bio = None if message.text == "📝 Без описания" else message.text
        await state.update_data(bio=bio)
        await message.answer("📱 Username (с @ или без, или «⏭️ Пропустить»):", reply_markup=get_skip_keyboard('ru'))
        await AdminStates.create_username.set()
    
    @dp.message_handler(state=AdminStates.create_username)
    async def create_username(message: types.Message, state: FSMContext):
        if message.text == "❌ Отмена":
            await state.finish()
            admin_photos.pop(message.from_user.id, None)
            await message.answer("❌", reply_markup=get_admin_keyboard())
            return
        
        username = None if message.text == "⏭️ Пропустить" else message.text.lstrip('@')
        
        data = await state.get_data()
        photos = admin_photos.get(message.from_user.id, [])
        
        new_id = database.create_bot_profile(
            name=data['name'],
            age=data['age'],
            city=data.get('city'),
            city_normalized=data.get('city_normalized'),
            country=data.get('country'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            gender=data['gender'],
            target_gender=data['target_gender'],
            bio=data.get('bio'),
            photo_ids=photos,
            username=username
        )
        
        admin_photos.pop(message.from_user.id, None)
        await state.finish()
        
        username_text = f"@{username}" if username else "(нет)"
        await message.answer(
            f"✅ <b>Создано!</b>\n\n"
            f"👤 {data['name']}, {data['age']}\n"
            f"📍 {data.get('city_normalized', '?')}\n"
            f"📱 {username_text}\n"
            f"🆔 <code>{new_id}</code>",
            parse_mode='HTML', reply_markup=get_admin_keyboard()
        )
    
    @dp.message_handler(lambda m: m.text == "🤖 Мои анкеты")
    async def admin_bots(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        profiles = database.get_bot_profiles()
        if not profiles:
            await message.answer("🤖 Пусто", reply_markup=get_admin_keyboard())
            return
        text = "🤖 <b>Бот-анкеты:</b>\n\n"
        for p in profiles:
            username = f"@{p.username}" if p.username else "(нет)"
            text += f"• <b>{p.name}</b>, {p.age} | {p.city or '?'}\n  {username} (<code>{p.telegram_id}</code>)\n\n"
        text += "💡 ID в «🔍 Поиск» для редактирования"
        await message.answer(text, parse_mode='HTML', reply_markup=get_admin_keyboard())
    
    # ========== ЗАПУСК ==========
    
    try:
        logger.info("🤖 Бот запущен!")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling()
    except Exception as e:
        logger.error(f"❌ {e}")
    finally:
        await dp.storage.close()
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())