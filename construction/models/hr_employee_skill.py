from odoo import fields, models

class HrEmployeeSkill(models.Model):
    _inherit = 'hr.employee.skill'

    attachment_id = fields.Binary('Upload Dokumen')