
odoo.define('weight_registry.vehicle_kanban_view_handler', function(require) {
"use strict";

var KanbanRecord = require('web.KanbanRecord');

KanbanRecord.include({
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     * @private
     */
    _openRecord: function () {
        if (this.modelName === 'vehicle' && this.$el.parents('.o_weight_registry_kanban').length) {
                                            // needed to diffentiate : check in/out kanban view of employees <-> standard employee kanban view
            var action = {
                type: 'ir.actions.client',
                name: 'Confirm',
                tag: 'weight_registry_kiosk_confirm',
                employee_id: this.record.id.raw_value,
                employee_name: this.record.name.raw_value,
                employee_state: this.record.weight_registry_state.raw_value,
            };
            this.do_action(action);
        } else {
            this._super.apply(this, arguments);
        }
    }
});

});
