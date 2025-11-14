{
    'name': 'Construction',
    'version': '19.0.1.0.0',
    'summary': 'Menu Construction yang mengelompokkan Project, Gudang, Product, Employee dan Pemasok',
    'description': """
Construction
=============
Module tambahan untuk mengelompokkan menu Project, Stock, Product, Employee, dan Pemasok
khusus untuk kebutuhan konstruksi.

Fitur:
- Menu utama Construction
- Menu Project (project.task)
- Menu Configuration (Warehouse & Location)
- Menu Product dengan filter Type Master Data (Bahan, Upah, Overhead, Jasa, Sewa Alat)
- Menu Employee
- Menu Pemasok (Vendor) dari res.partner
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
        'purchase',   # supaya field supplier_rank di res.partner tersedia
    ],
    'data': [
        'views/construction_menus.xml',
    ],
    'installable': True,
    'application': True,
}
