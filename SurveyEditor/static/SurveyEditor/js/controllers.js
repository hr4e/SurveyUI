'use strict';

/* Controllers */
// using_underscores for variable names
// camelCase for function names
ques_editor.controller('QuesCtrl', function ($scope) {

	var addQues = function (layer) {
		
		var ques = new Kinetic.Group({
			draggable: true
		});
		var x_pos = Math.random() * (500-100);
		var y_pos = Math.random() * (400-100);
		var square = new Kinetic.Rect({
			x: x_pos,
			y: y_pos,
			
			width: 100,
			height: 100,
			fill: 'green',
			stroke: 'black',
			strokeWidth: 4
		});
		var text = new Kinetic.Text({
			x: x_pos + 42,
			y: y_pos + 32,
			text: 6,
			fontSize: 30,
			fontFamily: 'Calibri',
			fill: 'black'
		});
		ques.add(square);
		ques.add(text);

		// add the shape to the layer
		$scope.layer.add(ques);
		$scope.stage.add($scope.layer);
	}

	// Methods published to the scope
	// ==============================
	$scope.initCanvas = function() {
		var stage = new Kinetic.Stage({
			container: 'QuesCanvas',
			width: 600,
			height: 400
		})
		$scope.stage = stage;
		var layer = new Kinetic.Layer();
		$scope.layer = layer;

		stage.add(layer);
	}

	$scope.surprise = function() {
		$scope.msg = "surprise!";
		addQues();
	}


})