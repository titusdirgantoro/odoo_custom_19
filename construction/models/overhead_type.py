from odoo import models, fields

class ConstructionOverheadType(models.Model):
    _name = 'construction.overhead.type'
    _description = 'Tipe Biaya Overhead'

    name = fields.Char(string='Nama Tipe', required=True)
    code = fields.Char(string='Kode')
    active = fields.Boolean(default=True)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.code} - {rec.name}" if rec.code else rec.name
