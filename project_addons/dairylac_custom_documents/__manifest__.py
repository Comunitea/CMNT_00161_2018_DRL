# © 2020 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Custom documents Dairylac",
    "version": "12.0.1.0.0",
    "category": "Uncategorized",
    "license": "AGPL-3",
    "author": "Comunitea,",
    "website": "https://www.comunitea.com",
    "depends": [
        "base",
        "web",
        "sale",
        "sale_stock",
        "stock",
        "delivery",
        "quality_control_stock",
        "quality_control"
    ],
    "data": [
        "views/res_partner_view.xml",
        "views/report_dac.xml",
        "views/report_templates.xml",
        "views/port_letter.xml",
        "views/stock_view.xml",
        "views/report_analityc_certificate.xml",
    ],
    "installable": True,
}
