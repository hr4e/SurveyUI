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
  $scope.deleteQuesModal = function (question, survey) {
    var modalInstance = $modal.open({
      templateUrl: 'deleteQuestionModal.html',
      controller: DeleteQuesInstanceCtrl,
      resolve: {
        selection: function () {
          return [question, survey];
        }
      }
    });
  };
  $scope.updateQuesModal = function (question, survey) {
    var modalInstance = $modal.open({
      templateUrl: 'updateQuestionModal.html',
      controller: QuesInstanceCtrl,
      resolve: {
        selection: function () {
          return [question, survey];
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
var DeleteQuesInstanceCtrl = function ($scope, $modalInstance, selection) {
  $scope.question = selection[0];
  $scope.survey = selection[1];

  $scope.cancel = function () {
    $modalInstance.dismiss('cancel');
  };
};
var QuesInstanceCtrl = function ($scope, $modalInstance, selection) {
  $scope.question = {};
  $scope.question["questionTag"] = selection[0].questionTag;
  $scope.question["questionText"] = selection[0].questionText;
  $scope.question["helpText"] = selection[0].helpText;
  $scope.question["explanation"] = selection[0].explanation;
  $scope.question["language"] = selection[0].language;
  $scope.question["description"] = selection[0].description;
  $scope.question["imageFileName"] = selection[0].imageFileName;
  $scope.question["imageFileType"] = selection[0].imageFileType;
  $scope.question = selection[0];
  $scope.survey = selection[1];

  $scope.setField = function (newValue) {
    this.value = newValue;
  }
  $scope.cancel = function () {
    $modalInstance.dismiss('cancel');
  };
};