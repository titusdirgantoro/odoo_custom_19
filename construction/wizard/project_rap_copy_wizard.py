# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class ProjectRapCopyWizard(models.TransientModel):
    _name = "project.rap.copy.wizard"
    _description = "Copy RAP/PFC to Another Project"

    source_rap_id = fields.Many2one("project.rap", required=True, readonly=True)
    target_project_id = fields.Many2one("project.project", required=True)
    target_type = fields.Selection([("rap", "RAP"), ("pfc", "PFC")], default="rap", required=True)
    new_name = fields.Char(string="New Document Name")

    def action_copy(self):
        self.ensure_one()
        source = self.source_rap_id

        if self.target_project_id == source.project_id:
            raise UserError(_("Target project harus berbeda dari project sumber."))

        defaults = {
            "project_id": self.target_project_id.id,
            "type": self.target_type,
            "state": "draft",
        }
        if self.new_name:
            defaults["name"] = self.new_name

        # Deep copy: Odoo akan otomatis copy O2M yang copy=True (pekerjaan->sub->lines)
        new_doc = source.copy(default=defaults)

        return {
            "type": "ir.actions.act_window",
            "res_model": "project.rap",
            "view_mode": "form",
            "res_id": new_doc.id,
            "target": "current",
        }
