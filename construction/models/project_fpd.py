# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectFpd(models.Model):
    _name = "project.fpd"
    _description = "FPD"
    _order = "id desc"

    name = fields.Char(string="FPD No", default=lambda self: _("New"), copy=False, readonly=True)

    rap_id = fields.Many2one("project.rap", string="RAP", required=True, ondelete="cascade", index=True)
    project_id = fields.Many2one("project.project", string="Project", required=True, ondelete="restrict", index=True)

    pekerjaan_id = fields.Many2one(
        "project.pekerjaan",
        string="Pekerjaan",
        required=True,
        ondelete="restrict",
        domain="[('rap_id', '=', rap_id)]",
    )
    sub_pekerjaan_id = fields.Many2one(
        "project.sub.pekerjaan",
        string="Sub-Pekerjaan",
        required=True,
        ondelete="restrict",
        domain="[('pekerjaan_id', '=', pekerjaan_id)]",
    )

    line_ids = fields.One2many("project.fpd.line", "fpd_id", string="Lines", copy=True)

    currency_id = fields.Many2one(related="project_id.currency_id", store=True, readonly=True)
    amount_total = fields.Monetary(
        string="Total",
        compute="_compute_amount_total",
        store=True,
        currency_field="currency_id",
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirmed"),
            ("approve", "Approved"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        default="draft",
    )

    @api.depends("line_ids.total_price")
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped("total_price"))

    # -----------------------
    # Workflow Actions
    # -----------------------
    def action_confirm(self):
        for rec in self:
            if rec.state != "draft":
                continue
            if not rec.line_ids:
                raise UserError(_("FPD Lines masih kosong."))
            rec.state = "confirm"

    def action_approve(self):
        for rec in self:
            if rec.state != "confirm":
                continue
            if not rec.line_ids:
                raise UserError(_("FPD Lines masih kosong."))
            rec.state = "approve"

    def action_cancel(self):
        for rec in self:
            if rec.state == "cancel":
                continue
            rec.state = "cancel"

    def action_set_draft(self):
        for rec in self:
            rec.state = "draft"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("project.fpd") or _("New")
        return super().create(vals_list)


class ProjectFpdLine(models.Model):
    _name = "project.fpd.line"
    _description = "FPD Line"
    _order = "id asc"

    fpd_id = fields.Many2one("project.fpd", string="FPD", required=True, ondelete="cascade")

    product_tmpl_id = fields.Many2one("product.template", string="Product", required=True)
    qty = fields.Float(string="Qty", default=1.0)
    uom_id = fields.Many2one("uom.uom", string="UoM", required=True)
    price_unit = fields.Float(string="Price Unit", default=0.0)
    total_price = fields.Float(string="Total Price", compute="_compute_total_price", store=True)

    @api.depends("qty", "price_unit")
    def _compute_total_price(self):
        for line in self:
            line.total_price = (line.qty or 0.0) * (line.price_unit or 0.0)

    @api.onchange("product_tmpl_id")
    def _onchange_product_tmpl_id(self):
        for line in self:
            if line.product_tmpl_id:
                line.uom_id = line.product_tmpl_id.uom_id
                # optional: default harga dari construction_price bila ada
                if "construction_price" in line.product_tmpl_id._fields and not line.price_unit:
                    line.price_unit = line.product_tmpl_id.construction_price or 0.0
