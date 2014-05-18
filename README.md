SurveyUI
========

Development Server Setup
1. From the command line, cd into this repo's root directory
2. Run ``python manage.py runserver''
3. visit http://127.0.0.1:8000/test/

To view the database structures via Django admin
1. Run ``python manage.py syncdb''
2. It will ask if you want to create a super user; yes
3. You can press enter to skip fields such as email
4. visit http://127.0.0.1:8000/admin/ to view database