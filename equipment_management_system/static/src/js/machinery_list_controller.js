/** @odoo-module **/
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";

export class MachineryListController extends ListController {

    onSelectPeriod(periodType) {
        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth() + 1;

        let domain = [];

        if (periodType === "year") {
            domain = [
                ["create_date", ">=", `${year}-01-01 00:00:00`],
                ["create_date", "<=", `${year}-12-31 23:59:59`],
            ];
        }

        if (periodType === "month") {
            const start = new Date(year, month - 1, 1);
            const end = new Date(year, month, 0);

            domain = [
                ["create_date", ">=", start.toISOString().slice(0, 10) + " 00:00:00"],
                ["create_date", "<=", end.toISOString().slice(0, 10) + " 23:59:59"],
            ];
        }

        // Proper Odoo 19 API
        this.env.searchModel.setDomain(domain);
    }
}

export const MachineryListView = {
    ...listView,
    Controller: MachineryListController,
    buttonTemplate: "ems.MachineryListButtons",
};

registry.category("views").add(
    "machinery_list_view_filter",
    MachineryListView
);
