    # -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProjectSubPekerjaan(models.Model):
    _name = "project.sub.pekerjaan"
    _description = "Sub Pekerjaan (RAP/PFC)"
    _order = "id asc"

    pekerjaan_id = fields.Many2one("project.pekerjaan", required=True, ondelete="cascade", index=True, copy=False)
    rap_state = fields.Selection(
        related="pekerjaan_id.rap_id.state",
        store=True,
        readonly=True,
    )
    name = fields.Char(required=True, copy=True)
    uom_id = fields.Many2one("uom.uom", copy=True)
    volume = fields.Float(default=1.0, copy=True)

    # === One2many detail (semua akan jadi PAGE di view) ===
    master_bahan_ids = fields.One2many("project.master.bahan", "sub_pekerjaan_id", copy=True)
    master_upah_ids = fields.One2many("project.master.upah", "sub_pekerjaan_id", copy=True)
    master_sewa_alat_ids = fields.One2many("project.master.sewa.alat", "sub_pekerjaan_id", copy=True)
    master_overhead_ids = fields.One2many("project.master.overhead", "sub_pekerjaan_id", copy=True)
    master_jasa_ids = fields.One2many("project.master.jasa", "sub_pekerjaan_id", copy=True)

    total_harga = fields.Float(compute="_compute_total_harga", store=True, readonly=True)

    @api.depends(
        "master_bahan_ids.total_harga",
        "master_upah_ids.total_harga",
        "master_sewa_alat_ids.total_harga",
        "master_overhead_ids.total_harga",
        "master_jasa_ids.total_harga",
    )
    def _compute_total_harga(self):
        for rec in self:
            total = 0.0
            total += sum(rec.master_bahan_ids.mapped("total_harga"))
            total += sum(rec.master_upah_ids.mapped("total_harga"))
            total += sum(rec.master_sewa_alat_ids.mapped("total_harga"))
            total += sum(rec.master_overhead_ids.mapped("total_harga"))
            total += sum(rec.master_jasa_ids.mapped("total_harga"))
            rec.total_harga = total

    def _ensure_parent_editable(self):
        for rec in self:
            if rec.pekerjaan_id.rap_id.state == "approved":
                raise UserError(_("Dokumen RAP/PFC sudah Approved, tidak bisa diubah."))

    def write(self, vals):
        self._ensure_parent_editable()
        return super().write(vals)

    def unlink(self):
        self._ensure_parent_editable()
        return super().unlink()
