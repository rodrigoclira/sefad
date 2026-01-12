# SEFAD
SEFAD - Sistema de Estimativa de Força Acadêmica Docente

## Description
System for estimating academic teaching strength built with Django and PostgreSQL.

## Prerequisites
- Docker
- Docker Compose

## Environment Configuration

The project supports two environment modes:
- **dev**: Uses SQLite database (no PostgreSQL required)
- **prod**: Uses PostgreSQL database (default in Docker Compose)

Set the `ENVIRONMENT` variable in your `.env` file to switch between modes.

## Setup

### Quick Verification

Before running the project, you can verify that all files are correctly set up:
```bash
./verify-setup.sh
```

This script will check:
- Python file syntax
- Docker Compose configuration validity
- Presence of all required files

### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/rodrigoclira/sefad.git
cd sefad
```

2. (Optional) Create a `.env` file from the example:
```bash
cp .env.example .env
```
Edit the `.env` file with your custom configurations if needed.

**For development with SQLite:**
- Set `ENVIRONMENT=dev` in your `.env` file
- No database container needed

**For production with PostgreSQL:**
- Set `ENVIRONMENT=prod` in your `.env` file (or remove it, prod is default)
- Configure database credentials if needed

3. Build and run the containers:
```bash
docker-compose up --build
```

The application will be available at `http://localhost:8000`

## Usage

### Running the application
```bash
docker-compose up
```

### Stopping the application
```bash
docker-compose down
```

### Running Django management commands
```bash
# Create a superuser
docker-compose exec web python manage.py createsuperuser

# Make migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic
```

### Accessing the database
```bash
docker-compose exec db psql -U sefad -d sefad
```

### Viewing logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs web
docker-compose logs db
```

## Development

### Running locally without Docker (Development Mode)

For local development using SQLite:

1. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Create a `.env` file:
```bash
cp .env.example .env
```
Ensure `ENVIRONMENT=dev` is set in the `.env` file.

3. Run migrations and start the development server:
```bash
python manage.py migrate
python manage.py runserver
```

The application will be available at `http://localhost:8000`

### Running with Docker (Production Mode)

To run the application in production mode with Docker Compose:

```bash
docker-compose up --build
```

Or to run with Django's development server inside Docker:
```bash
docker-compose run --rm --service-ports web python manage.py runserver 0.0.0.0:8000
```

## Project Structure
```
sefad/
├── sefad/              # Django project settings
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py     # Project settings
│   ├── urls.py         # URL configuration
│   └── wsgi.py
├── manage.py           # Django management script
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker image configuration
├── docker-compose.yml  # Docker Compose configuration
├── .dockerignore       # Docker ignore file
├── .env.example        # Environment variables example
└── README.md           # This file
```

## License
This project is open source and available under the [MIT License](LICENSE).

