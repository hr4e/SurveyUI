var EditorCtrl = function ($scope, $modal) {
  $scope.visible = true;
  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };
  $scope.newProjModal = function() {
    var modalInstance = $modal.open({
      templateUrl: 'addProjectModal.html',
      controller: StandardInstanceCtrl,
    });
  };
  $scope.newSurvModal = function() {
    var modalInstance = $modal.open({
      templateUrl: 'addSurveyModal.html',
      controller: StandardInstanceCtrl,
    });
  };
	$scope.newPageModal = function() {
    var modalInstance = $modal.open({
      templateUrl: 'addPageModal.html',
      controller: StandardInstanceCtrl,
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
      controller: StandardInstanceCtrl,
    });
  };
  $scope.selectSurvModal = function() {
    var modalInstance = $modal.open({
      templateUrl: 'selectSurveyModal.html',
      controller: StandardInstanceCtrl,
    });
  };
  $scope.deleteQuesModal = function (question) {
    var modalInstance = $modal.open({
      templateUrl: 'deleteQuestionModal.html',
      controller: deleteQuesInstanceCtrl,
      resolve: {
        objectToDelete: function () {
          return question;
        }
      }
    });
  };

};


var StandardInstanceCtrl = function ($scope, $modalInstance) {
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
var deleteQuesInstanceCtrl = function ($scope, $modalInstance, objectToDelete) {
  $scope.question = objectToDelete;
  $scope.cancel = function () {
    $modalInstance.dismiss('cancel');
  };
};