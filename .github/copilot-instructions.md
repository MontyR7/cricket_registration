# Copilot Instructions for cricket_registration

## Project Overview
This is a Python/Flask-based web application for managing cricket event registrations, player profiles, payments, and asset generation. The codebase is organized for modularity and extensibility, with clear separation between data models, routes, utilities, and asset management scripts.

## Architecture & Major Components
- **app.py**: Main Flask app entry point. Imports routes and extensions.
- **models.py**: SQLAlchemy models for players, payments, and related entities.
- **routes.py**: Defines all HTTP endpoints for registration, payment, admin, and asset access.
- **forms.py**: WTForms definitions for user input validation.
- **extensions.py**: Flask extensions setup (DB, login, etc.).
- **templates/**: Jinja2 HTML templates for all user/admin views.
- **static/**: Static assets (images, JS, generated player cards).
- **Player_Event_Assets/**: Stores generated player assets and summaries.
- **migrations/**: Alembic migration scripts for DB schema changes.

## Developer Workflows
- **Database Setup**: Use `init_mysql.py` and `setup_mysql.py` for DB initialization. Alembic migrations in `migrations/`.
- **Asset Generation**: Run `card_generator.py` and `create_player_assets.py` to generate player cards and event assets.
- **Testing**: Use `test_card_generator.py` and `test_card_generation.py` for asset generation tests. No standard test runner; run scripts directly.
- **Running the App**: Use `run_with_public_url.py` or `app.py` to start the Flask server. For public access, use ngrok or similar.

## Project-Specific Patterns
- **Player Data Storage**: Player details and assets are stored in nested folders under `Player_Event_Assets/` and `static/player_cards/` by role and player name.
- **Payment Handling**: Payment screenshots and UPI details are managed via forms and stored in the DB; see `payment_handlers.py`.
- **Admin Views**: Templates under `templates/admin/` provide admin dashboard, login, and player detail views.
- **Profile Defaults**: Use `create_default_profile.py` to generate default player profiles.

## Integration Points
- **MySQL**: All persistent data is stored in MySQL, configured via `init_mysql.py` and `setup_mysql.py`.
- **Alembic**: DB migrations managed in `migrations/`.
- **WTForms**: Used for all form validation in `forms.py`.
- **Static/Generated Assets**: Player cards and event assets are generated and served from `static/player_cards/` and `Player_Event_Assets/`.

## Conventions
- **File Naming**: Scripts are named for their purpose (e.g., `card_generator.py`, `check_players.py`).
- **Directory Structure**: Assets and player data are organized by role and player name for easy lookup.
- **No Centralized Test Runner**: Tests are script-based; run them individually.

## Examples
- To generate player cards: `python card_generator.py`
- To initialize the database: `python init_mysql.py`
- To run the app: `python app.py` or `python run_with_public_url.py`

## Key Files & Directories
- `app.py`, `routes.py`, `models.py`, `forms.py`, `extensions.py`
- `templates/`, `static/`, `Player_Event_Assets/`, `migrations/`

---

For questions or unclear conventions, review the above files or ask for clarification. Update this file as new workflows or patterns emerge.