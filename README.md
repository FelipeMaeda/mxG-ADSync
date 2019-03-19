# Setup devlopment environment (First time)

### Step 1
- **Open a terminal window**:
```
mkdir ~/ADSynCode
cd ~/ADSynCode
git clone https://github.com/inova-tecnologias/mxG-ADSync.git
cd mxG-ADSync
virtualenv -p PYTHON_PATH .venv
source .venv/bin/activate
sudo apt-get install rabbitmq-server
pip install -r requirements.txt
python manage.py migrate
celery -A mxG_ADSync worker -l info
```
### Step 2
- **Open other terminal window**:
```
cd ~/ADSynCode/mxG-ADSync
source .venv/bin/activate
celery -A mxG_ADSync beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```
### Step 3
- **Open other terminal window**:
```
cd ~/ADSynCode/mxG-ADSync
source .venv/bin/activate
python manage.py runserver
```
# Continuos development

### Setup

- If you haven't installed RabbitMQ yet:

> update and install this package first:
```
sudo apt-get install rabbitmq-server
```

### Step 1
- **Open a terminal window**:
```
cd ~/ADSynCode/mxG-ADSync
source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
celery -A mxG_ADSync worker -l info
```
### Step 2
- **Open other terminal window**:
```
cd ~/ADSynCode/mxG-ADSync
source .venv/bin/activate
celery -A mxG_ADSync beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```
### Step 3
- **Open other terminal window**:
```
cd ~/ADSynCode/mxG-ADSync
source .venv/bin/activate
python manage.py runserver
```

