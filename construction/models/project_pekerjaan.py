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

    template_id = fields.Many2one(
        'construction.pekerjaan.template',
        string='Pekerjaan Template',
        copy=False,
        index=True,
    )
    name = fields.Char(required=True, copy=True)
    code = fields.Char(required=True, copy=True, index=True)

    sub_pekerjaan_ids = fields.One2many("project.sub.pekerjaan", "pekerjaan_id", copy=True)

    total_harga = fields.Float(string="Total Harga Pekerjaan",compute="_compute_total_harga", store=True)

    _sql_constraints = [
        ("uniq_rap_code", "unique(rap_id, code)", "Code pekerjaan harus unik dalam 1 dokumen RAP/PFC."),
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
