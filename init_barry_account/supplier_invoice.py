from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

class supplier_invoice(osv.osv):
    _inherit = 'account.invoice'
    
    _columns = {
                'is_create_invoice': fields.boolean("Create Supplier Invoice")
                }
    
    def create_supplier_invoice(self,cr, uid, ids, context=None):
        acc_invoice = self.pool.get('account.invoice')
        acc_invoice_line = self.pool.get('account.invoice.line')
        
        invoice_id = 0
        for obj in self.browse( cr, uid, ids, context):
            company_id = self.pool['res.company'].search(cr, uid, [('partner_id', '=', obj.partner_id.id)], context=context)
            journal_id = self._get_journal(cr, uid, {'company_id': company_id[0],
                                                     'type' : 'in_invoice'})
            data_inv = {
                          'type': 'in_invoice',
                          'state': 'draft',
                          'reference_type': 'none',
                          'supplier_invoice_number': obj.name,
                          'partner_id': obj.company_id.partner_id.id,
                          'company_id': company_id[0],
                          'fiscal_position': obj.fiscal_position.id,
                          'payment_term': obj.payment_term.id,
                          'account_id': False,
                          'currency_id': obj.currency_id.id,
                          'journal_id': journal_id,
                          'user_id': obj.user_id.id,
                          }
            
            account_ids = self.pool.get('account.account').search(cr, uid, [('company_id','=', company_id[0]),('type', '=', 'payable')])
            if account_ids:
                data_inv['account_id'] = account_ids[0]
            else:
                raise osv.except_osv('No Payable Account !',"You must define payable account for company!")
                    
            if not company_id: continue
            invoice_id = acc_invoice.create(cr, uid, data_inv)
            for invoice_line in obj.invoice_line:
                account = self.pool.get('account.invoice.line')._default_account_id(cr, uid, {'force_company': company_id[0]})
                
                dict_line =  {
                              'name': invoice_line.name,
                              'origin': invoice_line.origin,
                              'invoice_id': invoice_id,
                              'uos_id': invoice_line.uos_id and invoice_line.uos_id.id or False,
                              'product_id': invoice_line.product_id and invoice_line.product_id.id or False,
                              'account_id': account,
                              'price_unit': invoice_line.price_unit,
                              'quantity': invoice_line.quantity,
                              'discount': invoice_line.discount,
                              'company_id': company_id[0],
                              'partner_id': invoice_line.company_id.partner_id.id,
                              }
                if invoice_line.product_id:
                    value_onchange = self.pool.get('account.invoice.line').product_id_change(cr, uid, ids, invoice_line.product_id.id, invoice_line.uos_id.id, invoice_line.quantity, '', 'in_invoice',obj.company_id.partner_id.id, False, False, False, None, company_id[0])
                    dict_line.update(value_onchange['value'])
                
                if not dict_line['account_id'] or \
                    self.pool.get('account.account').browse(cr, uid, dict_line['account_id']).company_id.id not in company_id:
                    company_obj = self.pool['res.company'].browse(cr, uid, company_id[0])
                    if company_obj.property_account_expense_partner:
                        dict_line['account_id'] = company_obj.property_account_expense_partner.id
                if not dict_line['account_id']:
                    account_type_ids = self.pool.get('account.account.type').search(cr, uid, [('report_type','=','income')])
                    account_ids = self.pool.get('account.account').search(cr, uid, [('company_id','=', company_id[0]),('user_type','in', account_type_ids),('type', '!=', 'view')])
                    if account_ids:
                        dict_line['account_id'] = account_ids[0]
                    else:
                        raise osv.except_osv('No Income Account !',"You must define income account for company!")
                acc_invoice_line.create(cr, uid, dict_line)
        return {
            'name':_("Supplier Invoice"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'account.invoice',
            'views':False,
            'res_id': invoice_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {},
        }        
    def invoice_validate(self, cr, uid, ids,context=None):
        
        for obj in self.browse( cr, uid, ids, context):
            if obj.is_create_invoice:
                self.create_supplier_invoice(cr, uid, ids, context=context)
                
        return super(supplier_invoice, self).invoice_validate(cr, uid, ids,context)
              