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
        'views/construction_menus.xml',
    ],
    'installable': True,
    'application': True,
}
