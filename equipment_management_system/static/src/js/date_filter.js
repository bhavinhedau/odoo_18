/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";

export class DateFilter extends Component {
    static template = "equipment_management_system.DateFilter";
    static components = { Dropdown, DropdownItem };

    setup() {
        this.action = useService("action");
        this.state = useState({
            selectedLabel: "2025", // This would be dynamic in a real app
        });
    }

    async onSelectPeriod(periodType) {
        // This triggers the Odoo search domain updates
        let domain = [];
        if (periodType === 'year') {
            domain = [['create_date', '>=', '2025-01-01'], ['create_date', '<=', '2025-12-31']];
        }
        // Logic to reload the view with the new domain
        this.env.bus.trigger("RELAYER_SEARCH", { domain });
    }
}