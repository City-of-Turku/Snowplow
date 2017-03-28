# Street Maintenance API
[![Build Status](https://travis-ci.org/City-of-Turku/street-maintenance-api.svg?branch=master)](https://travis-ci.org/City-of-Turku/street-maintenance-api)

Django-based REST API for Turku area street maintenance vehicle data.

## Requirements

* Python 3.x
* PostgreSQL + PostGIS

## Development

### Install required system packages

#### PostgreSQL

    # Ubuntu 16.04
    sudo apt-get install build-essential python3-dev libpq-dev postgresql postgis
    
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

The API will be located at `http://localhost:8000/v1/`

## Importing data

### Configuring importers

Vehicle data importers are enabled and configured using `STREET_MAINTENANCE_IMPORTERS` setting.

It is a dictionary where keys are fully qualified names of enabled importers' classes, and values for those are dictionaries containing settings for that importer.

Example config for KuntoTurku importer (the only available importer ATM):

```
STREET_MAINTENANCE_IMPORTERS = {
    'vehicles.importers.kuntoturku.KuntoTurkuImporter': {
        'RUN_INTERVAL': 5.0,  # in seconds, defaults to 5.0 if not given
        'URL': <KuntoTurku URL>,  # required
    }
}
```

### Running importers

[Celery](http://www.celeryproject.org/) is used to run the vehicle data importers. It is installed along other python packages, but it requires an external broker application. We are using [Redis](https://redis.io/) for that, which can be most easily installed by 

```
sudo apt-get install redis-server
```

That packaged version is somewhat old, but it doesn't really matter in our usage.

In *development*, celery can be started with command

```
celery -A streetmaintenance worker -l debug -B -c 1
```

It is important to keep concurrency (`-c`) at `1` to prevent possible race conditions.

### Creating a new importer

In order to create a new importer, following steps are needed:

1) Create a class for the new importer by subclassing `BaseVehicleImporter`.

2) Choose a unique id for the importer. A `DataSource` object will be created automatically to match the importer.

3) Implement at least `run()` method. For setting up stuff `__init__(*args, **kwargs)` can be used, but remember to call the super class as well. Importers are instantiated when the django app config is ready.

4) Enable the new importer by putting it and it's settings in `STREET_MAINTENANCE_IMPORTERS` dict.

Inside the importer, settings for it are available as `self.settings` and its data source object as `self.datasource`. The importer needs to assign the data source for its vehicles.

Check the [KuntoTurku](vehicles/importers/kuntoturku.py) importer for an example implementation.

## API

The API closely matches [Helsinki City Aura API](https://github.com/City-of-Helsinki/aura/wiki/API) with two minor differences:
  * `ID`s are `int`s instead of `string`s
  * timestamps contain the letter `T` and a time zone, example: `2017-03-22T14:14:25+02:00`

A [Swagger](https://swagger.io/) specification of the API is [here](swagger.yaml).
