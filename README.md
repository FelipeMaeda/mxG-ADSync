# mxG-ADSync

mxG-ADSync is synchronize schedule of LDAP attributes with MxGateway system

## Instalation

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
## Usage
- **Create a super user admin account**:
In mxG-ADSync directory

```python
$ python manage.py createsuperuser
```
- **Login**:
Now, open a Web browser and go to “/admin/” on your local domain – e.g., http://127.0.0.1:8000/admin/. You should see the admin’s login screen:

<a href="https://docs.djangoproject.com/en/1.8/_images/admin01.png"><img src="https://docs.djangoproject.com/en/1.8/_images/admin01.png" title="Login" alt="Login"></a>

<!-- [![FVCproductions](https://avatars1.githubusercontent.com/u/4284691?v=3&s=200)](http://fvcproductions.com) -->

- **Create a db isntance in django admin**

- **Create a periodic task in django admin**:
In this section user has to pass name of db instance and domain name in periodic task as arguments.

## WARNING:

> Is not recomended create periodic tasks with less tahn of 5 minutes...


