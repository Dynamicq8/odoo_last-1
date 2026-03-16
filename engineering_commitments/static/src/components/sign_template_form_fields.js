/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { SignTemplateForm } from "@sign/views/sign_template_form/sign_template_form";

patch(SignTemplateForm.prototype, {
    setup() {
        super.setup();
        // This 'setup' method is called when the component is initialized.
        // You would typically use this for more complex state management.
        // For simple visibility based on another field, the attrs in XML
        // are replaced by a direct connection in the component template.
        // However, Odoo 17+ views often handle simple boolean visibility
        // in the XML without needing complex JS if the field is bound
        // to the view. Let's try the XML method first.
    },
});
