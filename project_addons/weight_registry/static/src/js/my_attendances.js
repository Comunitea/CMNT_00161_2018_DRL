odoo.define('weight_registry.my_attendances', function (require) {
"use strict";

var core = require('web.core');
var Widget = require('web.Widget');

var QWeb = core.qweb;
var _t = core._t;


var MyAttendances = Widget.extend({
    events: {
        "click .o_weight_registry_sign_in_out_icon": function() {
            this.$('.o_weight_registry_sign_in_out_icon').attr("disabled", "disabled");
            this.update_weight_registry();
        },
    },

    start: function () {
        var self = this;

        var def = this._rpc({
                model: 'vehicle',
                method: 'search_read',
                args: [[['user_id', '=', this.getSession().uid]], ['weight_registry_state', 'name']],
            })
            .then(function (res) {
                self.employee = res[0];
                self.$el.html(QWeb.render("WeightRegistryMyMainMenu", {widget: self}));
                if (_.isEmpty(res) ) {
                    return;
                }

            });

        return $.when(def, this._super.apply(this, arguments));
    },

    update_weight_registry: function () {
        var self = this;
        this._rpc({
                model: 'vehicle',
                method: 'weight_registry_manual',
                args: [[self.employee.id], 'weight_registry.weight_registry_action_my_attendances'],
            })
            .then(function(result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_warn(result.warning);
                }
            });
    },
});

core.action_registry.add('weight_registry_my_attendances', MyAttendances);

return MyAttendances;

});
