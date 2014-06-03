var EditorCtrl = function ($scope, $modal) {
  $scope.visible = true;
  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

  $scope.newProjModal = function() {
    var modalInstance = $modal.open({
      templateUrl: 'addProjectModal.html',
      controller: NewProjInstanceCtrl,
    });
  };

  $scope.newSurvModal = function() {
    var modalInstance = $modal.open({
      templateUrl: 'addSurveyModal.html',
      controller: NewSurvInstanceCtrl,
    });
  };

	$scope.newPageModal = function() {
    var modalInstance = $modal.open({
      templateUrl: 'addPageModal.html',
      controller: NewPageInstanceCtrl,
    });
	};

  $scope.newQuesModal = function (page, survey) {
    var modalInstance = $modal.open({
      templateUrl: 'addQuestionModal.html',
      controller: NewQuesInstanceCtrl,
      resolve: {
        selection: function () {
          return [page, survey];
        }
      }
    });
  };

  $scope.selectProjModal = function() {
    var modalInstance = $modal.open({
      templateUrl: 'selectProjectModal.html',
      controller: SelectProjInstanceCtrl,
    });
  };

  $scope.selectSurvModal = function() {
    var modalInstance = $modal.open({
      templateUrl: 'selectSurveyModal.html',
      controller: SelectSurvInstanceCtrl,
    });
  };

};
// /open(listPages[selectedPage-1].currentPage, selectedSurvey)
var NewProjInstanceCtrl = function ($scope, $modalInstance) {
  $scope.cancel = function () {
    $modalInstance.dismiss('cancel');
  };
};

var NewSurvInstanceCtrl = function ($scope, $modalInstance) {
  $scope.cancel = function () {
    $modalInstance.dismiss('cancel');
  };
};

var NewPageInstanceCtrl = function ($scope, $modalInstance) {
  $scope.cancel = function () {
    $modalInstance.dismiss('cancel');
  };
};

var NewQuesInstanceCtrl = function ($scope, $modalInstance, selection) {
  $scope.page = selection[0];
  $scope.survey = selection[1];
  $scope.cancel = function () {
    $modalInstance.dismiss('cancel');
  };
};

var SelectProjInstanceCtrl = function ($scope, $modalInstance) {
  $scope.cancel = function () {
    $modalInstance.dismiss('cancel');
  };
};

var SelectSurvInstanceCtrl = function ($scope, $modalInstance) {
  $scope.cancel = function () {
    $modalInstance.dismiss('cancel');
  };
};