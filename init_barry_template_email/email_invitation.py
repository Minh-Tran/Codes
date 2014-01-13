from datetime import datetime, timedelta
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.osv import osv

def now(**kwargs):
    dt = datetime.now() + timedelta(**kwargs)
    return dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

class template_invitation(osv.osv):
    _inherit = 'res.users'
    
    def action_reset_password(self, cr, uid, ids, context=None):
        """ create signup token for each user, and send their signup url by email """
        # prepare reset password signup
        res_partner = self.pool.get('res.partner')
        template_obj = self.pool.get('email.template')
        partner_ids = [user.partner_id.id for user in self.browse(cr, uid, ids, context)]
        res_partner.signup_prepare(cr, uid, partner_ids, signup_type="reset", expiration=now(days=+1), context=context)

        if not context:
            context = {}

        # send email to users with their signup url
        body_html = """
             <p>Dear ${object.name}, </p> 
             <p>Welcome to your new ownership account with Probity Management. It's designed to give you quick and easy access to important information about your account. Please log in to your ownership account to do things like pay your fees, see your payment history, and make service requests. Have a look around and let us know if you have any questions.</p>
             <p>Your username is: ${object.login}</p>
             <p>Please sign in to your account using the link below. You'll be prompted to change your password to one that you can easily remember.</p>
             <p><a href="${object.signup_url}">This link</a>.</p>
            <p>Thanks from ${object.company_id.name or ''}.</p> 
        """
        
        template = False
        if context.get('create_user'):
            try:
                template = self.pool.get('ir.model.data').get_object(cr, uid, 'auth_signup', 'set_password_email')
                template_obj.write(cr, uid, template.id,{'body_html':body_html,}, context = context )
            except ValueError:
                pass
            
        body_html = """
             <p>A password reset was requested for the Probity Management account linked to this email.</p> 
             <p>You may change your password by following <a href="${object.signup_url}">this link</a>.</p> 
             <p>Note: If you do not expect this, you can safely ignore this email.</p>
        """
        
        if not bool(template):
            template = self.pool.get('ir.model.data').get_object(cr, uid, 'auth_signup', 'reset_password_email')
            template_obj.write(cr, uid, template.id,{'body_html':body_html,}, context = context )
        mail_obj = self.pool.get('mail.mail')
        assert template._name == 'email.template'
        for user in self.browse(cr, uid, ids, context):
            if not user.email:
                raise osv.except_osv(_("Cannot send email: user has no email address."), user.name)
            mail_id = self.pool.get('email.template').send_mail(cr, uid, template.id, user.id, True, context=context)
            mail_state = mail_obj.read(cr, uid, mail_id, ['state'], context=context)
            if mail_state and mail_state['state'] == 'exception':
                raise osv.except_osv(_("Cannot send email: no outgoing email server configured.\nYou can configure it under Settings/General Settings."), user.name)
            else:
                return True
        