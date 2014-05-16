'use strict';

/* Controllers */
// using_underscores for variable names
// camelCase for function names
ques_editor.controller('QuesCtrl', function ($scope) {



	// Methods published to the scope
	// ==============================
	$scope.ques_list = ['a', 'b', 'c', 'd'];
	$scope.hello = "hello AngularJS world";

	$scope.initCanvas = function() {
		var stage = new Kinetic.Stage({
			container: 'ques_canvas',
			width: 1000,
			height: 400
		})
		//$scope.stage = stage;

		var layer = new Kinetic.Layer();
		//$scope.layer = layer;

	stage.add(layer);
	}


})