const erp_onl = frappe.listview_settings["Sales Invoice"].onload;
frappe.listview_settings["Sales Invoice"].onload = function (list_view) {
    if (erp_onl) {
        erp_onl(list_view);
    }
    list_view.page.add_action_item(__("Generate IRN"), function (event) {
        let selected = [];

        for (let check of cur_list.$checks) {
            selected.push(check.dataset.name);
        }
        frappe.call({
            method: "gst_india.cleartax_integration.API.irn.bulk_irn",
            args: {
                data: selected
            },
            type: "POST",
            callback: function (r) {
                frappe.msgprint("IRN is being Generated!")
                list_view.refresh();
            }
        })

    });
    list_view.page.add_action_item(__("Generate EWB"), function (event) {
        let selected = [];

        for (let check of cur_list.$checks) {
            selected.push(check.dataset.name);
        }
        frappe.call({
            method: "gst_india.cleartax_integration.API.ewb.bulk_ewb",
            args: {
                data: selected
            },
            type: "POST",
            callback: function (r) {
                frappe.msgprint("EWB is being Generated!")
                list_view.refresh();
            }
        })

    });

    list_view.page.add_action_item(__("GST Invoice"), function (event) {
        let selected = [];

        for (let check of cur_list.$checks) {
            selected.push(check.dataset.name);
        }
        frappe.call({
            method: "gst_india.cleartax_integration.API.gst.bulk_sales_gst",
            args: {
                data: selected
            },
            type: "POST",
            callback: function (r) {
                frappe.msgprint("GST Invoices are scheduled to be genereated!")
                list_view.refresh();
            }
        })

    });

};
