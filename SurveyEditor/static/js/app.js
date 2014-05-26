'use strict';


// Declare app level module which depends on filters, and services
// The page_editor app will allow users to add/del and arrange the
//  order of pages for this survey
// var page_editor = angular.module('page_editor', []);

// The ques_editor app will allow users to add/del/mod questions
//  for a chosen page.
var EditorApp = angular.module('EditorApp', ['ui.bootstrap']);

var NavbarCtrl = function ($scope, $location) {

  $scope.isCollapsed = true;
  $scope.msg = 'wat';
  $scope.test = function() {
    return 'yes';
  }
  $scope.isActive = function(path) {
    if ($location.path().substr(0, path.length) == path) {
      return "active"
    } else {
      return $location.path()
    }
  };

};