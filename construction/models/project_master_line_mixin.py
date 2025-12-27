# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProjectMasterLineMixin(models.AbstractModel):
    _name = "project.master.line.mixin"
    _description = "Mixin: Master Line RAP (Bahan/Upah/Sewa Alat/Overhead/Jasa)"
    _order = "id asc"

    sub_pekerjaan_id = fields.Many2one(
        "project.sub.pekerjaan",
        string="Sub Pekerjaan",
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

    template_line_id = fields.Many2one(
        'construction.sub.template.line',
        string='Template Line',
        copy=False,
        readonly=True,
    )

    code = fields.Char(related="product_id.default_code", store=True, readonly=True)
    uom_id = fields.Many2one("uom.uom", related="product_id.uom_id", store=True, readonly=True)

    volume = fields.Float(default=1.0, copy=True)
    harga_satuan = fields.Float(default=0.0, copy=True)

    total_harga = fields.Float(compute="_compute_total_harga", store=True)

    @api.depends("volume", "harga_satuan")
    def _compute_total_harga(self):
        for rec in self:
            rec.total_harga = (rec.volume or 0.0) * (rec.harga_satuan or 0.0)

    def _ensure_parent_editable(self):
        for rec in self:
            rap = rec.sub_pekerjaan_id.pekerjaan_id.rap_id
            if rap and rap.state == "approved":
                raise UserError(_("Dokumen RAP/PFC sudah Approved, tidak bisa diubah."))

    def write(self, vals):
        self._ensure_parent_editable()
        return super().write(vals)

    def unlink(self):
        self._ensure_parent_editable()
        return super().unlink()
