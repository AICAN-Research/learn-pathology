Learn Pathology
=====================

Learn Pathology is a web-based system for teaching students 
the field of pathology. In the system, teachers can create online courses
and assignments. Students can view and interact with
large whole slide microscopy images (WSIs) as well as answering questions
and performing assignments.

Learn Pathology is developed by the Norwegian University of Science and Technology (NTNU)
and SINTEF Digital, the Health Department, and is released under the permissive [MIT license](https://mit-license.org).

The system is built using the following open source technologies:
* [Django](https://www.djangoproject.com/)
* [OpenSeadragon](https://openseadragon.github.io)
* [FAST](https://fast.eriksmistad.no)
* [OpenSlide](https://openslide.org)

Requirements
-------------------
* Python 3
* For FAST backend you must have OpenCL installed

Development setup
-------------------
This is for setting up and running learn pathology locally on your computer
for development purposes. For deployment of the system on a web server, see the 
deployment instructions below.

1. Clone project
```bash
git clone https://github.com/AICAN-Research/learn-pathology.git
cd learn-pathology
```
2. Create virtual environment
```bash
# Install environment
pip install virtualenv
virtualenv -ppython3 environment
# Activate environment
source environment/bin/activate # Linux
environment/Scripts/activate.ps1 # Windows
# Install dependencies
pip install -r requirements.txt
```
3. Create database
```bash
python manage.py migrate
```
4. Create super user
```bash
python manage.py createsuperuser
```
5. Run server
```bash
python manage.py runserver
```
Open your web browser at http://localhost:8000

6. Add some slides
- Download some slides from http://openslide.org/demo to your machine
- Login
- Go to admin page
- Press slide, and add some slides to the database

Deployment & Server optimization
-------------------

This guide is for Ubuntu Linux.
To setup Learn Pathology for deployment on a server use apache2 and mod_wsgi.

**1. First install packages**
```bash
sudo apt install python3-pip apache2 libapache2-mod-wsgi-py3
```

Also make sure you have all [requirements for FAST installed](https://fast.eriksmistad.no/install-ubuntu-linux.html):
```bash
sudo apt install libgl1 libopengl0 libopenslide0 libusb-1.0-0 libxcb-xinerama0
```
You also need OpenCL. To install OpenCL on Linux, download an implementation depending on the CPU/GPU you have.


**2. Then clone the repo on the server** for instance to /var/www/
```bash
cd /var/www/
git clone https://github.com/AICAN-Research/learn-pathology
```

**3. Setup virtual environment on the server**
```bash
cd learn-pathology
virtualenv -ppython3 environment
source environment/bin/activate
```

**4. Install requirements**
```bash
pip install --upgrade pip # Make sure pip is up to date first
pip install -r requirements.txt
```

**5. Create a secret key and configure settings**   
Generate a secret key and add it to settings.py
```bash
python manage.py shell -c 'from django.core.management import utils; print(utils.get_random_secret_key())'
```
Edit the file learnpathology/settings.py.
Uncomment and set the SECRET_KEY to the output of the python command above.
**Remember to keep this key secret, and do not push it to git/github.** You may change it, even when the system is in use, but note that users may be logged out.
See here for more info: https://medium.com/@bayraktar.eralp/changing-rotating-django-secret-key-without-logging-users-out-804a29d3ea65

Disable debug mode by setting `debug = False`.
For security reasons this should always be off on a production server, only turn it on if you need to actually debug.

Add your domain to ALLOWED_HOST, for example like so:  
```ALLOWED_HOSTS = ['learnpathology.no', 'www.learnpathology.no']```


**6. Initialize database**
```bash
./manage.py makemigrations
./manage.py migrate
```

**7. Create super user**
```bash
./manage.py createsuperuser
```


**8. Collect static files**
```bash
./manage.py collectstatic
```

**9. Fix user permissions**    
Apache needs write access to the database.
Apache runs on the user wwww-data thus give this user write 
access to the root folder and the database file db.sqlite3
```bash
cd ..
sudo chown :www-data learn-pathology
sudo chmod g+w learn-pathology
cd learn-pathology
sudo chown www-data db.sqlite3
sudo chmod g+w db.sqlite3
```

**10. Create an apache config**
```bash
sudo nano /etc/apache2/sites-available/learnpathology.conf
```
You should always use HTTPS and SSL encryption.
If you are not using HTTPS, you are essentially transferring everything, login password, images, on the webpage totally unencrypted over the internet! 
To use HTTPS/SSL encryption you need an SSL certificate, you can buy one cheap from services like [namecheap.com](https://www.namecheap.com) or free from [Let's encrypt](https://letsencrypt.org/). 
Store the certificate, the key, and the CA certificate files on the server, e.g. in folder /var/www/learn-pathology/ssl/.
The config with SSL/HTTPS end-to-end-encryption will then look something like this:
```
# Redirect to secure site
<VirtualHost *:80>
    ServerName learnpathology.no
    ServerAdmin you@domain.com
    Redirect permanent / https://learnpathology.no
</VirtualHost>

<VirtualHost *:443>
    # Common stuff
    ServerName learnpathology.no
    ServerAdmin you@domain.com
    DocumentRoot /var/www/learn-pathology/

    # SSL stuff
    SSLEngine on
    SSLCertificateFile "/var/www/learn-pathology/ssl/certificate.crt"
    SSLCertificateKeyFile "/var/www/learn-pathology/ssl/certificate.key"
    SSLCACertificateFile "/var/www/learn-pathology/ssl/certificate.ca.crt"

    Alias /static /var/www/learn-pathology/static
    <Directory /var/www/learn-pathology/static>
        Require all granted
    </Directory>

    <Directory /var/www/learn-pathology/learnpathology>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    # Modify this to fit your python version:
    WSGIDaemonProcess learnpathologywsgi python-path=/var/www/learn-pathology/:/var/www/learn-pathology/environment/lib/python3.10/site-packages processes=32 threads=32
    # This setting is needed for FAST to run properly:
    WSGIApplicationGroup %{GLOBAL}
    WSGIProcessGroup learnpathologywsgi
    WSGIScriptAlias / /var/www/learn-pathology/learnpathology/wsgi.py

    ErrorLog ${APACHE_LOG_DIR}/learnpathology.error.log
    CustomLog ${APACHE_LOG_DIR}/learnpathology.access.log combined
</VirtualHost>
```

**11. Enable website and test**
```bash
sudo a2ensite learnpathology
sudo systemctl reload apache2
```
Open your browser and check that the webpage works.
A usual cause of error on the apache2 server, when enabling the website, is a syntax error in the configuration file. In such situations, you can use the command line `apache2ctl configtest` to debug the file.

**12. Server Optimizations**

**Use mpm_worker to enable multi-processing and multi-threading**  

By default, apache will use mpm_prefork to handle multiple requests, which do not use any multi-threading.
If you plan to serve hundreds of simultaneous users, you should consider using mpm_worker instead.

To do so, first enable mpm_worker:
```bash
sudo a2dismod mpm_prefork
sudo a2enmod mpm_worker
sudo service apache2 restart
```
Then open the mpm_worker config: `sudo nano /etc/apache2/mods-enabled/mpm_worker.conf`

The following config has worked well for us:
```
<IfModule mpm_worker_module>
        ServerLimit              32
        StartServers             16
        MinSpareThreads          50
        MaxSpareThreads          100
        ThreadLimit              64
        ThreadsPerChild          50
        MaxRequestWorkers        512
        MaxConnectionsPerChild   0
</IfModule>
```
Restart apache after changes:
```bash
sudo service apache2 restart
```

**Enable turbojpeg**

Requested image tiles have to be compressed with JPEG before they are sent to the users.
By default, PIL is used for compression which is slow. Turbo JPEG is a faster option.

To use TurboJPEG, first install it: 
```bash
sudo apt install libturbojpeg
```
and install it in your python environment:
```bash
pip install PyTurboJPEG==1.7.*
```
then enable it in learnpathology/settings.py:
```python
USE_TURBOJPEG = True
```

Reload apache after changes:
```bash
sudo service apache2 reload
```

**Cache tiles in memory using memcached**

In an educational setting, you might have several hundred students which will
access the same few images at the same time during class.
Since reading images from the harddrive is one of the slowest operations, you
can considerably improve performance by having the images in memory instead.
In this case, all students, except the first one, accessing an image, will read
images directly from memory instead of the slow harddrive.

We recommend using memcached for this purpose, you can install it like this:
```bash
sudo apt update
sudo apt install memcached libmemcached-tools
sudo service memcached start
```

Modify memcached config to allow it to use a lot of memory and large enough objects to be stored:
`nano /etc/memcached.conf`:
```
# Depending how much RAM you have, set the limit of you much
# memory memcached should be allowed to use, here we have set it
# to 100 GB = 100*1024 = 102400 MB:
-m 102400
# Allow file sizes up to 3 MB
-I 3m
```

Restart after modifying the config:
```bash
sudo service memcached restart
```

Install the pymemcache binding in your python environment:
```bash
pip install pymemcache==4.*
```

Enable the tile caching in learnpathology/settings.py:
```python
USE_TILE_CACHE = True
```

Reload apache after modifying settings:
```bash
sudo service apache2 reload
```

You can check if memcached is working by looking at its statistics (how many items are stored, number of cache hits/misses etc.):
```bash
memcstat --servers="127.0.0.1"
```

The images are stored for 30 minutes in memory as defined in slide/views.py:
```python
@cache_page(60 * 30)
def tile(request, slide_id, osd_level, x, y):
    ...
```

Learn Pathology is set to store a maximum of 100 000 images, here are the settings we have used (defined in learnpathology/settings.py):
```python
if USE_TILE_CACHE:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
            'LOCATION': '127.0.0.1:11211',
            'MAX_ENTRIES': 100000,
            'OPTIONS': {
                'no_delay': True,
                'ignore_exc': True,
                'max_pool_size': 4,
                'use_pooling': True,
            }
        }
    }
```

**13. Setting up FEIDE login**

To enable users to login using FEIDE/dataporten make sure you have got your client ID and secret key from your 
local FEIDE administration.

Then enable FEIDE login in learnpathology/settings.py:
```python
USE_FEIDE_LOGIN = True
```

Reload apache after modifying settings:
```bash
sudo service apache2 reload
```

Then go the admin page using your browser and create a new item under "Social applications"
and set the provider to *Dataporten* and enter your client id and secret key, also remember to add a site and select it
with your domain.
