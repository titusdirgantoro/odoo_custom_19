
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    rap_id = fields.Many2one(
        "project.rap",
        string="RAP",
        index=True,
        copy=False,
    )
    pekerjaan_id = fields.Many2one(
        "project.pekerjaan",
        string="Pekerjaan",
        copy=False,
    )
    sub_pekerjaan_id = fields.Many2one(
        "project.sub.pekerjaan",
        string="Sub-Pekerjaan",
        copy=False,
    )

    project_id = fields.Many2one(
        related="rap_id.project_id",
        string="Proyek",
        store=True,
        readonly=True,
    )

    deliver_to_id = fields.Many2one(
        "res.partner",
        string="Deliver To",
        copy=False,
    )
    expected_arrival = fields.Datetime(
        string="Expected Arrival",
        copy=False,
    )

    allowed_product_tmpl_ids = fields.Many2many(
        "product.template",
        string="Allowed Products (Templates)",
        compute="_compute_allowed_product_tmpl_ids",
        compute_sudo=True,
    )

    is_work_order = fields.Boolean(
        string="Is Work Order",
        default=False,
        index=True,
        copy=False,
        help="Jika dicentang, Purchase Order ini dianggap Work Order (WO) dan akan memakai sequence WO.",
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        """Jika is_work_order=True, pakai sequence berbeda (purchase.work.order)."""
        for vals in vals_list:
            if vals.get("is_work_order"):
                name = vals.get("name")
                # Odoo biasanya default 'New'
                if not name or name == "New" or name == "/":
                    vals["name"] = self.env["ir.sequence"].next_by_code("purchase.work.order") or "New"
        return super().create(vals_list)
    
    @api.depends("sub_pekerjaan_id", "is_work_order")
    def _compute_allowed_product_tmpl_ids(self):
        for order in self:
            sub = order.sub_pekerjaan_id
            tmpl_ids = []

            if sub:
                tmpl_ids = (
                    sub.master_bahan_ids.mapped("product_id").ids
                    + sub.master_upah_ids.mapped("product_id").ids
                    + sub.master_sewa_alat_ids.mapped("product_id").ids
                    + sub.master_overhead_ids.mapped("product_id").ids
                    + sub.master_jasa_ids.mapped("product_id").ids
                )

                # WO hanya service
                if order.is_work_order and tmpl_ids:
                    tmpl_ids = self.env["product.template"].browse(list(set(tmpl_ids))).filtered(
                        lambda t: t.type == "service"
                    ).ids

                order.allowed_product_tmpl_ids = [(6, 0, list(set(tmpl_ids)))]
            else:
                # kalau tidak pakai sub_pekerjaan: kosongkan allowed
                order.allowed_product_tmpl_ids = [()]

    @api.onchange("rap_id")
    def _onchange_rap_id(self):
        for order in self:
            order.pekerjaan_id = False
            order.sub_pekerjaan_id = False

    @api.onchange("pekerjaan_id")
    def _onchange_pekerjaan_id(self):
        for order in self:
            order.sub_pekerjaan_id = False

    @api.onchange("sub_pekerjaan_id")
    def _onchange_sub_pekerjaan_id(self):
        for order in self:
            if order.sub_pekerjaan_id:
                if not order.pekerjaan_id:
                    order.pekerjaan_id = order.sub_pekerjaan_id.pekerjaan_id
                if not order.rap_id:
                    order.rap_id = order.sub_pekerjaan_id.pekerjaan_id.rap_id


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    sub_pekerjaan_id = fields.Many2one(
        related="order_id.sub_pekerjaan_id",
        store=True,
        readonly=True,
    )
    allowed_product_tmpl_ids = fields.Many2many(
        related="order_id.allowed_product_tmpl_ids",
        readonly=True,
    )
    is_work_order = fields.Boolean(related='order_id.is_work_order')

    @api.constrains("product_id")
    def _check_work_order_service_only(self):
        for line in self:
            if line.order_id.is_work_order and line.product_id and line.product_id.type != "service":
                raise ValidationError(
                    "Work Order (WO) hanya boleh berisi product type Service."
                )