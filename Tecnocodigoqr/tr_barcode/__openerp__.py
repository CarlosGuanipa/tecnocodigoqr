# -*- coding: utf-8 -*-
#/#############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2004-TODAY Tech-Receptives(<http://www.tech-receptives.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#/#############################################################################

{
    'name': 'TR Barcode',
    'version': '1.1.4',
    'category': 'Warehouse Management',
    'description': """

Presentation:

This module adds the menu Barcode used to generate and configuration barcodes.

    """,
    'author': 'Tech-Receptives Solutions Pvt. Ltd.',
    'website': 'http://www.techreceptives.com',
    'depends': [
        "base",
        "base_setup", 
        'stock',
    ],
    'data': [
        "wizard/tr_barcode_wizard.xml",
        "res_config_view.xml",
        "tr_barcode_view.xml",
        "security/ir.model.access.csv",
        "custom_views/res_users_view.xml",
        "reports/carnet_qr.xml",
        "custom_views/carnet_user.xml",
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
