SurveyUI
========

Live Test: http://hr4etest.herokuapp.com/

Development Server Setup

1. From the command line, cd into this repo's root directory
2. Run ``python manage.py runserver''
3. visit http://127.0.0.1:8000/test/

To view the database structures via Django admin

1. visit http://127.0.0.1:8000/admin/ to view database

Questionnaire Editor Python Dependencies
1. pip install python-dateutil
2. pip install reportlab

Troubleshooting:

Ensure you have Django installed on your machine, otherwise step 2 will fail.
To install Django:

1. Install pip: https://pip.pypa.io/en/latest/installing.html
2. Install Django with `pip install django`

Steps above may require root privileges.

Admin credentials
> usr = hr4e
> pw  = pw