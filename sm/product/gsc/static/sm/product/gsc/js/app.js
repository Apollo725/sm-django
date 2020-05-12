var app = angular.module('app', ['angularMoment']);

app.controller("checkout", ['$scope', '$sce', function ($scope, $sce) {
    // disabling inputs, for some reason, this has to go first otherwise it breaks the controller

    // fetching the data from the checkoutData variable that was placed on the global scope by the view
    $scope.data = checkoutData;

    // Creating array of data keys, because somehow ng-repeat didn't work with object in this context
    $scope.keys = [];

    $scope.mapKeys = function (array) {
        for (var key in $scope.data) {
            if ($scope.data.hasOwnProperty(key)) {
                array.push(key);
            }
        }
    };

    $scope.mapKeys($scope.keys);
    //alert($scope.keys)

    // Utilities
    $scope.htmlTrusting = function (string) {
        return $sce.trustAsHtml(string);
    };


// Defining the active card based on the checkout step

    // Defining the Card object
    $scope.Card = {};

    // Defining the step
    $scope.Card.state = !$scope.data.transfer;

    // If it's a transfer create and initialize $scope.data.transferValidated to "notValidated"
    if ($scope.data.transfer) {
        $scope.data.transferValidated = "transferNotValidated";
    }


    $scope.Card.goState = function () {
        if (!$scope.Card.state && $scope.data.transfer && $scope.data.transferValidated === "transferNotValidated") {
            return 0;
        } else if ($scope.Card.state === 0 && $scope.data.transfer && $scope.data.transferValidated === "transferDenied") {
            return 1;
        } else if ($scope.Card.state === 0 && $scope.data.transfer && $scope.data.transferValidated === "transferGranted") {
            return 2;
        } else if ($scope.Card.state > 0) {
            if ($scope.data.typeOrder === "first") {
                if ($scope.data.unitType === "user" && $scope.data.selfService) {
                    return 3;
                } else if ($scope.data.unitType === "user" && !$scope.data.selfService) {
                    return 4;
                } else if ($scope.data.unitType === "pack" && $scope.data.selfService) {
                    return 5;
                } else if ($scope.data.unitType === "pack" && !$scope.data.selfService) {
                    return 6;
                }
            } else if ($scope.data.typeOrder === "up") {
                if ($scope.data.unitType === "user" && $scope.data.selfService) {
                    return 7;
                } else if ($scope.data.unitType === "user" && !$scope.data.selfService) {
                    return 4; // In that case we display the same checkout card as in 3
                } else if ($scope.data.unitType === "pack" && $scope.data.selfService) {
                    return 5; // In that case we display the same checkout card as in 4
                } else if ($scope.data.unitType === "pack" && !$scope.data.selfService) {
                    return 6; // In that case we display the same checkout card as in 5
                }
            } else if ($scope.data.typeOrder === "add") {
                if ($scope.data.unitType === "user" && $scope.data.selfService) {
                    return 8;
                }
            }
        }
    }

    $scope.Card.state = $scope.Card.goState();

    // Mapping the steps to the cards the represent them
    $scope.Card.activeMapping = [
        'checkAvailability-s1',
        'transferDenied',
        'checkAvailability-s2',
        'orderFirstUserSelf',
        'orderFirstUser',
        'orderFirstPackSelf',
        'orderFirstPack',
        'orderUpUserSelf',
        'orderAddUserSelf'
    ];


    $scope.Card.isActive = function () {
        return $scope.Card.activeMapping[$scope.Card.state];
    };

    $scope.Card.Active = $scope.Card.isActive();

    $scope.Card.update = function () {
        // Because the true and false value in the view are strings, they are always interpreted as true
        // We need a middleware that translate them back into real true/false values
        for (var prop in $scope.data) {
            // skip loop if the property is from prototype
            if (!$scope.data.hasOwnProperty(prop)) continue;

            // your code
            if ($scope.data[prop] === "true") {
                $scope.data[prop] = true;
            } else if ($scope.data[prop] === "false") {
                $scope.data[prop] = false;
            }
        }
        ;
        $scope.Card.state = $scope.Card.goState();
        $scope.Card.Active = $scope.Card.isActive();
    }


// Checking token
    $scope.token = '';

    // TO DO

    $scope.checkEligibility = function () {
        if ($scope.token) {
            if ($scope.token === "token") {
                $scope.data.transferValidated = "transferGranted";
                $scope.Card.update();
            } else {
                $scope.data.transferValidated = "transferDenied";
                $scope.Card.update();
            }
        }
    };

    $scope.validateTransfer = function () {
        $scope.Card.update();
        switchForm();
    }

// calculate price - type user

    $scope.deductLicense = function () {
        $scope.data.newQuantity--;
        $scope.data.newTotalPrice = $scope.data.newQuantity * $scope.data.newUnitPrice;
    }

    $scope.addLicense = function () {
        $scope.data.newQuantity++;
        $scope.data.newTotalPrice = $scope.data.newQuantity * $scope.data.newUnitPrice;
    }

// calculate price - type pack
    $scope.packsPrices = [
        {qty: 5, price: 50, option: "5 users pack"},
        {qty: 10, price: 100, option: "10 users pack"},
        {qty: 20, price: 200, option: "20 users pack"},
        {qty: 50, price: 250, option: "50 users pack"},
        {qty: 100, price: 350, option: "100 users pack"},
        {qty: 250, price: 450, option: "250 users pack"},
        {qty: 500, price: 550, option: "500 users pack"},
        {qty: 1000, price: 1250, option: "+1000 users pack"}
    ];
    // Defining the preselection
    // ZHIMIN, this will have to come from the backend
    if ($scope.unitType === 'pack') {
        $scope.data.newTotalPrice = $scope.packsPrices[2].price;
    }


    // Switching order type to upgrade quantities

    $scope.switchTypeOrder = function (type) {
        $scope.data.typeOrder = type;
        $scope.Card.update();
    }

    // Balance message

    $scope.balanceMessage = function () {
        if ($scope.data.balance > 0) {
            return "A credit of " + $scope.data.currency + $scope.data.balance + " will be applied to your invoice";
        } else if ($scope.data.balance < 0) {
            return "Your balance has a debit of " + $scope.data.currency + Math.abs($scope.data.balance) + " that will be applied to your next invoice";
        }
    }

    // Add

    $scope.data.oldquantity = $scope.data.newQuantity;

    $scope.data.Addquantity = 0;

    $scope.updateQty = function () {
        $scope.data.newQuantity = $scope.data.newQuantity + Number($scope.data.Addquantity);
    };


    // First order switch
    $scope.BCCswitchedOn = false;
    $scope.BDCswitchedOn = false;

    if ($scope.data.typeOrder === 'first') {
        $scope.BCCswitchedOn = true;
        $scope.BDCswitchedOn = true;
    }


    $scope.BCCisFirstswitcher = function () {
        $scope.BCCswitchedOn = !$scope.BCCswitchedOn;
    };

    $scope.BDCisFirstswitcher = function () {
        $scope.BDCswitchedOn = !$scope.BDCswitchedOn;
    };

}]);

$(function () {
    angular.bootstrap(document, ['app']);
});