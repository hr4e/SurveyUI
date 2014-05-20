var surveyControllers = angular.module("surveyControllers", []);

surveyControllers.controller("ProjectListCtrl", ["$scope", "$http",
						 function($scope, $http){
  							$http.get("projects/projects.json").success(function(data){
    								$scope.projects = data;
  							})
						 }
]);
