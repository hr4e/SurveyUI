var HR4ESurvey = angular.module("HR4ESurvey", [
    "ngRoute",
    "ui.bootstrap",
    "surveyControllers"
]);

HR4ESurvey.config(["$routeProvider",
		   function($routeProvider){
		       $routeProvider.
			   when("/login",{
			       templateUrl: "partials/login.html",
			   }).
			   when("/projects",{
			       templateUrl: "partials/projects.html",
			       controller: "ProjectListCtrl"
			   }).
			   when("/specific-project",{
    			       templateUrl: "partials/specific-project.html"
  			   }).
			   when("/editor",{
    			       templateUrl: "partials/editor.html"
  			   }).
			   otherwise({
    			       redirectTo: "/projects"
  			   });
		   }
]);
