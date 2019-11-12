odoo.define('weight_registry.set_weight', function (require) {
"use strict";

var core = require('web.core');
// var Widget = require('web.Widget');
var AbstractAction = require('web.AbstractAction');


var QWeb = core.qweb;
var _t = core._t;


var SetWeight = AbstractAction.extend({
    events: {
        "click .fa-truck": function() {
            // this.$('fa-truck').attr("disabled", "disabled");
            this.search_vehicle();
        },

        "click .o_weight_registry_sign_in_out_icon": function() {
            this.$('.o_weight_registry_sign_in_out_icon').attr("disabled", "disabled");
            this.update_registry();
        },
    },

    start: function () {
        var self = this;
        self.state = 'init'
        self.error = false;
        self.input_number = ''

        self.$el.html(QWeb.render("WeightRegistryMyMainMenu", {widget: self}));
    },

    search_vehicle: function () {
        var self = this;
        var vehicle_number = this.$('.input_vehicle_number').val();
        self.input_number = vehicle_number
        this._rpc({
            model: 'vehicle',
            method: 'search_read',
            args: [[['register', '=',vehicle_number]], []],
        })
        .then(function (res) {
            if (_.isEmpty(res) ) {
                self.error = true;
                self.state = 'init';
            }
            else {
                self.error = true;
                self.state = '1step'
                self.vehicle = res[0];
                
            }
            self.$el.html(QWeb.render("WeightRegistryMyMainMenu", {widget: self}));

        });
    },


    update_registry: function () {
        var self = this;
       
        this._rpc({
            model: 'weight.registry',
            method: 'set_weight_registry',
            args: [self.vehicle.id],
        })
        .then(function(result) {
            self.state = 'init'
            self.$el.html(QWeb.render("WeightRegistryMyMainMenu", {widget: self}));
        });
    },
});

core.action_registry.add('set_weight', SetWeight);

return SetWeight;

});
