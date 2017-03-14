# Street Maintenance API

Django-based REST API for Turku area street maintenance vehicle data.

## Requirements

* Python 3.x
* PostgreSQL + PostGIS

## Development

### Install required system packages

#### PostgreSQL

    # Ubuntu 16.04
    sudo apt-get install python3-dev libpq-dev postgresql postgis
    
#### GeoDjango extra packages

    # Ubuntu 16.04
    sudo apt-get install binutils libproj-dev gdal-bin

### Creating a virtualenv

Using a virtual environment for Python is *highly* recommended.

There are a couple of options for that:

- Using Python `venv` module:

  Creating the virtual env:
     
      sudo apt-get install python3-venv
      python3 -m venv <path to new virtual environment>

  Activating the virtual env:

      source <path to new virtual environment>/bin/activate
 
- Using [virtualenv](https://virtualenv.pypa.io/en/stable/) tool and the great [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/):

  Creating the virtual env:

      sudo apt-get install virtualenvwrapper
      mkvirtualenv -p /usr/bin/python3 streetmaintenance

  Activating the virtual env (not required straight after creation):

      workon streetmaintenance

### Python requirements

Use [pip-tools](https://github.com/jazzband/pip-tools) to install and maintain installed dependencies.

    pip install -U pip  # pip-tools needs pip==6.1 or higher (!)
    pip install pip-tools

Install requirements as follows

    pip-sync requirements.txt requirements-dev.txt

### Django configuration

Use `local_settings.py` in the project root to override settings with environment specific values.

### Database

Create user and database

    sudo -u postgres createuser -P -R -S streetmaintenance  # use password `streetmaintenance`
    sudo -u postgres createdb -O streetmaintenance streetmaintenance
    sudo -u postgres psql streetmaintenance -c "CREATE EXTENSION IF NOT EXISTS postgis;"

Allow user to create test database

    sudo -u postgres psql -c "ALTER USER streetmaintenance CREATEDB;"

Tests also require that PostGIS extension is installed on the test database. This can be achieved most easily by adding PostGIS extension to the default template: 

    sudo -u postgres psql -d template1 -c "CREATE EXTENSION IF NOT EXISTS postgis;"

Run migrations

    python manage.py migrate

### Updating requirements files

Use `pip-tools` to update the `requirements*.txt` files.

When you change requirements, set them in `requirements.in` or `requirements-dev.in`. Then run:

    pip-compile requirements.in
    pip-compile requirements-dev.in

*NOTE:* Unfortunately there is a [bug](https://github.com/jazzband/pip-tools/issues/445) in `pip-compile` ATM (v1.8.0), so you might need to edit `requirements*.txt` manually to remove `setuptools` dependencies.

### Running tests

Run all tests

    py.test
    
Run with coverage

    py.test --cov-report html --cov .
    
Open `htmlcov/index.html` for the coverage report.

### Starting a development server

    python manage.py runserver

The API will be located at `http://localhost:8000`
