SurveyUI
========

Live Test: http://hr4etest.herokuapp.com/
Live test last update: 6/1/14

Verify adding/selecting projects affect the old website
---------------------------------------------
1. Visit [our live website](http://hr4etest.herokuapp.com/)
2. Click 'Write your own survey'
3. Login using Username='hr4e' and Password='pw'
4. Create a new project by clicking 'Add a new project'
5. Fill in the required fields and click 'submit'
6. Visit [the old website](http://hr4etest.herokuapp.com/multiquest/registration/selectProjectDefault/)
7. Verify that your newly created project is listed.
8. Select a project from the old website
9. Visit [our live website](http://hr4etest.herokuapp.com/home/)
10. Verify that your selected project is now reflected in the home page, at the top
Note that Selecting a project on our website will not reflect onto the old website due to its implementation


Verify adding surveys affect the old website
--------------------------------------------
1. Visit [our live website](http://hr4etest.herokuapp.com/)
2. Click 'Write your own survey'
3. Login using Username='hr4e' and Password='pw'
4. Create a new survey by clicking 'Create a new survey'
5. Fill in the required fields and click 'submit'
6. Visit the old website: [selectQuestionnaireDefault](http://hr4etest.herokuapp.com/multiquest/registration/selectQuestionnaireDefault/)
It should redirect you and tell you to select a default project. Select the project that contains your survey, and revisit [selectQuestionnaireDefault](http://hr4etest.herokuapp.com/multiquest/registration/selectQuestionnaireDefault/)
7. Verify that the survey you created is reflected on this list
8. Select your newly created survey (important for the next test)
9. Visit the old website: [setPageToPageTransitionCalculated](http://hr4etest.herokuapp.com/multiquest/working_pages/setPageToPageTransitionCalculated/)
It shouldn't work; To demonstrate changes on this page:
12. Visit [our live website](http://hr4etest.herokuapp.com/editor/)
13. Select your newly created survey
14. Click 'Add a new page' and fill in the required fields; submit
15. Visit the old website: [setPageToPageTransitionCalculated](http://hr4etest.herokuapp.com/multiquest/working_pages/setPageToPageTransitionCalculated/)
16. It should still be broken! We have not yet added any questions to this new survey
17. Visit [our live website](http://hr4etest.herokuapp.com/editor/)
18. Select the same survey
19. Select the new page you have created
20. Click 'Add a new question' and fill in the required fields; submit
21. Visit the old website: [setPageToPageTransitionCalculated](http://hr4etest.herokuapp.com/multiquest/working_pages/setPageToPageTransitionCalculated/)
22. It should work, add more pages to see more changes



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




