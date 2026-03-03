# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    engineering_package_id = fields.Many2one(
        'engineering.package', 
        string='الباقة الهندسية (Package)',
        domain="[('building_type', 'in', [building_type, 'all']), ('active', '=', True)]"
    )
    
    package_features_html = fields.Html(
        string="مميزات الباقة (Package Features)", 
        compute="_compute_package_features_html",
        store=True
    )

    @api.depends('engineering_package_id')
    def _compute_package_features_html(self):
        """ Generates an HTML list of features for the selected package. """
        for order in self:
            if not order.engineering_package_id:
                order.package_features_html = False
                continue

            html = "<ul>"
            for feature in order.engineering_package_id.feature_ids:
                if feature.included:
                    html += f'<li><i class="fa fa-check text-success"/> {feature.name}</li>'
                else:
                    html += f'<li><i class="fa fa-times text-danger"/> <s>{feature.name}</s></li>'
            html += "</ul>"
            order.package_features_html = html

    @api.onchange('engineering_package_id')
    def _onchange_engineering_package_id(self):
        """
        When a package is selected, this function automatically:
        1. Clears any existing order lines.
        2. Adds the package's main product to the order lines.
        """
        if not self.engineering_package_id:
            # Clear lines if package is removed
            self.order_line = [(5, 0, 0)]
            return

        package = self.engineering_package_id
        if not package.product_id:
            raise UserError(_("This package '%s' does not have a related product. Please create one from the package form.") % package.name)

        # Remove all existing lines
        self.order_line = [(5, 0, 0)]
        
        # Add the new package product line
        self.order_line = [(0, 0, {
            'product_id': package.product_id.id,
            'name': package.product_id.name,
            'product_uom_qty': 1,
            'price_unit': package.list_price,
        })]
