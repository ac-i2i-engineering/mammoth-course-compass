# Mammoth Course Compass (Amherst's Course Review System) Project
We're creating a web app with Course Review System at Amherst College. Planned features include:
* Auto-indexing of courses from college catalog
* Appropriate balance between anonymity & trust through robust moderation
* In-depth insights using statistics & machine learning to help you chart out a plan towards your academic goals
* And much, much more!

To clone the app, run in terminal:

```bash
git clone https://github.com/ac-i2i-engineering/mammoth-course-compass.git
cd access-amherst
```

[Optional]: Set-up a virtual environment and activate it to "containerize" the dependencies:

```bash
python3 -m venv env
source env/bin/activate
```

To run the app locally, run:

```bash
pip install -r requirements.txt
cd access_amherst_backend
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
