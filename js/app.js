var HR4ESurvey = angular.module("HR4ESurvey", [
    "ngRoute",
    "ui.bootstrap",
    "surveyControllers"
]);

HR4ESurvey.config(["$routeProvider",
		   function($routeProvider){
		       $routeProvider.
			   when("/projects",{
			       templateUrl: "partials/projects.html",
			       controller: "ProjectListCtrl"
			   })/*.
			   otherwise({
    			       redirectTo: "/projects"
  			   });*/
		   }
]);
