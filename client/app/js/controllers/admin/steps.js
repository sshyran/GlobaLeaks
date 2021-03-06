GLClient.controller('AdminStepAddCtrl', ['$scope',
  function($scope) {
    $scope.new_step = {};

    $scope.add_step = function() {
      var step = new $scope.admin_utils.new_step($scope.questionnaire.id);
      step.label = $scope.new_step.label;
      step.presentation_order = $scope.newItemOrder($scope.questionnaire.steps, 'presentation_order');

      step.$save(function(new_step){
        $scope.questionnaire.steps.push(new_step);
        $scope.new_step = {};
      });
    };
  }
]).
controller('AdminStepEditorCtrl', ['$scope', '$uibModal', 'AdminStepResource', 'AdminFieldResource',
  function($scope, $uibModal, AdminStepResource, AdminFieldResource) {
    $scope.editing = false;
    $scope.new_field = {};
    $scope.fields = $scope.step.children;

    $scope.toggleEditing = function () {
      $scope.editing = $scope.editing ^ 1;
    };

    $scope.save_step = function(step) {
      var updated_step = new AdminStepResource(step);
      return $scope.Utils.update(updated_step);
    };

    $scope.addField = function(field) {
      $scope.step.children.push(field);
    };

    $scope.delField = function(fields, field) {
      AdminFieldResource.delete({
        id: field.id
      }, function() {
        $scope.Utils.deleteFromList(fields, field);
      });
    };

    $scope.add_field = function() {
      var field = $scope.admin_utils.new_field($scope.step.id, '');
      field.label = $scope.new_field.label;
      field.type = $scope.new_field.type;
      field.attrs = $scope.admin.get_field_attrs(field.type);
      field.y = $scope.newItemOrder($scope.step.children, 'y');

      field.$save(function(new_field){
        $scope.addField(new_field);
        $scope.new_field = {};
      });
    };

    $scope.add_field_from_template = function(template_id) {
      var field = $scope.admin_utils.new_field_from_template(template_id, $scope.step.id, '');
      field.y = $scope.newItemOrder($scope.step.children, 'y');

      field.$save(function(new_field) {
        $scope.step.children.push(new_field);
      });
    };

    $scope.moveUpAndSave = function(elem) {
      $scope.Utils.moveUp(elem);
      $scope.save_step(elem);
    };

    $scope.moveDownAndSave = function(elem) {
      $scope.Utils.moveDown(elem);
      $scope.save_step(elem);
    };

    $scope.moveLeftAndSave = function(elem) {
      $scope.Utils.moveLeft(elem);
      $scope.save_step(elem);
    };

    $scope.moveRightAndSave = function(elem) {
      $scope.Utils.moveRight(elem);
      $scope.save_step(elem);
    };
  }
]);
