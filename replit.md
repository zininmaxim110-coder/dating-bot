# Telegram Dating Bot

## Overview
A feature-rich Telegram dating/matchmaking bot built with Python using the aiogram framework. The bot enables users to create profiles, browse other users, like/dislike profiles, and get notified about mutual matches.

## Current State
✅ **Fully functional** - Bot is running and connected to PostgreSQL database

## Features
- **User Profiles**: Create profiles with photos, bio, age, location, gender preferences
- **Matching System**: Browse potential matches with like/dislike functionality
- **Mutual Matches**: Get notified when both users like each other
- **Multi-language Support**: Russian, Uzbek, Ukrainian, Kazakh
- **Location-based**: City and geolocation support with distance calculation
- **Admin Panel**: Manage users, bot profiles, and shadow bans
- **Valentine Messages**: Send messages with likes
- **Profile Editing**: Users can edit all aspects of their profiles

## Recent Changes
- **December 7, 2025**: Project imported to Replit
  - Configured PostgreSQL database connection
  - Set up BOT_TOKEN and ADMIN_ID secrets
  - Configured workflow to run bot

## Project Architecture

### Tech Stack
- **Language**: Python 3.10
- **Framework**: aiogram (Telegram Bot framework)
- **Database**: PostgreSQL (Replit managed)
- **ORM**: SQLAlchemy

### Key Files
- `main.py` - Main bot logic and handlers (1737 lines)
- `config.py` - Configuration and environment variable loading
- `database.py` - Database models and functions
- `translations.py` - Multi-language support
- `states.py` - FSM states for conversation flows
- `keyboards.py` - Telegram keyboard layouts
- `geo_utils.py` - Location and distance utilities

### Database Schema
Users table with fields:
- Profile info: name, age, bio, gender, target_gender
- Location: city, city_normalized, country, latitude, longitude
- Photos: photo_ids (array)
- Metadata: telegram_id, username, language, is_bot_profile, is_shadow_banned
- Timestamps: created_at, last_active

Likes table:
- Tracks likes between users
- Supports mutual match detection
- Optional valentine message

### Bot Commands
- `/start` - Start bot and register/login
- `/myid` - Get your Telegram ID

### Environment Variables
- `BOT_TOKEN` (secret) - Telegram bot token from @BotFather
- `ADMIN_ID` (secret) - Telegram ID of the admin user
- `DATABASE_URL` (auto-configured) - PostgreSQL connection string

## How to Use

### For Users
1. Start the bot with `/start`
2. Select your language
3. Fill out your profile (name, age, city, gender, preferences)
4. Upload photos (optional)
5. Start browsing profiles
6. Like/dislike profiles
7. Get notified about mutual matches

### For Admin
- Admin panel accessible to user with ADMIN_ID
- Manage user profiles
- Create bot profiles for testing
- Shadow ban users
- Broadcast messages

## Running the Bot
The bot runs automatically via the "Run Telegram Bot" workflow:
```bash
python main.py
```

The bot uses long polling to receive updates from Telegram.

## Development Notes
- Bot state is managed with aiogram FSM (Finite State Machine)
- All user interactions are localized based on user language preference
- Photos are stored as Telegram file IDs (no local storage needed)
- Distance calculations use Haversine formula for geo-matching
- Shadow ban feature hides users from search without notification

## User Preferences
None specified yet.
