
# mxG-ADSync

mxG-ADSync is synchronization schedule LDAP attributes with MxGateway system.


## Getting Started
Requirements: python 3.6 or above and celery
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
Below steps can be do it in multiples tabs in the same window.
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

- **Create a credential in Db_Instances in django admin**: Set name and database credentials to do the syncronization with ldap attributes.
Example:

![README_07](https://user-images.githubusercontent.com/25668878/56669255-3bb75700-6687-11e9-89f5-17e78c109fb9.png)

- **Create a periodic task in django admin**: Set the task tha will be schedule.
Example:
```
Task (custom):
db_instances.tasks.adsync_task
```

![README_06](https://user-images.githubusercontent.com/25668878/56668670-4fae8900-6686-11e9-935d-a0ee773ec502.png)

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
![README_02](https://user-images.githubusercontent.com/25668878/56668682-550bd380-6686-11e9-9243-bd5fc81c60cd.png)

Save.

Your server screen has to seems like this:

![README_05](https://user-images.githubusercontent.com/25668878/56668722-68b73a00-6686-11e9-8707-6b9cb8be36a9.png)

## WARNING:

> Is not recomended create periodic tasks with less than 5 minutes...


