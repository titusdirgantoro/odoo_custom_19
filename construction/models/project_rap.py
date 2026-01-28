# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

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

    total_nilai_rap = fields.Float(compute="_compute_total", store=True)
    selisih_kon_rap = fields.Float(compute="_compute_total", store=True)
    total_nilai_pfc = fields.Float(
        string="Total Nilai PFC",
        compute="_compute_total_pfc",
        store=True,
    )

    selisih_kon_pfc = fields.Float(
        string="Selisih Kontrak PFC",
        compute="_compute_total_pfc",
        store=True,
    )

    total_realisasi = fields.Float(default=0.0)
    notes = fields.Text()

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("request_approval", "Request Approval"),
            ("approved", "Approved"),
        ],
        default="draft",
        tracking=True,
        copy=False,
    )

    user_request_id = fields.Many2one("res.users", readonly=True, copy=False)
    user_approve_id = fields.Many2one("res.users", readonly=True, copy=False)
    tanggal_disetujui = fields.Datetime(readonly=True, copy=False)
    comment = fields.Text(copy=False)
    purchase_order_count = fields.Integer(
        string="Purchase Orders",
        compute="_compute_purchase_order_count",
    )
    rap_origin_id = fields.Many2one(
        "project.rap",
        string="Source RAP",
        index=True,
        copy=False,
        readonly=True,
        domain=[("type", "=", "rap")],
        help="RAP source document that generated this PFC.",
    )
    pfc_ids = fields.One2many(
        "project.rap",
        "rap_origin_id",
        string="PFC",
        copy=False,
        readonly=True,
    )
    pfc_count = fields.Integer(string="PFC", compute="_compute_pfc_count")
    fpd_ids = fields.One2many("project.fpd", "rap_id", string="FPD Documents")
    fpd_count = fields.Integer(string="FPD", compute="_compute_fpd_count")
    total_nilai_pfc_on_rap = fields.Float(
        string="Total Nilai PFC on RAP",
        compute="_compute_total_nilai_pfc",
        store=True,
    )
    work_order_count = fields.Integer(
        string="Work Orders",
        compute="_compute_work_order_count",
    )

    @api.depends("pekerjaan_ids.total_harga", "nilai_kontrak", "type", "name")
    def _compute_total_pfc(self):
        for rec in self:
            if rec.type != "pfc":
                rec.total_nilai_pfc = 0.0
                rec.selisih_kon_pfc = 0.0
                continue

            total = sum(rec.pekerjaan_ids.mapped("total_harga"))
            rec.total_nilai_pfc = total
            rec.selisih_kon_pfc = (rec.nilai_kontrak or 0.0) - total

    @api.depends("pfc_ids.total_nilai_rap", "type")
    def _compute_total_nilai_pfc(self):
        for rec in self:
            if rec.type != "rap":
                rec.total_nilai_pfc_on_rap = 0.0
                continue
            rec.total_nilai_pfc_on_rap = sum(rec.pfc_ids.mapped("total_nilai_rap"))


    def _compute_fpd_count(self):
        for rec in self:
            rec.fpd_count = len(rec.fpd_ids)

    def action_open_fpd(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("FPD"),
            "res_model": "project.fpd",
            "view_mode": "list,form",
            "domain": [("rap_id", "=", self.id)],
            "context": {"default_rap_id": self.id, "default_project_id": self.project_id.id},
            "target": "current",
        }

    def action_create_fpd(self):
        self.ensure_one()
        if not self.project_id:
            raise UserError(_("RAP belum memiliki Project."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Create FPD"),
            "res_model": "project.rap.create.fpd.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_rap_id": self.id,
                "default_project_id": self.project_id.id,
            },
        }

    def _compute_pfc_count(self):
        for rec in self:
            rec.pfc_count = len(rec.pfc_ids) if rec.type == "rap" else 0

    def action_view_pfcs(self):
        """Smart button on RAP to open all PFC linked to this RAP."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("PFC"),
            "res_model": "project.rap",
            "view_mode": "list,form",
            "domain": [("rap_origin_id", "=", self.id), ("type", "=", "pfc")],
            "context": {
                "default_type": "pfc",
                "default_project_id": self.project_id.id if self.project_id else False,
                "default_rap_origin_id": self.id,
            },
            "target": "current",
        }

    def action_create_pfc(self):
        """Create PFC from RAP (copy structure & lines), link it back to RAP."""
        self.ensure_one()
        if self.type != "rap":
            raise UserError(_("Create PFC hanya bisa dilakukan dari dokumen RAP."))
        if not self.id:
            raise UserError(_("Silakan simpan dokumen terlebih dahulu."))
        if self.state != "approved":
            raise UserError(_("PFC hanya boleh dibuat saat RAP sudah Approved."))

        # Generate readable unique name
        base = f"PFC - {self.name}"
        existing = self.search_count([
            ("type", "=", "pfc"),
            ("rap_origin_id", "=", self.id),
        ])
        new_name = base if existing == 0 else f"{base} ({existing + 1})"

        # NOTE: copy() akan ikut menyalin pekerjaan/sub pekerjaan/master lines (copy=True)
        pfc = self.copy({
            "name": new_name,
            "type": "pfc",
            "project_id": self.project_id.id,  # penting karena project_id copy=False
            "rap_origin_id": self.id,
            "state": "draft",
            "user_request_id": False,
            "user_approve_id": False,
            "tanggal_disetujui": False,
            "comment": False,
        })

        return {
            "type": "ir.actions.act_window",
            "name": _("PFC"),
            "res_model": "project.rap",
            "view_mode": "form",
            "res_id": pfc.id,
            "target": "current",
        }
    
    def _compute_purchase_order_count(self):
        PurchaseOrder = self.env["purchase.order"]
        for rec in self:
            rec.purchase_order_count = PurchaseOrder.search_count([
                ("rap_id", "=", rec.id),
                ("is_work_order", "=", False),
            ])

    def _compute_work_order_count(self):
        PurchaseOrder = self.env["purchase.order"]
        for rec in self:
            rec.work_order_count = PurchaseOrder.search_count([
                ("rap_id", "=", rec.id),
                ("is_work_order", "=", True),
            ])

    def action_view_purchase_orders(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Purchase Orders"),
            "res_model": "purchase.order",
            "view_mode": "list,form",
            "domain": [("rap_id", "=", self.id), ("is_work_order", "=", False)],
            "context": {
                "default_rap_id": self.id,
                "default_project_id": self.project_id.id if self.project_id else False,
            },
            "target": "current",
        }

    def action_open_create_wo_wizard(self):
        self.ensure_one()
        if not self.id:
            raise UserError(_("Silakan simpan dokumen terlebih dahulu."))

        if self.state != "approved":
            raise UserError(_("WO hanya boleh dibuat saat RAP sudah Approved."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Create Work Order"),
            "res_model": "project.rap.create.wo.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_rap_id": self.id,
            },
        }
        
    def action_view_work_orders(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Work Orders"),
            "res_model": "purchase.order",
            "view_mode": "list,form",
            "domain": [("rap_id", "=", self.id), ("is_work_order", "=", True)],
            "context": {
                "default_rap_id": self.id,
                "default_project_id": self.project_id.id if self.project_id else False,
                "default_is_work_order": True,
            },
            "target": "current",
        }


    @api.constrains("project_id", "type")
    def _check_one_rap_per_project(self):
        """Fallback + pesan lebih jelas (dan aman jika SQL partial unique tidak didukung)."""
        for rec in self:
            if rec.type != "rap" or not rec.project_id:
                continue

            cnt = self.search_count([
                ("id", "!=", rec.id),
                ("project_id", "=", rec.project_id.id),
                ("type", "=", "rap"),
            ])
            if cnt:
                raise ValidationError(_("Satu project hanya boleh memiliki 1 dokumen RAP."))
            
    @api.depends("pekerjaan_ids.total_harga", "nilai_kontrak")
    def _compute_total(self):
        for rec in self:
            total = sum(rec.pekerjaan_ids.mapped("total_harga"))
            rec.total_nilai_rap = total
            rec.selisih_kon_rap = (rec.nilai_kontrak or 0.0) - total

    def action_open_create_po_wizard(self):
        self.ensure_one()
        if not self.id:
            raise UserError(_("Silakan simpan dokumen terlebih dahulu."))

        if self.state != "approved":
            raise UserError(_("PO hanya boleh dibuat saat RAP sudah Approved."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Create Purchase Order"),
            "res_model": "project.rap.create.po.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_rap_id": self.id,
            },
        }
    
    def action_request_approval(self):
        for rec in self:
            if not rec.pekerjaan_ids:
                raise UserError(_("Tidak bisa Request Approval tanpa pekerjaan."))
            rec.write(
                {
                    "state": "request_approval",
                    "user_request_id": self.env.user.id,
                }
            )

    def action_approve(self):
        for rec in self:
            if rec.state != "request_approval":
                continue
            # NOTE: ini masih rule sederhana, silakan sesuaikan group/flow approval sesuai kebutuhan
            if not self.env.user.has_group("base.group_system"):
                raise UserError(_("Hanya Administrator yang bisa approve dokumen ini."))
            rec.write(
                {
                    "state": "approved",
                    "user_approve_id": self.env.user.id,
                    "tanggal_disetujui": fields.Datetime.now(),
                }
            )

    def action_set_draft(self):
        for rec in self:
            rec.write({"state": "draft"})

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

    def action_open_import_template_wizard(self):
        self.ensure_one()
        if not self.id:
            raise UserError(_("Silakan simpan dokumen terlebih dahulu."))
        if self.state == "approved":
            raise UserError(_("Dokumen RAP/PFC sudah Approved, tidak bisa diubah."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Add from Template"),
            "res_model": "project.rap.import.template",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_rap_id": self.id,
            },
        }

    def action_open_save_as_template_wizard(self):
        self.ensure_one()
        if not self.id:
            raise UserError(_("Silakan simpan dokumen terlebih dahulu."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Save as Template"),
            "res_model": "project.rap.save.as.template",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_source_rap_id": self.id,
            },
        }

    # === lock editing ===
    def _ensure_editable(self):
        for rec in self:
            if rec.state == "approved":
                raise UserError(_("Dokumen RAP/PFC sudah Approved, tidak bisa diubah."))

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.project_id.rap_id = res
        return res

    def write(self, vals):
        # tetap izinkan perubahan metadata approval/state via action
        editable_keys = {"state", "user_request_id", "user_approve_id", "tanggal_disetujui"}
        if any(k not in editable_keys for k in vals.keys()):
            self._ensure_editable()
        return super().write(vals)

    def unlink(self):
        self._ensure_editable()
        return super().unlink()
