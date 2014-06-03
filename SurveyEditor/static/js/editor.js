var EditorCtrl = function ($scope, $modal) {
  $scope.visible = true;
  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };
  // Select modals
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
  // Create modals
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
  // Delete modals
  $scope.deleteProjModal = function(project) {
    var modalInstance = $modal.open({
      templateUrl: 'deleteProjectModal.html',
      controller: DeleteInstanceCtrl,
      resolve: {
        selection: function () {
          return project;
        }
      }
    });
  };
  $scope.deleteSurvModal = function() {
    var modalInstance = $modal.open({
      templateUrl: 'deleteSurveyModal.html',
      controller: StandardInstanceCtrl,
    });
  };
  $scope.deletePageModal = function() {
    var modalInstance = $modal.open({
      templateUrl: 'deletePageModal.html',
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
  // Edit modals
  $scope.updateQuesModal = function (question, survey) {
    var modalInstance = $modal.open({
      templateUrl: 'updateQuestionModal.html',
      controller: UpdateQuesInstanceCtrl,
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
var DeleteInstanceCtrl = function ($scope, $modalInstance, selection) {
  $scope.selection = selection;
  $scope.cancel = function () {
    $modalInstance.dismiss('cancel');
  };
};
var UpdateQuesInstanceCtrl = function ($scope, $modalInstance, selection) {
  $scope.question = {};
  $scope.question["questionTag"] = selection[0].questionTag;
  $scope.question["originalTag"] = selection[0].questionTag;
  $scope.question["questionText"] = selection[0].questionText;
  $scope.question["helpText"] = selection[0].helpText;
  $scope.question["explanation"] = selection[0].explanation;
  $scope.question["language"] = selection[0].language;
  $scope.question["description"] = selection[0].description;
  $scope.question["imageFileName"] = selection[0].imageFileName;
  $scope.question["imageFileType"] = selection[0].imageFileType;
  $scope.survey = selection[1];

  $scope.cancel = function () {
    $modalInstance.dismiss('cancel');
  };
};