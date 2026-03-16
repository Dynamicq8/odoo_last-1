/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { registry } from "@web/core/registry";

// Extend the FormController for sign.template forms
export class SignTemplateFormControllerCustom extends FormController {
    // Override the get_form_data method or add specific logic here if needed
    // For simple field visibility, we might just need to pass props to the view.
    // The main change is in the client-side rendering.
}

// Register a new form view for sign.template if needed, or patch the existing one.
// For visibility, the easiest is to patch the component directly.

// Let's create a custom component for the fields instead of patching the whole form controller.
// This is a cleaner approach in Odoo 17+ for specific field behavior.

// Assuming the sign_template_view_form uses a standard FormRenderer.
// We need to extend/patch the SignTemplateForm component (if it exists) or a generic FormRenderer
// to add our custom visibility logic. This can be complex depending on Odoo's internal structure.

// A simpler approach might be to leverage a custom widget or an extension point.
// However, the `attrs` replacement for conditional visibility directly within the form view
// is usually handled by providing a custom `FormRenderer` or patching a specific field widget.

// Let's assume you just want to hide the building_type if is_commitment is false.
// This means we need access to the record's values in the template.

// --- The most common Odoo 17+ way to do conditional visibility in a custom component is: ---
// 1. Create a custom template for your fields (or section)
// 2. Wrap your fields in an <t-if> condition.

// This means *replacing* the <field> definitions for your custom group in XML,
// not just adding to it. This requires more extensive modification.

// Given the complexity of Odoo 17+ client-side changes, for a simple
// conditional visibility, you might be able to get away with a custom widget
// or by dynamically manipulating the DOM (less recommended).

// Let's try to make a dedicated component for the "Engineering Commitment Settings" group.
