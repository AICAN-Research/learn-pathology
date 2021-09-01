Learn Pathology
=====================

Learn Pathology is a web-based system for teaching students 
the field of pathology. In the system, students can view and interact with
large whole slide microscopy images (WSIs) as well as answering questions
and performing assignments.

Learn Pathology is developed by the Norwegian University of Science and Technology (NTNU)
and SINTEF Medical Technology, and is released under the permissive MIT license.

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

Deployment
-------------------