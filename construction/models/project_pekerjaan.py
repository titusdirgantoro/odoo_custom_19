# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProjectPekerjaan(models.Model):
    _name = "project.pekerjaan"
    _description = "Pekerjaan (RAP/PFC)"
    _order = "id asc"

    rap_id = fields.Many2one("project.rap", required=True, ondelete="cascade", index=True, copy=False)
    rap_state = fields.Selection(
        related="rap_id.state",
        store=True,
        readonly=True,
    )
    name = fields.Char(required=True, copy=True)
    code = fields.Char(copy=True)

    sub_pekerjaan_ids = fields.One2many("project.sub.pekerjaan", "pekerjaan_id", copy=True)

    total_harga = fields.Float(compute="_compute_total_harga", store=True, readonly=True)

    _sql_constraints = [
        ("code_uniq_per_rap", "unique(rap_id, code)", "Code Pekerjaan harus unik per dokumen."),
    ]

    @api.depends("sub_pekerjaan_ids.total_harga")
    def _compute_total_harga(self):
        for rec in self:
            rec.total_harga = sum(rec.sub_pekerjaan_ids.mapped("total_harga"))

    def _ensure_parent_editable(self):
        for rec in self:
            if rec.rap_id.state == "approved":
                raise UserError(_("Dokumen RAP/PFC sudah Approved, tidak bisa diubah."))

    def write(self, vals):
        self._ensure_parent_editable()
        return super().write(vals)

    def unlink(self):
        self._ensure_parent_editable()
        return super().unlink()
