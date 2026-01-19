from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)
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
    construction_price = fields.Monetary(
        string='Harga',
        currency_field='currency_id',
        default=0.0,
        help='Harga acuan PT untuk kebutuhan master data (bukan harga jual).'
    )
    construction_product_type = fields.Selection(
        [('consu', 'Barang'), ('service', 'Layanan')],
        string='Tipe Produk',
        default='consu',
        required=True
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

    @api.depends('name', 'default_code')
    @api.depends_context('formatted_display_name')
    def _compute_display_name(self):
        for template in self:
            if not template.name:
                template.display_name = False
            elif self.env.context.get('formatted_display_name'):
                code_prefix = f'[{template.default_code}] ' if template.default_code else ''
                level_sufix = f' - Level {template.product_level} ' if template.product_level else ''
                template.display_name = f'{code_prefix}{template.name}{level_sufix}'
            else:
                code_prefix = f'[{template.default_code}] ' if template.default_code else ''
                level_sufix = f' - Level {template.product_level} ' if template.product_level else ''
                template.display_name = f'{code_prefix}{template.name}{level_sufix}'
            
    @api.onchange('construction_product_type')
    def _onchange_construction_product_type(self):
        """Sinkronkan ke field standar Odoo (detailed_type atau type)."""
        for rec in self:
            if 'detailed_type' in rec._fields:
                rec.detailed_type = rec.construction_product_type
            elif 'type' in rec._fields:
                rec.type = rec.construction_product_type
                
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
    
    @api.model_create_multi
    def create(self, vals_list):
        """Pastikan saat create dari menu master, type standar ikut terset."""
        for vals in vals_list:
            ctype = vals.get('construction_product_type')
            if ctype:
                if 'detailed_type' in self._fields and not vals.get('detailed_type'):
                    vals['detailed_type'] = ctype
                if 'type' in self._fields and not vals.get('type'):
                    vals['type'] = ctype
        return super().create(vals_list)
    
    def write(self, vals):
        """Jika construction_product_type diubah, sync ke field standar."""
        if 'construction_product_type' in vals:
            ctype = vals.get('construction_product_type')
            if ctype:
                if 'detailed_type' in self._fields and 'detailed_type' not in vals:
                    vals['detailed_type'] = ctype
                if 'type' in self._fields and 'type' not in vals:
                    vals['type'] = ctype
        return super().write(vals)
    
class ProductProduct(models.Model):
    _inherit = 'product.product'

    # ===== Mirror dari template (store=True semuanya) =====
    en_name = fields.Char(related='product_tmpl_id.en_name', store=False, readonly=True)
    type_master_data = fields.Selection(
        related='product_tmpl_id.type_master_data',
        store=False,
        readonly=True,
        string='Type Master Data',
        help='Menandai jenis master data produk untuk kebutuhan Construction.',
    )

    parent_product_id = fields.Many2one(
        'product.template',
        related='product_tmpl_id.parent_product_id',
        store=False,
        readonly=True,
        string='Parent Product',
    )
    product_level = fields.Integer(
        related='product_tmpl_id.product_level',
        store=False,
        readonly=True,
        string='Product Level',
    )

    tanggal_harga = fields.Date(related='product_tmpl_id.tanggal_harga', store=False, readonly=True)
    city_id = fields.Many2one('res.city', related='product_tmpl_id.city_id', store=False, readonly=True)

    construction_usage = fields.Selection(related='product_tmpl_id.construction_usage', store=False, readonly=True)
    rap_coefficient = fields.Float(related='product_tmpl_id.rap_coefficient', store=False, readonly=True)
    rap_uom_id = fields.Many2one('uom.uom', related='product_tmpl_id.rap_uom_id', store=False, readonly=True)

    construction_price = fields.Monetary(
        related='product_tmpl_id.construction_price',
        store=False,
        readonly=True,
        currency_field='currency_id',
        string='Harga',
    )
    construction_product_type = fields.Selection(
        related='product_tmpl_id.construction_product_type',
        store=False,
        readonly=True,
        string='Tipe Produk',
    )

    # ===== Bahan =====
    bahan_group_id = fields.Many2one('construction.material.group', related='product_tmpl_id.bahan_group_id', store=False, readonly=True)
    bahan_spec = fields.Char(related='product_tmpl_id.bahan_spec', store=False, readonly=True)
    bahan_brand = fields.Char(related='product_tmpl_id.bahan_brand', store=False, readonly=True)
    weight_uom_id = fields.Many2one('uom.uom', related='product_tmpl_id.weight_uom_id', store=False, readonly=True)
    usage_category_ids = fields.Many2many(
        'construction.usage.category',
        'product_product_usage_category_rel',   # nama table relasi (HARUS ada)
        'product_id',                           # kolom FK ke product_product
        'category_id',                          # kolom FK ke usage category
        string='Kategori Penggunaan',
        compute='_compute_usage_category_ids',
        inverse='_inverse_usage_category_ids',
        store=False,
    )


    product_account_id = fields.Many2one('account.account', related='product_tmpl_id.product_account_id', store=False, readonly=True)
    kantor_account_id = fields.Many2one('account.account', related='product_tmpl_id.kantor_account_id', store=False, readonly=True)
    workshop_account_id = fields.Many2one('account.account', related='product_tmpl_id.workshop_account_id', store=False, readonly=True)
    proyek_account_id = fields.Many2one('account.account', related='product_tmpl_id.proyek_account_id', store=False, readonly=True)

    # ===== Upah =====
    is_status_upah_alat = fields.Boolean(related='product_tmpl_id.is_status_upah_alat', store=False, readonly=True)
    skill_level_id = fields.Many2one('construction.skill.level', related='product_tmpl_id.skill_level_id', store=False, readonly=True)

    # ===== Overhead =====
    overhead_type_id = fields.Many2one('construction.overhead.type', related='product_tmpl_id.overhead_type_id', store=False, readonly=True)
    overhead_description = fields.Char(related='product_tmpl_id.overhead_description', store=False, readonly=True)

    # ===== Jasa =====
    service_category_id = fields.Many2one('construction.service.category', related='product_tmpl_id.service_category_id', store=False, readonly=True)
    service_scope = fields.Text(related='product_tmpl_id.service_scope', store=False, readonly=True)

    # ===== Sewa Alat =====
    equipment_category_id = fields.Many2one('construction.equipment.category', related='product_tmpl_id.equipment_category_id', store=False, readonly=True)
    rental_unit = fields.Selection(related='product_tmpl_id.rental_unit', store=False, readonly=True)
    min_rental_duration = fields.Float(related='product_tmpl_id.min_rental_duration', store=False, readonly=True)

    @api.depends('product_tmpl_id.usage_category_ids')
    def _compute_usage_category_ids(self):
        for rec in self:
            rec.usage_category_ids = rec.product_tmpl_id.usage_category_ids

    def _inverse_usage_category_ids(self):
        # karena kamu desain 1 template = 1 variant, inverse ini aman
        for rec in self:
            rec.product_tmpl_id.usage_category_ids = rec.usage_category_ids

    def action_open_product_template(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Product Template"),
            "res_model": "product.template",
            "view_mode": "form",
            "res_id": self.product_tmpl_id.id,
            "target": "current",
            "context": dict(self.env.context, create=False),
        }
