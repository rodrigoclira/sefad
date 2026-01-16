#!/bin/bash
# This script verifies the Django project setup is correct

echo "Verifying Django project setup..."
echo "=================================="
echo ""

# Check Python files syntax
echo "1. Checking Python files syntax..."
python -m py_compile sefad/sefad/settings.py sefad/sefad/urls.py sefad/sefad/wsgi.py sefad/manage.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ All Python files are syntactically correct"
else
    echo "✗ Python syntax errors found"
    exit 1
fi

# Check Docker Compose configuration
echo ""
echo "2. Checking docker-compose.yml syntax..."
docker compose config --quiet 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ docker-compose.yml is valid"
else
    echo "✗ docker-compose.yml has errors"
    exit 1
fi

# Check required files
echo ""
echo "3. Checking required files..."
required_files=(
    "sefad/Dockerfile"
    "docker-compose.yml"
    "sefad/.dockerignore"
    ".env.example"
    "sefad/requirements.txt"
    "sefad/manage.py"
    "sefad/sefad/settings.py"
    "sefad/sefad/urls.py"
    "sefad/sefad/wsgi.py"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file is missing"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = false ]; then
    exit 1
fi

echo ""
echo "=================================="
echo "✓ All checks passed!"
echo ""
echo "To run the Django project with Docker Compose:"
echo "1. Run: docker-compose up --build"
echo "2. Access the application at: http://localhost:8000"
echo ""
echo "For more information, see README.md"
