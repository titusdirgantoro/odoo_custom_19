from odoo import models, fields


class KelompokProyek(models.Model):
    _name = 'kelompok.proyek'
    _description = 'Kelompok Proyek'

    name = fields.Char(required=True)
    code = fields.Char()
    active = fields.Boolean(default=True)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.code} - {rec.name}" if rec.code else rec.name
