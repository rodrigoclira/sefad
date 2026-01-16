# CSV Import Instructions

## Overview
This guide explains how to import course and discipline data from the CSV file into the database.

## Prerequisites
- Docker and docker-compose installed
- CSV file at: `data/matriz_curricular_ads.csv`

## Steps to Import Data

### 1. Start the Docker containers
```bash
docker-compose up -d
```

### 2. Run migrations to update the database schema
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### 3. Import the CSV data
```bash
docker-compose exec web python manage.py import_csv /app/../data/matriz_curricular_ads.csv
```

Or if you want to clear existing data first:
```bash
docker-compose exec web python manage.py import_csv /app/../data/matriz_curricular_ads.csv --clear
```

### 4. Verify the import
You can access the Django admin interface to verify the imported data:
- URL: http://localhost:8000/admin/
- Create a superuser if needed:
  ```bash
  docker-compose exec web python manage.py createsuperuser
  ```

## CSV Format

The CSV file should have the following columns:
- `nome_curso`: Course name
- `ano_perfil`: Grade year (e.g., 2019.2)
- `modulo`: Module/semester number
- `disciplina`: Discipline name
- `creditos`: Credits
- `ch_aula`: Classroom hours
- `ch_relogio`: Clock hours
- `pre_requisito`: Prerequisite (optional)
- `co_requisito`: Co-requisite (optional)

## What the Import Does

1. **Creates Courses**: One course per unique combination of `nome_curso` and `ano_perfil`
2. **Creates Disciplines**: All disciplines from the CSV with the following mappings:
   - `modulo` → `period` (semester)
   - `creditos` → `credits`
   - `ch_aula` → `ch_aula`
   - `ch_relogio` → `ch_relogio`
   - `pre_requisito` → `pre_requisito`
   - `co_requisito` → `co_requisito`
   - `main_area` is automatically inferred from the discipline name:
     - "computação" for CS-related disciplines
     - "other" for all others

## Notes

- The import uses `update_or_create` for disciplines, so running it multiple times won't create duplicates
- All disciplines with CS-related keywords will be assigned to "computação" area
- You can refine the `main_area` field later through the Django admin interface
