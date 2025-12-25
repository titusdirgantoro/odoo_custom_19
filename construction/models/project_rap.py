# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProjectRap(models.Model):
    _name = "project.rap"
    _description = "RAP / PFC"
    _order = "id desc"

    name = fields.Char(required=True, copy=True)
    type = fields.Selection(
        [("rap", "RAP"), ("pfc", "PFC")],
        default="rap",
        required=True,
        copy=True,
    )

    project_id = fields.Many2one("project.project", required=True, index=True, copy=False)

    nilai_kontrak = fields.Float(related="project_id.nilai_kontrak", readonly=True)
    project_manager_id = fields.Many2one(related="project_id.user_id", readonly=True)

    pekerjaan_ids = fields.One2many("project.pekerjaan", "rap_id", copy=True)

    total_nilai_rap = fields.Float(compute="_compute_total", store=True, readonly=True)
    selisih_kon_rap = fields.Float(compute="_compute_total", store=True, readonly=True)

    total_realisasi = fields.Float(default=0.0, copy=False)
    notes = fields.Text(copy=True)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("request_approval", "Request Approval"),
            ("approved", "Approved"),
        ],
        default="draft",
        copy=False,
    )
    user_request_id = fields.Many2one("res.users", readonly=True, copy=False)
    user_approve_id = fields.Many2one("res.users", readonly=True, copy=False)
    tanggal_disetujui = fields.Datetime(readonly=True, copy=False)
    comment = fields.Text(copy=False)

    @api.depends("pekerjaan_ids.total_harga", "nilai_kontrak")
    def _compute_total(self):
        for rec in self:
            total = sum(rec.pekerjaan_ids.mapped("total_harga"))
            rec.total_nilai_rap = total
            rec.selisih_kon_rap = (rec.nilai_kontrak or 0.0) - total

    # === workflow ===
    def action_request_approval(self):
        for rec in self:
            if not rec.pekerjaan_ids:
                raise UserError(_("Tidak bisa Request Approval: belum ada Pekerjaan."))
            rec.user_request_id = self.env.user.id
            rec.state = "request_approval"

    def action_approve(self):
        for rec in self:
            # Ganti rule group sesuai kebutuhanmu (misal group custom)
            if not self.env.user.has_group("base.group_system"):
                raise UserError(_("Hanya user tertentu yang boleh Approve (silakan sesuaikan group)."))
            rec.user_approve_id = self.env.user.id
            rec.tanggal_disetujui = fields.Datetime.now()
            rec.state = "approved"

    def action_set_draft(self):
        for rec in self:
            if rec.state == "approved" and not self.env.user.has_group("base.group_system"):
                raise UserError(_("Hanya user tertentu yang boleh Reset dari Approved."))
            rec.state = "draft"

    # === copy wizard ===
    def action_open_copy_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Copy RAP/PFC"),
            "res_model": "project.rap.copy.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_source_rap_id": self.id,
                "default_target_type": self.type,
                "default_new_name": f"{self.name} (Copy)",
            },
        }

    # === lock editing ===
    def _ensure_editable(self):
        for rec in self:
            if rec.state == "approved":
                raise UserError(_("Dokumen RAP/PFC sudah Approved, tidak bisa diubah."))

    def write(self, vals):
        # tetap izinkan perubahan metadata approval/state via action
        editable_keys = {"state", "user_request_id", "user_approve_id", "tanggal_disetujui"}
        if any(k not in editable_keys for k in vals.keys()):
            self._ensure_editable()
        return super().write(vals)

    def unlink(self):
        self._ensure_editable()
        return super().unlink()
