from odoo import models, fields


class ResKantor(models.Model):
    _name = 'res.kantor'
    _description = 'Kantor'

    name = fields.Char(string='Nama Kantor', required=True)
    code = fields.Char(string='Kode Kantor')
    company_id = fields.Many2one('res.company', string='Perusahaan')
    active = fields.Boolean(default=True)

    def _compute_display_name(self):
        for rec in self:
            if rec.code and rec.name:
                rec.display_name = f"{rec.code} - {rec.name}"
            elif rec.code:
                rec.display_name = rec.code
            else:
                rec.display_name = rec.name or ''
