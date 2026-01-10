{
    'name': 'Construction',
    'version': '19.0.1.0.0',
    'summary': 'Menu Construction yang mengelompokkan Project, Gudang, Product, Employee dan Pemasok',
    'description': """
Construction
=============
Module tambahan untuk mengelompokkan menu Project, Stock, Product, Employee, dan Pemasok
khusus untuk kebutuhan konstruksi.

    """,
    'category': 'Construction',
    'author': 'Your Company',
    'website': 'https://yourcompany.example.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'project',
        'stock',
        'product',
        'hr',
        'purchase', 
        'mail',
        'web',
        'base_address_extended',
        'l10n_id_efaktur_coretax'
    ],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/res_kantor_views.xml',
        'views/kelompok_proyek_views.xml',
        'views/res_bidang_views.xml',
        'views/hr_employee_views.xml',
        'views/res_sub_bidang_views.xml',
        'views/status_proyek_views.xml',
        'views/project_project_views.xml',
        'views/res_partner_views.xml',
        'views/supplier_category_views.xml',
        'views/supplier_service_views.xml',
        'views/material_group_views.xml',
        'views/skill_level_views.xml',
        'views/overhead_type_views.xml',
        'views/service_category_views.xml',
        'views/equipment_category_views.xml',
        'views/usage_category_views.xml',
        'views/product_views.xml',
        'views/rap_template_views.xml',
        'views/project_rap_views.xml',
        'views/project_pekerjaan_views.xml',
        'views/project_sub_pekerjaan_views.xml',
        'views/purchase_order_views.xml',

        'wizard/project_rap_create_po_wizard_views.xml',
        'wizard/project_rap_copy_wizard_views.xml',
        'wizard/project_rap_import_template_wizard_views.xml',
        'wizard/project_rap_save_as_template_wizard_views.xml',
        
        'views/construction_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'construction/static/src/scss/font_scale.scss',
            'construction/static/src/views/form/form_status_indicator.xml',
            'construction/static/src/js/chatter_restrict_group_system.js',
            'construction/static/src/xml/chatter_restrict_group_system.xml',
        ],
        'web._assets_primary_variables': [
            'construction/static/src/scss/form_variables_override.scss',
        ],
    },
    'installable': True,
    'application': True,
}
