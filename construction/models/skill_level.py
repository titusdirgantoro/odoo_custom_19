from odoo import models, fields

class ConstructionSkillLevel(models.Model):
    _name = 'construction.skill.level'
    _description = 'Level Keahlian Tenaga Kerja'

    name = fields.Char(string='Nama Level', required=True)
    code = fields.Char(string='Kode')
    active = fields.Boolean(default=True)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.code} - {rec.name}" if rec.code else rec.name
