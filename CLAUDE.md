# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

General Walarus is a Discord bot built with py-cord (discord.py fork) that provides chat moderation, user statistics tracking, voice channel management, and AI-powered interactions. The bot is deployed on Google Cloud Platform using Cloud Build CI/CD and runs in a Docker container on a Compute Engine VM.

## Development Commands

### Running the Bot Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot (requires environment variables)
python run.py
```

### Docker Commands

```bash
# Build Docker image
docker build -t general-walarus:latest .

# Run in Docker (see docker_run.sh for required environment variables)
./docker_run.sh
```

### Deployment

The bot uses a two-stage CI/CD pipeline on Google Cloud Platform:

1. **Build stage** (`ci/build.yaml`): Builds and pushes Docker image to Artifact Registry
2. **Deploy stage** (`ci/deploy.yaml`): SSHs into Compute Engine VM and deploys the container

To trigger a build and deployment:
```bash
./test_cloudbuild.sh
```

## Required Environment Variables

- `BOT_TOKEN`: Discord bot token
- `DB_CONN_STRING`: MongoDB connection string
- `ARCHIVE_DATE_ID`: MongoDB document ID for archive scheduling
- `OPENAI_API_KEY`: OpenAI API key for LLM features
- `OPENAI_ASST_ID`: OpenAI Assistant ID
- `OPENAI_MODEL`: OpenAI model to use (e.g., gpt-4o-mini)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to GCP service account key for Vision API
- `CMD_PREFIX`: Command prefix for bot commands (default: `+`)
- `ENV_NAME`: Environment name (production/development)

## Architecture

### Core Structure

The bot follows a cog-based architecture where functionality is organized into separate modules:

- **run.py**: Entry point that initializes the bot, sets up intents, loads cogs, and starts the bot
- **globals.py**: Global state management for active servers, voice connections, elections, and WSE sessions
- **utilities.py**: Shared utilities for logging, message sending, and timezone handling

### Cogs (Command/Event Handlers)

Located in `cogs/`:

- **EventsCog**: Core event handlers (on_ready, on_message, on_guild_join/remove, on_voice_state_update). Handles bot lifecycle, AI responses when mentioned, NSFW content filtering, and user statistics tracking
- **ArchiveCog**: Scheduled channel archiving functionality
- **ElectionCog**: Server election management
- **MiscellaneousCog**: Miscellaneous commands
- **StatisticsCog**: User statistics and leaderboard commands
- **VoiceCog**: Voice channel management and audio playback
- **WSECog**: "Walarus Stock Exchange" game mechanics
- **OpenAICog**: Additional OpenAI integrations (currently disabled in run.py)

### AI Components (`ai/`)

- **LLMEngine**: OpenAI Assistant API wrapper for conversational responses when the bot is mentioned
- **VisionEngine**: Google Cloud Vision API wrapper for NSFW image detection and auto-moderation

### Models (`models/`)

Data classes representing runtime state:
- **Server**: Server-specific configuration
- **VCConnection**: Voice channel connection state
- **Election**: Active election state
- **WSESession**: Active Walarus Stock Exchange game session
- **TimeSpan**: Time range utilities

### Database Layer (`database/`)

MongoDB integration using pymongo. Each file provides functions for a specific domain:

- **db_servers.py**: Server configuration (shuffle settings, archive categories, WSE status, timeout roles)
- **db_user_stats.py**: User statistics (messages sent, mentions, voice time tracking)
- **db_archive.py**: Archive scheduling and management
- **db_wse.py**: Walarus Stock Exchange data (prices, transactions)
- **db_globals.py**: Database connection initialization

All database functions accept Discord guild/user objects and handle MongoDB operations internally.

### State Management

Global state is managed through dictionaries in `globals.py`:
- `servers`: Maps Guild -> Server configuration
- `vc_connections`: Maps Guild -> VCConnection for active voice sessions
- `elections`: Maps Guild -> Election for active votes
- `live_wse_sessions`: Maps Guild -> WSESession for active stock exchange games

These are initialized in EventsCog.on_ready() and maintained throughout the bot's lifecycle.

### Key Patterns

1. **Database Operations**: All database operations go through the `database/` module. Functions accept Discord objects (Guild, Member, User) and handle serialization internally.

2. **User Statistics Tracking**: EventsCog.on_message() and EventsCog.on_voice_state_update() automatically track user activity (messages sent, mentions received, voice time) to the database.

3. **Voice Time Tracking**: Complex logic in EventsCog.db_update_voice() tracks voice channel time, only counting time when 2+ non-bot users are present. Uses vc_timer flag to determine if time should be tracked.

4. **LLM Integration**: When the bot is mentioned in a message, EventsCog.on_message() uses LLMEngine to generate a contextual response using OpenAI's Assistant API with a persistent conversation thread.

5. **NSFW Moderation**: VisionEngine checks images for NSFW content and automatically deletes/reblurs inappropriate images.

6. **WSE Game Mechanic**: When a tracked user joins the server during an active WSE session, the stock price crashes to 0 (see EventsCog.on_member_join()).

## Dependencies

Key dependencies (see requirements.txt):
- `py-cord[voice]`: Discord API wrapper with voice support
- `pymongo`: MongoDB driver
- `openai`: OpenAI API client
- `google-cloud-vision`: GCP Vision API for image analysis
- `apscheduler`: Task scheduling for archive automation
- `pydub` + `ffmpeg`: Audio processing for voice features
- `matplotlib`: Chart generation for statistics
