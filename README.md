SurveyUI
========
If you have npm and want some convenience with setup, the command "npm install" gets all dependencies along with http-server and bower for you.
=======

Development Server Setup

1. From the command line, cd into this repo's root directory
2. Run ``python manage.py runserver''
3. visit http://127.0.0.1:8000/test/

To view the database structures via Django admin

1. Run ``python manage.py syncdb''
2. It will ask if you want to create a super user; yes
3. You can press enter to skip fields such as email
4. visit http://127.0.0.1:8000/admin/ to view database

Troubleshooting:

Ensure you have Django installed on your machine, otherwise step 2 will fail.
To install Django:

1. Install pip: https://pip.pypa.io/en/latest/installing.html
2. Install Django with `pip install django`

Steps above may require root privileges.