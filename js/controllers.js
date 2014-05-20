var HR4ESurvey = angular.module("HR4ESurvey", []);

HR4ESurvey.controller("ProjectListCtrl", function($scope, $http){
  $http.get("projects/projects.json").success(function(data){
    $scope.projects = data;
  });
});
