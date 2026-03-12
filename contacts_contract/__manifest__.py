# -*- coding: utf-8 -*-
{
    'name': "Contacts Contracts",
    'summary': """
       Can manage contract for contact """,
    'author': "José Luis Hernández Ricardo",
    'website': "https://github.com/theceojose/",
    'category': 'Productivity',
    'version': '16.0',
    'depends': ['contacts'],
    'data': [
        'security/contract_security.xml',
        'security/ir.model.access.csv',
        'data/contract_type_data.xml',
        'data/contract_category_data.xml',
        'data/contract_part_data.xml',
        'data/cron_data.xml',
        'data/mail_activity_type_data.xml',
        'views/menu_view.xml',
        'views/contract_views.xml',
        'views/res_partner_view.xml',
        'views/contract_tree_views.xml',
    ],
    'license': 'LGPL-3',
}
