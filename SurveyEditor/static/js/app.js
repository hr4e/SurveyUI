'use strict';


// Declare app level module which depends on filters, and services
// The page_editor app will allow users to add/del and arrange the
//  order of pages for this survey
// var page_editor = angular.module('page_editor', []);

// The ques_editor app will allow users to add/del/mod questions
//  for a chosen page.
var EditorApp = angular.module('EditorApp', ['ui.bootstrap']);

EditorApp.factory('Nav', function(){
  var page = 'default';
  return {
    selected: function() {
    	return page;
    },
    selectPage: function(newPage) { 
    	page = newPage;
    }
  };
});

EditorApp.controller('MainCtrl', function ($scope, Nav) {
	$scope.Nav = Nav;
});

EditorApp.directive('resize', function ($window) {
	return function (scope, element) {
		var w = angular.element($window);
		scope.getWindowDimensions = function () {
			return {
				'h': w.height(),
				'w': w.width()
			};
		};
		scope.$watch(scope.getWindowDimensions, function (newValue, oldValue) {
			scope.windowHeight = newValue.h;
			scope.windowWidth = newValue.w;

			scope.style = function () {
				return {
					'height': (newValue.h - 100) + 'px',
					'width': (newValue.w - 100) + 'px'
				};
			};

		}, true);

		w.bind('resize', function () {
			scope.$apply();
		});
	}
})