# YouTube Organizer Backend

This is a Django project using Django Rest Framework, ready for Dockerization. No frontend or database config is included yet.

## Structure

- `youtube_organizer/` - Django project root
- `organizer/` - Basic app for future endpoints
- `requirements.txt` - Python dependencies

## Setup

1. Create a virtual environment and install requirements:
   ```sh
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run the server:
   ```sh
   python manage.py runserver
   ```

## Next Steps

- Add database configuration
- Implement API endpoints in `organizer` app
- Add Docker support
