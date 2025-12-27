# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ConstructionPekerjaanTemplate(models.Model):
    _name = "construction.pekerjaan.template"
    _description = "Template Pekerjaan (Reusable untuk RAP/PFC)"
    _order = "code, id"

    name = fields.Char(required=True, copy=True)
    code = fields.Char(required=True, copy=True, index=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, index=True)
    notes = fields.Text()

    sub_template_ids = fields.One2many(
        "construction.sub.pekerjaan.template",
        "pekerjaan_template_id",
        string="Sub Pekerjaan Template",
        copy=True,
    )

    _sql_constraints = [
        ("construction_pekerjaan_template_code_uniq", "unique(code, company_id)", "Code template harus unik per company."),
    ]

    def name_get(self):
        res = []
        for rec in self:
            display = f"{rec.code} - {rec.name}" if rec.code else rec.name
            res.append((rec.id, display))
        return res


class ConstructionSubPekerjaanTemplate(models.Model):
    _name = "construction.sub.pekerjaan.template"
    _description = "Template Sub Pekerjaan (Reusable untuk RAP/PFC)"
    _order = "sequence, id"

    pekerjaan_template_id = fields.Many2one(
        "construction.pekerjaan.template",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )

    sequence = fields.Integer(default=10)
    name = fields.Char(required=True, copy=True)
    uom_id = fields.Many2one("uom.uom", string="UoM", copy=True)
    default_volume = fields.Float(string="Default Volume", default=1.0, copy=True)

    line_ids = fields.One2many(
        "construction.sub.template.line",
        "sub_template_id",
        string="Lines",
        copy=True,
    )

    def name_get(self):
        res = []
        for rec in self:
            if rec.pekerjaan_template_id and rec.pekerjaan_template_id.code:
                display = f"{rec.pekerjaan_template_id.code} / {rec.name}"
            else:
                display = rec.name
            res.append((rec.id, display))
        return res


class ConstructionSubTemplateLine(models.Model):
    _name = "construction.sub.template.line"
    _description = "Template Line Sub Pekerjaan (Bahan/Upah/Sewa Alat/Overhead/Jasa)"
    _order = "id asc"

    sub_template_id = fields.Many2one(
        "construction.sub.pekerjaan.template",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )

    product_id = fields.Many2one(
        "product.product",
        string="Item",
        required=True,
        index=True,
        copy=True,
    )
    type_master_data = fields.Selection(
        related="product_id.type_master_data",
        store=True,
        readonly=True,
    )

    volume = fields.Float(default=1.0, copy=True)
    harga_satuan_default = fields.Float(string="Default Unit Price", copy=True)

    code = fields.Char(related="product_id.default_code", store=True, readonly=True)
    uom_id = fields.Many2one("uom.uom", related="product_id.uom_id", store=True, readonly=True)

    @api.constrains("product_id")
    def _check_product_type_master_data(self):
        for rec in self:
            if rec.product_id and not rec.product_id.type_master_data:
                raise ValidationError(_("Product harus punya Type Master Data (bahan/upah/overhead/jasa/sewa_alat)."))
