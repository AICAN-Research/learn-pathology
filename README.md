Learn Pathology
=====================

Learn Pathology is a web-based system for teaching students the field of pathology. 
In the system, teachers can create online courses and assignments. 
Students can view and interact with large whole slide microscopy images (WSIs) as well as answering questions and performing assignments.

Learn Pathology is developed by the Norwegian University of Science and Technology (NTNU) and SINTEF Digital, the Health Department, and is released under the permissive [MIT license](https://mit-license.org).

The system is built using the following open source technologies:
* [Django](https://www.djangoproject.com/)
* [OpenSeadragon](https://openseadragon.github.io)
* [Annotorious](https://github.com/annotorious/annotorious)
* [OpenSlide](https://openslide.org)
* [FAST](https://fast-imaging.github.io)
* ++ see requirements.txt file

Requirements
-------------------
* Python 3.10
* See requirements.txt for all requirements
* For FAST backend you must have OpenCL installed

Development setup
-------------------
This is for setting up and running learn pathology locally on your computer
for development purposes. These instructions are not for deployment/production use.

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

6. Add some whole slide images
- Login
- Go to admin page
- Press slide, and add some slides to the database by specifying the path to the slides.

