from odoo import models, fields

class ConstructionMaterialGroup(models.Model):
    _name = 'construction.material.group'
    _description = 'Kelompok Bahan Konstruksi'

    name = fields.Char(string='Nama Kelompok', required=True)
    code = fields.Char(string='Kode')
    active = fields.Boolean(default=True)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.code} - {rec.name}" if rec.code else rec.name
