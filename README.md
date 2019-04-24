# mxG-ADSync

mxG-ADSync is synchronization schedule LDAP attributes with MxGateway system.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

What things you need to install the software and how to install them.

### Instalation

- **Open a terminal window**
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
```

## Running
Can be in multiples tabs in the same window.
### Step 1
- **Open terminal window**
```
cd ~/ADSynCode/mxG-ADSync
source .venv/bin/activate
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




## Usage
- **Create a super user admin account**:
In mxG-ADSync directory

```python
/mxG_ADSync$ python manage.py createsuperuser
```
- **Login**:
Now, open a Web browser and go to “/admin/” on your local domain – e.g., http://127.0.0.1:8000/admin/. You should see the admin’s login screen:

<a href="https://docs.djangoproject.com/en/1.8/_images/admin01.png"><img src="https://docs.djangoproject.com/en/1.8/_images/admin01.png" title="Login" alt="Login"></a>

<!-- [![FVCproductions](https://avatars1.githubusercontent.com/u/4284691?v=3&s=200)](http://fvcproductions.com) -->

- **Create a credential in Db_Instances in django admin**
Set name and database credentials to do the syncronization with ldap attributes setting host, user, password and database.

- **Create a periodic task in django admin**:

Set the task tha will be perfomed, set schedule and set the arguments.
```
Task (custom):
db_instances.tasks.adsync_task
```
```
Interval: every 5 minutes
```
```
Start_time: today
            now
```            
```
Arguments: ["MxGateway", "inova.net"]
```

Save.

## WARNING:

> Is not recomended create periodic tasks with less than 5 minutes...


