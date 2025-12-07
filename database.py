from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
import json
import logging
import math

from geo_utils import calculate_distance
from config import DATABASE_URL  # Импортируем URL из конфига

logger = logging.getLogger(__name__)

# Настройка движка в зависимости от типа БД
if DATABASE_URL.startswith("sqlite"):
    # SQLite - для локальной разработки
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
else:
    # PostgreSQL - для Railway
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True  # Проверяет соединение перед использованием
    )

Base = declarative_base()
Session = sessionmaker(bind=engine)
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String(100))
    name = Column(String(100))
    age = Column(Integer)
    gender = Column(String(20))
    target_gender = Column(String(20), default='всех')
    city = Column(String(100))
    city_normalized = Column(String(100))
    country = Column(String(100))  # Страна
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    bio = Column(Text, nullable=True)
    photo_ids = Column(Text, default='[]')
    language = Column(String(10), default='ru')  # Язык пользователя
    created_at = Column(String(50), default=lambda: str(datetime.now()))
    last_active = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)
    is_bot_profile = Column(Boolean, default=False)
    is_shadow_banned = Column(Boolean, default=False)
    shadow_ban_reason = Column(Text, nullable=True)

class Like(Base):
    __tablename__ = 'likes'
    
    id = Column(Integer, primary_key=True)
    from_user_id = Column(Integer)
    to_user_id = Column(Integer)
    message = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    is_mutual = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

class ViewedProfile(Base):
    __tablename__ = 'viewed_profiles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    viewed_user_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)

class BannedKeyword(Base):
    __tablename__ = 'banned_keywords'
    
    id = Column(Integer, primary_key=True)
    keyword = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.now)

class BroadcastTemplate(Base):
    """Шаблоны рассылки"""
    __tablename__ = 'broadcast_templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    text_ru = Column(Text)
    text_uz = Column(Text, nullable=True)
    text_uk = Column(Text, nullable=True)
    text_kz = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ База данных создана")
    except Exception as e:
        print(f"❌ Ошибка создания БД: {e}")

init_db()

# ========== ШАБЛОНЫ РАССЫЛКИ ==========

def create_broadcast_template(name: str, text_ru: str, text_uz: str = None, 
                               text_uk: str = None, text_kz: str = None) -> int:
    session = Session()
    template = BroadcastTemplate(
        name=name, text_ru=text_ru, text_uz=text_uz, text_uk=text_uk, text_kz=text_kz
    )
    session.add(template)
    session.commit()
    tid = template.id
    session.close()
    return tid

def get_broadcast_templates():
    session = Session()
    templates = session.query(BroadcastTemplate).order_by(BroadcastTemplate.created_at.desc()).all()
    session.close()
    return templates

def get_broadcast_template(template_id: int):
    session = Session()
    template = session.query(BroadcastTemplate).filter_by(id=template_id).first()
    session.close()
    return template

def delete_broadcast_template(template_id: int):
    session = Session()
    template = session.query(BroadcastTemplate).filter_by(id=template_id).first()
    if template:
        session.delete(template)
        session.commit()
        session.close()
        return True
    session.close()
    return False

def get_all_active_users_for_broadcast():
    """Получить всех активных пользователей для рассылки"""
    session = Session()
    users = session.query(User).filter(
        User.is_active == True,
        User.is_bot_profile == False,
        User.telegram_id > 0
    ).all()
    session.close()
    return users

# ========== КЛЮЧЕВЫЕ СЛОВА ==========

def add_banned_keyword(keyword: str) -> bool:
    session = Session()
    try:
        existing = session.query(BannedKeyword).filter_by(keyword=keyword.lower()).first()
        if existing:
            session.close()
            return False
        kw = BannedKeyword(keyword=keyword.lower())
        session.add(kw)
        session.commit()
        session.close()
        return True
    except:
        session.close()
        return False

def remove_banned_keyword(keyword: str) -> bool:
    session = Session()
    kw = session.query(BannedKeyword).filter_by(keyword=keyword.lower()).first()
    if kw:
        session.delete(kw)
        session.commit()
        session.close()
        return True
    session.close()
    return False

def get_banned_keywords() -> list:
    session = Session()
    keywords = session.query(BannedKeyword).all()
    result = [kw.keyword for kw in keywords]
    session.close()
    return result

def check_for_banned_keywords(text: str) -> str:
    if not text:
        return None
    keywords = get_banned_keywords()
    text_lower = text.lower()
    for keyword in keywords:
        if keyword in text_lower:
            return keyword
    return None

def apply_shadow_ban(telegram_id: int, reason: str = None):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.is_shadow_banned = True
        user.shadow_ban_reason = reason
        session.commit()
    session.close()

def remove_shadow_ban(telegram_id: int):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.is_shadow_banned = False
        user.shadow_ban_reason = None
        session.commit()
    session.close()

def get_shadow_banned_users():
    session = Session()
    users = session.query(User).filter_by(is_shadow_banned=True).all()
    session.close()
    for u in users:
        if u.photo_ids:
            try:
                u.photo_ids = json.loads(u.photo_ids)
            except:
                u.photo_ids = []
    return users

# ========== ПОЛЬЗОВАТЕЛИ ==========

def create_user(telegram_id: int, name: str, age: int, gender: str, target_gender: str, 
                city: str, city_normalized: str, country: str = None, bio: str = None, 
                username: str = None, photo_ids: list = None, is_bot_profile: bool = False,
                latitude: float = None, longitude: float = None, language: str = 'ru'):
    
    text_to_check = f"{name} {bio or ''}"
    banned_word = check_for_banned_keywords(text_to_check)
    
    user = add_user(telegram_id, name, age, gender, bio, username, photo_ids, 
                    target_gender, is_bot_profile, city, city_normalized, latitude, longitude, language, country)
    
    if banned_word:
        apply_shadow_ban(telegram_id, f"Ключевое слово: {banned_word}")
    
    return user

def add_user(telegram_id: int, name: str, age: int, gender: str, bio: str = None, 
             username: str = None, photo_ids: list = None, target_gender: str = 'всех', 
             is_bot_profile: bool = False, city: str = None, city_normalized: str = None,
             latitude: float = None, longitude: float = None, language: str = 'ru', country: str = None):
    session = Session()
    
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    
    if user:
        user.name = name
        user.age = age
        user.gender = gender
        user.target_gender = target_gender
        user.city = city
        user.city_normalized = city_normalized
        user.country = country
        user.bio = bio
        user.username = username
        user.language = language
        user.last_active = datetime.now()
        user.is_bot_profile = is_bot_profile
        if latitude:
            user.latitude = latitude
        if longitude:
            user.longitude = longitude
        if photo_ids is not None:
            user.photo_ids = json.dumps(photo_ids)
    else:
        user = User(
            telegram_id=telegram_id,
            username=username,
            name=name,
            age=age,
            gender=gender,
            target_gender=target_gender,
            city=city,
            city_normalized=city_normalized,
            country=country,
            latitude=latitude,
            longitude=longitude,
            bio=bio,
            language=language,
            photo_ids=json.dumps(photo_ids or []),
            is_bot_profile=is_bot_profile
        )
        session.add(user)
    
    session.commit()
    session.close()
    return user

def create_bot_profile(name: str, age: int, gender: str, target_gender: str, 
                       city: str, city_normalized: str, country: str = None, bio: str = None, 
                       photo_ids: list = None, latitude: float = None, 
                       longitude: float = None, username: str = None):
    session = Session()
    
    last_bot = session.query(User).filter(User.telegram_id < 0).order_by(User.telegram_id.asc()).first()
    new_id = (last_bot.telegram_id - 1) if last_bot else -1
    
    if username and username.startswith('@'):
        username = username[1:]
    
    user = User(
        telegram_id=new_id,
        username=username,
        name=name,
        age=age,
        gender=gender,
        target_gender=target_gender,
        city=city,
        city_normalized=city_normalized,
        country=country,
        latitude=latitude,
        longitude=longitude,
        bio=bio,
        photo_ids=json.dumps(photo_ids or []),
        is_bot_profile=True,
        is_active=True
    )
    session.add(user)
    session.commit()
    
    result_id = user.telegram_id
    session.close()
    return result_id

def get_user(telegram_id: int):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    session.close()
    
    if user and user.photo_ids:
        try:
            user.photo_ids = json.loads(user.photo_ids)
        except:
            user.photo_ids = []
    
    return user

def get_user_language(telegram_id: int) -> str:
    user = get_user(telegram_id)
    return user.language if user else 'ru'

def update_user_language(telegram_id: int, language: str):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.language = language
        session.commit()
    session.close()

def update_user_field(telegram_id: int, field: str, value):
    """Обновить одно поле пользователя"""
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user and hasattr(user, field):
        if field == 'photo_ids' and isinstance(value, list):
            value = json.dumps(value)
        setattr(user, field, value)
        user.last_active = datetime.now()
        session.commit()
        session.close()
        return True
    session.close()
    return False

def update_user_username(telegram_id: int, username: str):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        if username and username.startswith('@'):
            username = username[1:]
        user.username = username
        session.commit()
        result = True
    else:
        result = False
    session.close()
    return result

def update_last_active(telegram_id: int):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.last_active = datetime.now()
        session.commit()
    session.close()

def delete_user(telegram_id: int):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    
    if user:
        session.query(Like).filter(
            (Like.from_user_id == telegram_id) | (Like.to_user_id == telegram_id)
        ).delete()
        session.query(ViewedProfile).filter(
            (ViewedProfile.user_id == telegram_id) | (ViewedProfile.viewed_user_id == telegram_id)
        ).delete()
        session.delete(user)
        session.commit()
        result = True
    else:
        result = False
    
    session.close()
    return result

def search_users(search_term: str, limit: int = 10):
    session = Session()
    pattern = f"%{search_term}%"
    users = session.query(User).filter(
        (User.name.ilike(pattern)) | 
        (User.username.ilike(pattern)) |
        (User.city.ilike(pattern))
    ).limit(limit).all()
    session.close()
    
    for u in users:
        if u.photo_ids:
            try:
                u.photo_ids = json.loads(u.photo_ids)
            except:
                u.photo_ids = []
    return users

def get_bot_profiles():
    session = Session()
    users = session.query(User).filter_by(is_bot_profile=True).order_by(User.created_at.desc()).all()
    session.close()
    
    for u in users:
        if u.photo_ids:
            try:
                u.photo_ids = json.loads(u.photo_ids)
            except:
                u.photo_ids = []
    return users

# ========== ПРОСМОТРЕННЫЕ ==========

def add_viewed_profile(user_id: int, viewed_user_id: int):
    session = Session()
    existing = session.query(ViewedProfile).filter_by(
        user_id=user_id, viewed_user_id=viewed_user_id
    ).first()
    if not existing:
        viewed = ViewedProfile(user_id=user_id, viewed_user_id=viewed_user_id)
        session.add(viewed)
        session.commit()
    session.close()

def get_viewed_ids(user_id: int) -> list:
    session = Session()
    viewed = session.query(ViewedProfile).filter_by(user_id=user_id).all()
    ids = [v.viewed_user_id for v in viewed]
    session.close()
    return ids

def clear_viewed_profiles(user_id: int):
    session = Session()
    session.query(ViewedProfile).filter_by(user_id=user_id).delete()
    session.commit()
    session.close()

# ========== ЛАЙКИ ==========

def add_like(from_user_id: int, to_user_id: int, message: str = None):
    session = Session()
    
    existing = session.query(Like).filter_by(
        from_user_id=from_user_id, to_user_id=to_user_id
    ).first()
    
    if existing:
        session.close()
        return existing, False, existing.is_mutual
    
    like = Like(from_user_id=from_user_id, to_user_id=to_user_id, message=message)
    session.add(like)
    
    mutual = session.query(Like).filter_by(
        from_user_id=to_user_id, to_user_id=from_user_id
    ).first()
    
    is_mutual = False
    if mutual:
        like.is_mutual = True
        mutual.is_mutual = True
        is_mutual = True
    
    session.commit()
    session.close()
    return like, True, is_mutual

def get_likes_to_user(user_id: int, unread_only: bool = False):
    session = Session()
    query = session.query(Like).filter_by(to_user_id=user_id)
    if unread_only:
        query = query.filter_by(is_read=False)
    likes = query.order_by(Like.created_at.desc()).all()
    session.close()
    return likes

def get_mutual_likes_for_user(user_id: int):
    session = Session()
    likes = session.query(Like).filter_by(
        from_user_id=user_id, is_mutual=True
    ).order_by(Like.created_at.desc()).all()
    session.close()
    return likes

def mark_like_as_read(like_id: int):
    session = Session()
    like = session.query(Like).filter_by(id=like_id).first()
    if like:
        like.is_read = True
        session.commit()
    session.close()

def get_mutual_likes(user1_id: int, user2_id: int):
    session = Session()
    like1 = session.query(Like).filter_by(from_user_id=user1_id, to_user_id=user2_id).first()
    like2 = session.query(Like).filter_by(from_user_id=user2_id, to_user_id=user1_id).first()
    session.close()
    return like1 and like2

# ========== ПОИСК ==========

def get_potential_matches(user_id: int, limit: int = 10, allow_repeats: bool = True):
    """Получить кандидатов с учётом возраста, города, страны.
    
    Приоритет:
    1. Не лайкнутые, не просмотренные
    2. Не лайкнутые, но просмотренные  
    3. ВСЕ кандидаты (включая лайкнутых) - полный сброс цикла
    """
    session = Session()
    user = session.query(User).filter_by(telegram_id=user_id).first()
    
    if not user:
        session.close()
        return []
    
    # Получаем ID лайкнутых и просмотренных
    liked_ids = set(like.to_user_id for like in session.query(Like).filter_by(from_user_id=user_id).all())
    viewed_ids = set(get_viewed_ids(user_id))
    
    # Базовый запрос - БЕЗ исключения лайкнутых!
    query = session.query(User).filter(
        User.telegram_id != user_id,
        User.is_active == True,
        User.is_shadow_banned == False
    )
    
    # Фильтр по полу
    if user.target_gender == 'девушек':
        query = query.filter(User.gender.in_(['👩 Женский', 'Женский', 'женский', '👩 Ayol', '👩 Жіноча', '👩 Әйел']))
    elif user.target_gender == 'парней':
        query = query.filter(User.gender.in_(['👨 Мужской', 'Мужской', 'мужской', '👨 Erkak', '👨 Чоловіча', '👨 Ер']))
    
    # Фильтр по стране (если указана)
    if user.country:
        query = query.filter(User.country == user.country)
    
    all_candidates = query.all()
    session.close()
    
    if not all_candidates:
        return []
    
    # Сортируем по расстоянию и возрасту
    for candidate in all_candidates:
        score = 0
        
        # Расстояние
        if user.latitude and user.longitude and candidate.latitude and candidate.longitude:
            dist = calculate_distance(user.latitude, user.longitude, candidate.latitude, candidate.longitude)
            candidate._distance = dist
            score += dist
        elif user.city_normalized and candidate.city_normalized:
            if user.city_normalized.lower() == candidate.city_normalized.lower():
                candidate._distance = 0
            else:
                candidate._distance = 500
                score += 500
        else:
            candidate._distance = 1000
            score += 1000
        
        # Разница в возрасте
        age_diff = abs(user.age - candidate.age) if user.age and candidate.age else 10
        score += age_diff * 10
        
        candidate._score = score
    
    all_candidates.sort(key=lambda x: x._score)
    
    # === ЛОГИКА ПРИОРИТЕТОВ ===
    
    # 1. Нелайкнутые и непросмотренные (лучший вариант)
    fresh = [c for c in all_candidates 
             if c.telegram_id not in liked_ids and c.telegram_id not in viewed_ids]
    
    if fresh:
        result = fresh[:limit]
    elif allow_repeats:
        # 2. Нелайкнутые, но просмотренные
        not_liked = [c for c in all_candidates if c.telegram_id not in liked_ids]
        
        if not_liked:
            # Сбрасываем просмотры и показываем нелайкнутых заново
            clear_viewed_profiles(user_id)
            result = not_liked[:limit]
        else:
            # 3. ВСЕ закончились - показываем всех включая лайкнутых!
            clear_viewed_profiles(user_id)
            logger.info(f"♻️ Пользователь {user_id}: полный сброс, показываем всех включая лайкнутых")
            result = all_candidates[:limit]
    else:
        result = []
    
    # Парсим photo_ids
    for u in result:
        if u.photo_ids:
            try:
                u.photo_ids = json.loads(u.photo_ids)
            except:
                u.photo_ids = []
    
    return result

def get_all_candidates_for_admin(admin_id: int, limit: int = 10):
    session = Session()
    
    liked_ids = [like.to_user_id for like in session.query(Like).filter_by(from_user_id=admin_id).all()]
    viewed_ids = get_viewed_ids(admin_id)
    
    query = session.query(User).filter(
        User.telegram_id != admin_id,
        User.is_active == True,
        User.is_bot_profile == False
    )
    
    if liked_ids:
        query = query.filter(User.telegram_id.notin_(liked_ids))
    
    all_candidates = query.order_by(User.last_active.desc()).all()
    session.close()
    
    not_viewed = [c for c in all_candidates if c.telegram_id not in viewed_ids]
    
    if not_viewed:
        result = not_viewed[:limit]
    else:
        clear_viewed_profiles(admin_id)
        result = all_candidates[:limit]
    
    for u in result:
        if u.photo_ids:
            try:
                u.photo_ids = json.loads(u.photo_ids)
            except:
                u.photo_ids = []
    
    return result

# ========== СТАТИСТИКА ==========

def get_admin_stats():
    session = Session()
    stats = {}
    
    try:
        stats['total_users'] = session.query(User).filter_by(is_bot_profile=False).count()
        stats['bot_profiles'] = session.query(User).filter_by(is_bot_profile=True).count()
        stats['shadow_banned'] = session.query(User).filter_by(is_shadow_banned=True).count()
        
        today = datetime.now().date()
        stats['active_today'] = session.query(User).filter(
            User.last_active >= datetime.combine(today, datetime.min.time()),
            User.is_bot_profile == False
        ).count()
        
        stats['total_likes'] = session.query(Like).count()
        stats['mutual_likes'] = session.query(Like).filter_by(is_mutual=True).count() // 2
        stats['templates'] = session.query(BroadcastTemplate).count()
            
    except Exception as e:
        logger.error(f"Ошибка статистики: {e}")
        stats = {'total_users': 0, 'bot_profiles': 0, 'shadow_banned': 0, 'active_today': 0, 
                 'total_likes': 0, 'mutual_likes': 0, 'templates': 0}
    
    session.close()
    return stats

def get_all_users(limit: int = None, include_bots: bool = True):
    session = Session()
    query = session.query(User).order_by(User.created_at.desc())
    if not include_bots:
        query = query.filter_by(is_bot_profile=False)
    users = query.limit(limit).all() if limit else query.all()
    session.close()
    
    for u in users:
        if u.photo_ids:
            try:
                u.photo_ids = json.loads(u.photo_ids)
            except:
                u.photo_ids = []
    return users

def delete_all_data():
    session = Session()
    session.query(Like).delete()
    session.query(ViewedProfile).delete()
    session.query(User).delete()
    session.query(BannedKeyword).delete()
    session.query(BroadcastTemplate).delete()
    session.commit()
    session.close()