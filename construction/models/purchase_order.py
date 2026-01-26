
from odoo import models, fields, api


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

    @api.depends("sub_pekerjaan_id")
    def _compute_allowed_product_tmpl_ids(self):
        for order in self:
            tmpl_ids = []
            sub = order.sub_pekerjaan_id
            if sub:
                # SAFE: gabung list python, bukan union recordset
                all_lines = (
                    list(sub.master_bahan_ids)
                    + list(sub.master_upah_ids)
                    + list(sub.master_sewa_alat_ids)
                    + list(sub.master_overhead_ids)
                    + list(sub.master_jasa_ids)
                )
                tmpl_ids = [ml.product_id.id for ml in all_lines if ml.product_id]
            order.allowed_product_tmpl_ids = [(6, 0, list(set(tmpl_ids)))] if sub else [()]

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