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
        self.state = 'weight1'
        self.error = false;
        self.input_number = ''
        self.weight = 1000.0

        self.$el.html(QWeb.render("WeightRegistryWidget", {widget: self}));
    },

    search_vehicle: function () {
        var self = this;
        var vehicle_number = this.$('.input_vehicle_number').val();
        self.input_number = vehicle_number

        this._rpc({
            // model: 'vehicle',
            // method: 'search_read',
            // args: [[['register', '=',vehicle_number]], []],
            model: 'vehicle',
            method: 'get_vehicle_data',
            args: [vehicle_number],
        })
        .then(function (res) {
            if (_.isEmpty(res) ) {
                self.error = true;
                self.state = 'weight1';
            }
            else {
                self.error = false;
                self.state = 'weight2'
                self.vehicle = res;
                
            }
            self.$el.html(QWeb.render("WeightRegistryWidget", {widget: self}));

        });
    },


    update_registry: function () {
        var self = this;
        var weight_field = this.$('#weight-field').val();
        self.weight = weight_field * 1.0

        var deposits = []
        this.$('.wh-deposits-table tbody tr').each(function(){
            var deposit_id = $(this).attr('dep')
            if (deposit_id){
            var check = $(this).find('td').eq(2).find('input').is(':checked')
            deposits.push({id: deposit_id, check: check})
            console.log(this)
            }
        });
        var vehicles = []
        this.$('.wh-vehicles-table tbody tr').each(function(){
            var vehicle_id = $(this).attr('veh')
            vehicles.push({id: vehicle_id})
            console.log(this)
        });
        vehicles = []
        for (var v in self.vehicle.vehicle_ids){
            vehicles.push({id: self.vehicle.vehicle_ids[v]['id'], 'register': self.vehicle.vehicle_ids[v]['register']})
        }
        //var vehicles = self.vehicle.vehicle_ids
        this._rpc({
            model: 'weight.registry',
            method: 'set_weight_registry',
            args: [self.vehicle.id, self.weight, deposits, vehicles],
        })
        .then(function(result) {
            self.state = 'weight1'
            self.$el.html(QWeb.render("WeightRegistryWidget", {widget: self}));
        });
    },
});

core.action_registry.add('set_weight', SetWeight);

return SetWeight;

});
