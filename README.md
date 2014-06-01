SurveyUI
========

Live Test: http://hr4etest.herokuapp.com/
Live test last update: 5/30/14

Verify we affect the old database
-----------------------------------

It is important to show that we actually did stuff,
and didn't goof off the entire time.

Let us specify a standard use case.

1. Navigate to the website, either a locally running server or the live
site.
2. Login with the admin credentials listed above.
3. Create a new project. Admiring our modals is optional.
4. Create a new questionnaire in the project by clicking the button
5. Select your survey. Press ok.
6. Add a new page with the button.
7. Add a new question to the page with the button.
8. Navigate to <url>/admin/ and verify that the enteires were correctly
input in the database.

Verify we affect the old site
-----------------------------

Now, let us verify that the changes are persistent in the database
between sites.

1. Navigate to the live site.
2. Login with the admin credentials listed above.
3. Create a new project. Admiring our modals is optional.
4. Create a new questionnaire in the project by clicking the button
5. Select your survey. Press ok.
6. Add a new page with the button.
7. Add a new question to the page with the button.
8. Navigate to [the old website](http://www.hr4etest.herokuapp.com/multiquest/registration/userLanding)
and login with the same credentials. (TODO update the URL).
9. Verify that the project and appropriate info are there.

Development Server Setup
------------------------

1. From the command line, cd into this repo's root directory
2. Run ``python manage.py runserver''
3. visit http://127.0.0.1:8000/test/

To view the database structures via Django admin

1. visit http://127.0.0.1:8000/admin/ to view database

Questionnaire Editor Python Dependencies
1. pip install python-dateutil
2. pip install reportlab

Troubleshooting:
----------------

Ensure you have Django installed on your machine, otherwise step 2 will fail.
To install Django:

1. Install pip: https://pip.pypa.io/en/latest/installing.html
2. Install Django with `pip install django`

Steps above may require root privileges.

Admin credentials
-----------------
> usr = hr4e
> pw  = pw




