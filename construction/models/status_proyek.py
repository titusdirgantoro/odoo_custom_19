from odoo import models, fields


class StatusProyek(models.Model):
    _name = 'status.proyek'
    _description = 'Status Proyek'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    code = fields.Char()
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    def _compute_display_name(self):
        self.display_name = f"{self.code} - {self.name}" if self.code else self.name
