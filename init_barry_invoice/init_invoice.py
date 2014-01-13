
from osv import fields, osv

class account_invoice(osv.osv):     
    
    _inherit = "account.invoice"
    
    _columns = {
        'journal_id': fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}, \
                                      domain="[('company_id','=', company_id)]"),
        }
    
    def invoice_print(self, cr, uid, ids, context=None):
        '''
        This function prints the invoice and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        self.write(cr, uid, ids, {'sent': True}, context=context)
        datas = {
             'ids': ids,
             'model': 'account.invoice',
             'form': self.read(cr, uid, ids[0], context=context)
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'invoice_ods',
            'datas': datas,
            'nodestroy' : True
        }

account_invoice()
