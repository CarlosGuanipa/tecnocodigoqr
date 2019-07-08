from openerp.report import report_sxw
from openerp.osv import osv

class reports_qr_user(report_sxw.rml_parse):
    def _init_(self,cr,uid,name,context):
        super(reports_qr_user,self)._init_(cr,uid,name,context)

class qr_user(osv.AbstractModel):
    _name="reports.tr_barcode.carnet"
    _inherit="reports.abstract_report"
    _template="reports.carnet"
    _wrapped_report_class=reports_qr_user
    
