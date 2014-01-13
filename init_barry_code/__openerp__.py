# -*- encoding: utf-8 -*-
##############################################################################
#
#    Init Tech, Open Source Management Solution
#    Copyright (C) 2012 Init Tech (<http://init.vn>). All Rights Reserved
#
##############################################################################

{
        "name" : "INIT Property Management",
        "version" : "1.0",
        "author" : "Init Tech",
        "website" : "http://www.init.vn",
        "category" : "INIT Modules",
        "description" : """Property Management Barry""",
        "depends" : ["base","account"],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "update_xml" : [
                        "init_data.xml",
                        "init_view.xml",
                        "wizard/init_import_payment_view.xml",
                        "init_partner_view.xml",
			            "init_sheduler.xml",
                        "wizard/init_bulk_charge_invoice_view.xml",
                        "wizard/init_update_task_sequence_view.xml",
                        "init_project_task_view.xml",
                         ],
        'installable': True,
        'auto_install': False,
        'application': True,
}
