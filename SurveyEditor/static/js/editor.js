var EditorCtrl = function ($scope) {
  $scope.visible = true;
  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

	$scope.surprise = function() {
		$scope.msg = $scope.windowWidth;
		drawQues();
	};

};

var NewPageModalCtrl = function ($scope, $modal, $log) {


  $scope.items = ['item1', 'item2', 'item3'];

  $scope.open = function (size) {

    var modalInstance = $modal.open({
      templateUrl: 'addPageModal.html',
      controller: NewPageInstanceCtrl,
      size: size,
      resolve: {
        items: function () {
          return $scope.items;
        }
      }
    });

    modalInstance.result.then(function (selectedItem) {
      $scope.selected = selectedItem;
    }, function () {
      $log.info('Modal dismissed at: ' + new Date());
    });
  };
};

// Please note that $modalInstance represents a modal window (instance) dependency.
// It is not the same as the $modal service used above.

var NewPageInstanceCtrl = function ($scope, $modalInstance, items) {
  $scope.items = items;
  $scope.selected = {
    item: $scope.items[0]
  };

  $scope.ok = function () {
    $modalInstance.close($scope.selected.item);
  };

  $scope.cancel = function () {
    $modalInstance.dismiss('cancel');
  };
};

var NewQuestionModalCtrl = function ($scope, $modal, $log) {

  $scope.open = function (page, survey) {

    var modalInstance = $modal.open({
      templateUrl: 'addQuestionModal.html',
      controller: NewQuestionInstanceCtrl,
      resolve: {
        selection: function () {
          return [page, survey];
        }
      }
    });

  };
};

// Please note that $modalInstance represents a modal window (instance) dependency.
// It is not the same as the $modal service used above.

var NewQuestionInstanceCtrl = function ($scope, $modalInstance, selection) {
  $scope.page = selection[0];
  $scope.cancel = function () {
    $modalInstance.dismiss('cancel');
  };
};