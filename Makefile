# Define the default target
.DEFAULT_GOAL := help

# Define variables
VENV := venv
REQUIREMENTS := requirements.txt
PYTHON := python3.11
PIP := $(VENV)/bin/pip
DJANGO_MANAGE := $(VENV)/bin/python manage.py
ENV_FILE := .env

# Ensure the virtual environment is created
$(VENV)/:
	$(PYTHON) -m venv $(VENV)

# Install dependencies
install: $(VENV)/
	@echo "Activating virtual environment and installing dependencies..."
	@source $(VENV)/bin/activate && $(PIP) install -r $(REQUIREMENTS)

# Delete the virtual environment
clean:
	rm -rf $(VENV)

# create the virtual environment and install dependencies
setup: clean install

create_env_file:
	@echo "Creating .env file with default values..."
	@echo "THRESHOLD=5000" > $(ENV_FILE)
	@echo "THRESHOLD_DAYS=2" >> $(ENV_FILE)

# Start the Django development server with environment variables loaded from .env
start: $(VENV)/
	@echo "Checking if .env file exists..."
	@if [ ! -f "$(ENV_FILE)" ]; then \
		make create_env_file; \
	fi
	@echo "Loading environment variables from $(ENV_FILE)"
	@source $(ENV_FILE) && $(DJANGO_MANAGE) runserver

# Create superuser with a specific password
create_superuser:
	@echo "Creating superuser with password 12345678..."
	@source $(ENV_FILE) && $(DJANGO_MANAGE) migrate
	@source $(ENV_FILE) && echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', '12345678')" | $(DJANGO_MANAGE) shell


# Help target to display available commands
help:
	@echo "Available targets:"
	@echo "  install       - Create virtual environment and install requirements"
	@echo "  clean         - Delete virtual environment"
	@echo "  setup         - Creating virtual environment and install requirements"
	@echo "  start         - Start Django development server"
	@echo "  create_superuser  - Create superuser with password 12345678"
	@echo "  help          - Display this help message"
