from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    en_name = fields.Char('Nama Inggris')
    type_master_data = fields.Selection(
        [
            ('bahan', 'Bahan'),
            ('upah', 'Upah'),
            ('overhead', 'Overhead'),
            ('jasa', 'Jasa'),
            ('sewa_alat', 'Sewa Alat'),
        ],
        string='Type Master Data',
        help='Menandai jenis master data produk untuk kebutuhan Construction.'
    )

    parent_product_id = fields.Many2one(
        'product.template',
        string='Parent Product',
        index=True
    )
    child_product_ids = fields.One2many(
        'product.template',
        'parent_product_id',
        string='Child Products'
    )
    product_level = fields.Integer(
        string='Product Level',
        compute='_compute_product_level',
        store=True, recursive=True
    )
    tanggal_harga = fields.Date('Tanggal Harga')
    city_id = fields.Many2one(comodel_name='res.city', string='City ID')

    # =========================================================
    # FIELD UMUM MODUL PRODUCT (BERLAKU UNTUK SEMUA TYPE)
    # =========================================================
    construction_usage = fields.Selection(
        [
            ('umum', 'Umum'),
            ('spesifik_proyek', 'Spesifik Proyek'),
        ],
        string='Penggunaan Construction',
        help='Menandai apakah product dipakai umum atau spesifik proyek.'
    )
    rap_coefficient = fields.Float(
        string='Koefisien RAP',
        help='Koefisien pemakaian dalam RAP per satuan output.'
    )
    rap_uom_id = fields.Many2one(
        'uom.uom',
        string='Satuan RAP',
        help='Satuan yang digunakan pada koefisien RAP.'
    )

    # =========================================================
    # FIELD KHUSUS TYPE: BAHAN
    # =========================================================
    bahan_group_id = fields.Many2one(
        'construction.material.group',
        string='Kelompok Bahan',
        help='Klasifikasi kelompok bahan konstruksi.'
    )
    bahan_spec = fields.Char(
        string='Spesifikasi Bahan',
        help='Spesifikasi teknis singkat bahan.'
    )
    bahan_brand = fields.Char(
        string='Merek Bahan',
        help='Merek/brand bahan jika relevan.'
    )
    weight_uom_id = fields.Many2one('uom.uom', string='Weight UoM')
    usage_category_ids = fields.Many2many(
        'construction.usage.category',
        string='Kategori Penggunaan'
    )
    product_account_id = fields.Many2one('account.account', string='Account (CoA)')
    kantor_account_id = fields.Many2one('account.account', string='Kode Perkiraan Kantor (CoA)')
    workshop_account_id = fields.Many2one('account.account', string='Kode Perkiraan Workshop (CoA)')
    proyek_account_id = fields.Many2one('account.account', string='Kode Perkiraan Proyek (CoA)')
    
    # =========================================================
    # FIELD KHUSUS TYPE: UPAH
    # =========================================================
    is_status_upah_alat = fields.Boolean('Status Upah Alat')
    skill_level_id = fields.Many2one(
        'construction.skill.level',
        string='Level Keahlian'
    )

    # =========================================================
    # FIELD KHUSUS TYPE: OVERHEAD
    # =========================================================
    overhead_type_id = fields.Many2one(
        'construction.overhead.type',
        string='Tipe Overhead'
    )
    overhead_description = fields.Char(
        string='Keterangan Overhead'
    )

    # =========================================================
    # FIELD KHUSUS TYPE: JASA
    # =========================================================
    service_category_id = fields.Many2one(
        'construction.service.category',
        string='Kategori Jasa'
    )
    service_scope = fields.Text(
        string='Ruang Lingkup Jasa'
    )

    # =========================================================
    # FIELD KHUSUS TYPE: SEWA ALAT
    # =========================================================
    equipment_category_id = fields.Many2one(
        'construction.equipment.category',
        string='Kategori Alat'
    )
    rental_unit = fields.Selection(
        [
            ('jam', 'Per Jam'),
            ('hari', 'Per Hari'),
            ('minggu', 'Per Minggu'),
            ('bulan', 'Per Bulan'),
        ],
        string='Satuan Sewa'
    )
    min_rental_duration = fields.Float(
        string='Durasi Minimum Sewa',
        help='Durasi minimum sewa dalam satuan yang dipilih.'
    )

    @api.depends('parent_product_id', 'parent_product_id.product_level')
    def _compute_product_level(self):
        for rec in self:
            if rec.parent_product_id:
                rec.product_level = rec.parent_product_id.product_level + 1
            else:
                rec.product_level = 1

    @api.constrains('parent_product_id')
    def _check_parent_product_id(self):
        """Cegah loop / siklus parent-child (A anaknya B, B anaknya A, dst)."""
        if not self._check_recursion(parent='parent_product_id'):
            raise ValidationError(_('You cannot create recursive product hierarchies.'))
        
class ProductProduct(models.Model):
    _inherit = 'product.product'

    type_master_data = fields.Selection(
        string='Type Master Data',
        help='Menandai jenis master data produk untuk kebutuhan Construction.',
        related='product_tmpl_id.type_master_data'
    )
