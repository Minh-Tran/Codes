from openerp.osv import fields, osv
from openerp.osv.osv import object_proxy
from openerp.tools.translate import _
from openerp import pooler
import time
from openerp import tools
from openerp import SUPERUSER_ID

class audittrail_rule(osv.osv):
    _inherit = 'audittrail.rule'
    _columns = {
                'check_all_model': fields.boolean("Check all model"),
                }
    
    def subscribe_inherit(self, cr, uid, ids, *args):
        
        obj_action = self.pool.get('ir.actions.act_window')
        obj_model = self.pool.get('ir.model.data')
        obj_model_ids = self.pool.get('ir.model')
        model_ids = self.pool.get('ir.model').search(cr, uid, [('model','!=', 'ir.filters')])
        
        for thisrule in self.browse(cr, uid, ids):
            if thisrule.check_all_model:
               # for id in model_ids:
                    for model_id in obj_model_ids.browse(cr, uid, model_ids):
                        obj = self.pool.get(model_id.model)
                        if not obj:
                            raise osv.except_osv(
                            _('WARNING: audittrail is not part of the pool'),
                            _('Change audittrail depends -- Setting rule as DRAFT'))
                        self.write(cr, uid, [thisrule.id], {"state": "draft"})
                        val = {
                               "name": 'View Log',
                               "res_model": 'audittrail.log',
                               "src_model": model_id.model,
                               #"domain": "[('object_id','=', " + str(model_id.id) + "), ('res_id', '=', active_id)]"
    
                        }
                        action_id = obj_action.create(cr, SUPERUSER_ID, val)
                        self.write(cr, uid, [thisrule.id], {"state": "subscribed", "action_id": action_id})
                        keyword = 'client_action_relate'
                        value = 'ir.actions.act_window,' + str(action_id)
                        res = obj_model.ir_set(cr, SUPERUSER_ID, 'action', keyword, 'View_log_' + model_id.model, [model_id.model], value, replace=True, isobject=True, xml_id=False)
            else:
                obj = self.pool.get(thisrule.object_id.model)
                if not obj:
                    raise osv.except_osv(
                            _('WARNING: audittrail is not part of the pool'),
                            _('Change audittrail depends -- Setting rule as DRAFT'))
                    self.write(cr, uid, [thisrule.id], {"state": "draft"})
                val = {
                     "name": 'View Log',
                     "res_model": 'audittrail.log',
                     "src_model": thisrule.object_id.model,
                     #"domain": "[('object_id','=', " + str(thisrule.object_id.id) + "), ('res_id', '=', active_id)]"
    
                }
                action_id = obj_action.create(cr, SUPERUSER_ID, val)
                self.write(cr, uid, [thisrule.id], {"state": "subscribed", "action_id": action_id})
                keyword = 'client_action_relate'
                value = 'ir.actions.act_window,' + str(action_id)
                res = obj_model.ir_set(cr, SUPERUSER_ID, 'action', keyword, 'View_log_' + thisrule.object_id.model, [thisrule.object_id.model], value, replace=True, isobject=True, xml_id=False)
        return True
    
    def unsubscribe_inherit(self, cr, uid, ids, *args):       

        obj_action = self.pool.get('ir.actions.act_window')
        ir_values_obj = self.pool.get('ir.values')
        value=''  
        obj_model_ids = self.pool.get('ir.model')
        model_ids = self.pool.get('ir.model').search(cr, uid, [('model','!=', 'ir.filters')])
        
        for thisrule in self.browse(cr, uid, ids):
            if thisrule.check_all_model:
                if thisrule.id in self.__functions:
                    for function in self.__functions[thisrule.id]:
                        setattr(function[0], function[1], function[2])
                w_id = obj_action.search(cr, uid, [('name', '=', 'View Log'), ('res_model', '=', 'audittrail.log'), ('src_model', '=', thisrule.object_id.model)])
                if w_id:
                    obj_action.unlink(cr, SUPERUSER_ID, w_id)
                    value = "ir.actions.act_window" + ',' + str(w_id[0])
                for model_id in obj_model_ids.browse(cr, uid, model_ids):
                    val_id = ir_values_obj.search(cr, uid, [('model', '=', model_id.model), ('value', '=', value)])
                    if val_id:
                        ir_values_obj = pooler.get_pool(cr.dbname).get('ir.values')
                        res = ir_values_obj.unlink(cr, uid, [val_id[0]])
                        self.write(cr, uid, [thisrule.id], {"state": "draft"})
            else:
                if thisrule.id in self.__functions:
                    for function in self.__functions[thisrule.id]:
                        setattr(function[0], function[1], function[2])
                w_id = obj_action.search(cr, uid, [('name', '=', 'View Log'), ('res_model', '=', 'audittrail.log'), ('src_model', '=', thisrule.object_id.model)])
                if w_id:
                    obj_action.unlink(cr, SUPERUSER_ID, w_id)
                    value = "ir.actions.act_window" + ',' + str(w_id[0])
                val_id = ir_values_obj.search(cr, uid, [('model', '=', thisrule.object_id.model), ('value', '=', value)])
                if val_id:
                    ir_values_obj = pooler.get_pool(cr.dbname).get('ir.values')
                    res = ir_values_obj.unlink(cr, uid, [val_id[0]])
                self.write(cr, uid, [thisrule.id], {"state": "draft"})
        return True

class audittrail_objects_proxy_inherit(object_proxy):
    
    def get_value_text(self, cr, uid, pool, resource_pool, method, field, value):
        field_obj = (resource_pool._all_columns.get(field)).column
        if field_obj._type in ('one2many','many2many'):
            data = pool.get(field_obj._obj).name_get(cr, uid, value)
            #return the modifications on x2many fields as a list of names
            res = map(lambda x:x[1], data)
        elif field_obj._type == 'many2one':
            #return the modifications on a many2one field as its value returned by name_get()
            res = value and value[1] or value
        else:
            res = value
        return res

    def create_log_line(self, cr, uid, log_id, model, lines=None):
        if lines is None:
            lines = []
        pool = pooler.get_pool(cr.dbname)
        obj_pool = pool.get(model.model)
        model_pool = pool.get('ir.model')
        field_pool = pool.get('ir.model.fields')
        log_line_pool = pool.get('audittrail.log.line')
        for line in lines:
            field_obj = obj_pool._all_columns.get(line['name'])
            assert field_obj, _("'%s' field does not exist in '%s' model" %(line['name'], model.model))
            field_obj = field_obj.column
            old_value = line.get('old_value', '')
            new_value = line.get('new_value', '')
            search_models = [model.id]
            if obj_pool._inherits:
                search_models += model_pool.search(cr, uid, [('model', 'in', obj_pool._inherits.keys())])
            field_id = field_pool.search(cr, uid, [('name', '=', line['name']), ('model_id', 'in', search_models)])
            if field_obj._type == 'many2one':
                old_value = old_value and old_value[0] or old_value
                new_value = new_value and new_value[0] or new_value
            vals = {
                    "log_id": log_id,
                    "field_id": field_id and field_id[0] or False,
                    "old_value": old_value,
                    "new_value": new_value,
                    "old_value_text": line.get('old_value_text', ''),
                    "new_value_text": line.get('new_value_text', ''),
                    "field_description": field_obj.string
                    }
            line_id = log_line_pool.create(cr, uid, vals)
        return True

    def log_fct(self, cr, uid_orig, model, method, fct_src, *args, **kw):
        pool = pooler.get_pool(cr.dbname)
        resource_pool = pool.get(model)
        model_pool = pool.get('ir.model')
        model_ids = model_pool.search(cr, SUPERUSER_ID, [('model', '=', model)])
        model_id = model_ids and model_ids[0] or False
        assert model_id, _("'%s' Model does not exist..." %(model))
        model = model_pool.browse(cr, SUPERUSER_ID, model_id)

        # fields to log. currently only used by log on read()
        field_list = []
        old_values = new_values = {}

        if method == 'create':
            res = fct_src(cr, uid_orig, model.model, method, *args, **kw)
            if res:
                res_ids = [res]
                new_values = self.get_data(cr, uid_orig, pool, res_ids, model, method)
        elif method == 'read':
            res = fct_src(cr, uid_orig, model.model, method, *args, **kw)
            # build the res_ids and the old_values dict. Here we don't use get_data() to
            # avoid performing an additional read()
            res_ids = []
            for record in res:
                res_ids.append(record['id'])
                old_values[(model.id, record['id'])] = {'value': record, 'text': record}
            # log only the fields read
            field_list = args[1]
        elif method == 'unlink':
            res_ids = args[0]
            old_values = self.get_data(cr, uid_orig, pool, res_ids, model, method)
            res = fct_src(cr, uid_orig, model.model, method, *args, **kw)
        else: # method is write, action or workflow action
            res_ids = []
            if args:
                res_ids = args[0]
                if isinstance(res_ids, (long, int)):
                    res_ids = [res_ids]
            if res_ids:
                # store the old values into a dictionary
                old_values = self.get_data(cr, uid_orig, pool, res_ids, model, method)
            # process the original function, workflow trigger...
            res = fct_src(cr, uid_orig, model.model, method, *args, **kw)
            if method == 'copy':
                res_ids = [res]
            if res_ids:
                # check the new values and store them into a dictionary
                new_values = self.get_data(cr, uid_orig, pool, res_ids, model, method)
        # compare the old and new values and create audittrail log if needed
        self.process_data(cr, uid_orig, pool, res_ids, model, method, old_values, new_values, field_list)
        return res

    def get_data(self, cr, uid, pool, res_ids, model, method):
        data = {}
        resource_pool = pool.get(model.model)
        # read all the fields of the given resources in super admin mode
        for resource in resource_pool.read(cr, SUPERUSER_ID, res_ids):
            values = {}
            values_text = {}
            resource_id = resource['id']
            # loop on each field on the res_ids we just have read
            for field in resource:
                if field in ('__last_update', 'id'):
                    continue
                values[field] = resource[field]
                # get the textual value of that field for this record
                values_text[field] = self.get_value_text(cr, SUPERUSER_ID, pool, resource_pool, method, field, resource[field])

                field_obj = resource_pool._all_columns.get(field).column
                if field_obj._type in ('one2many','many2many'):
                    # check if an audittrail rule apply in super admin mode
                    if self.check_rules(cr, SUPERUSER_ID, field_obj._obj, method):
                        # check if the model associated to a *2m field exists, in super admin mode
                        x2m_model_ids = pool.get('ir.model').search(cr, SUPERUSER_ID, [('model', '=', field_obj._obj)])
                        x2m_model_id = x2m_model_ids and x2m_model_ids[0] or False
                        assert x2m_model_id, _("'%s' Model does not exist..." %(field_obj._obj))
                        x2m_model = pool.get('ir.model').browse(cr, SUPERUSER_ID, x2m_model_id)
                        field_resource_ids = list(set(resource[field]))
                        if model.model == x2m_model.model:
                            # we need to remove current resource_id from the many2many to prevent an infinit loop
                            if resource_id in field_resource_ids:
                                field_resource_ids.remove(resource_id)
                        data.update(self.get_data(cr, SUPERUSER_ID, pool, field_resource_ids, x2m_model, method))
    
            data[(model.id, resource_id)] = {'text':values_text, 'value': values}
        return data

    def prepare_audittrail_log_line(self, cr, uid, pool, model, resource_id, method, old_values, new_values, field_list=None):
        if field_list is None:
            field_list = []
        key = (model.id, resource_id)
        lines = {
            key: []
        }
        # loop on all the fields
        for field_name, field_definition in pool.get(model.model)._all_columns.items():
            if field_name in ('__last_update', 'id'):
                continue
            #if the field_list param is given, skip all the fields not in that list
            if field_list and field_name not in field_list:
                continue
            field_obj = field_definition.column
            if field_obj._type in ('one2many','many2many'):
                # checking if an audittrail rule apply in super admin mode
                if self.check_rules(cr, SUPERUSER_ID, field_obj._obj, method):
                    # checking if the model associated to a *2m field exists, in super admin mode
                    x2m_model_ids = pool.get('ir.model').search(cr, SUPERUSER_ID, [('model', '=', field_obj._obj)])
                    x2m_model_id = x2m_model_ids and x2m_model_ids[0] or False
                    assert x2m_model_id, _("'%s' Model does not exist..." %(field_obj._obj))
                    x2m_model = pool.get('ir.model').browse(cr, SUPERUSER_ID, x2m_model_id)
                    # the resource_ids that need to be checked are the sum of both old and previous values (because we
                    # need to log also creation or deletion in those lists).
                    x2m_old_values_ids = old_values.get(key, {'value': {}})['value'].get(field_name, [])
                    x2m_new_values_ids = new_values.get(key, {'value': {}})['value'].get(field_name, [])
                    # We use list(set(...)) to remove duplicates.
                    res_ids = list(set(x2m_old_values_ids + x2m_new_values_ids))
                    if model.model == x2m_model.model:
                        # we need to remove current resource_id from the many2many to prevent an infinit loop
                        if resource_id in res_ids:
                            res_ids.remove(resource_id)
                    for res_id in res_ids:
                        lines.update(self.prepare_audittrail_log_line(cr, SUPERUSER_ID, pool, x2m_model, res_id, method, old_values, new_values, field_list))
            # if the value value is different than the old value: record the change
            if key not in old_values or key not in new_values or old_values[key]['value'][field_name] != new_values[key]['value'][field_name]:
                data = {
                      'name': field_name,
                      'new_value': key in new_values and new_values[key]['value'].get(field_name),
                      'old_value': key in old_values and old_values[key]['value'].get(field_name),
                      'new_value_text': key in new_values and new_values[key]['text'].get(field_name),
                      'old_value_text': key in old_values and old_values[key]['text'].get(field_name)
                }
                lines[key].append(data)
        return lines

    def process_data(self, cr, uid, pool, res_ids, model, method, old_values=None, new_values=None, field_list=None):
        if field_list is None:
            field_list = []
        # loop on all the given ids
        for res_id in res_ids:
            # compare old and new values and get audittrail log lines accordingly
            lines = self.prepare_audittrail_log_line(cr, uid, pool, model, res_id, method, old_values, new_values, field_list)

            # if at least one modification has been found
            for model_id, resource_id in lines:
                name = pool.get(model.model).name_get(cr, uid, [resource_id])[0][1]
                vals = {
                    'method': method,
                    'object_id': model_id,
                    'user_id': uid,
                    'res_id': resource_id,
                    'name': name,
                }
                if (model_id, resource_id) not in old_values and method not in ('copy', 'read'):
                    # the resource was not existing so we are forcing the method to 'create'
                    # (because it could also come with the value 'write' if we are creating
                    #  new record through a one2many field)
                    vals.update({'method': 'create'})
                if (model_id, resource_id) not in new_values and method not in ('copy', 'read'):
                    # the resource is not existing anymore so we are forcing the method to 'unlink'
                    # (because it could also come with the value 'write' if we are deleting the
                    #  record through a one2many field)
                    vals.update({'method': 'unlink'})
                # create the audittrail log in super admin mode, only if a change has been detected
                if lines[(model_id, resource_id)]:
                    log_id = pool.get('audittrail.log').create(cr, SUPERUSER_ID, vals)
                    model = pool.get('ir.model').browse(cr, uid, model_id)
                    self.create_log_line(cr, SUPERUSER_ID, log_id, model, lines[(model_id, resource_id)])
        return True

    def check_rules(self, cr, uid, model, method):
        pool = pooler.get_pool(cr.dbname)
        if 'audittrail.rule' in pool.models:
            model_ids = pool.get('ir.model').search(cr, SUPERUSER_ID, [('model', '=', model),('model','not like', 'ir.%')])
            model_id = model_ids and model_ids[0] or False
            
            if model_id:
                rule_ids = pool.get('audittrail.rule').search(cr, SUPERUSER_ID, [('state', '=', 'subscribed')])
                for rule in pool.get('audittrail.rule').read(cr, SUPERUSER_ID, rule_ids, ['user_id','log_read','log_write','log_create','log_unlink','log_action','log_workflow']):
                    if len(rule['user_id']) == 0 or uid in rule['user_id']:
                        if rule.get('log_'+method,0):
                            return True
                        elif 'has_' not in method and method not in ('default_get','read','fields_view_get','fields_get','search','search_count','name_search','name_get','get','request_get', 'get_sc', 'unlink', 'write', 'create', 'read_group', 'import_data'):
                            if rule['log_action']:
                                return True
        return False

    def execute_cr(self, cr, uid, model, method, *args, **kw):
        fct_src = super(audittrail_objects_proxy_inherit, self).execute_cr 
        if self.check_rules(cr,uid,model,method):
            return self.log_fct(cr, uid, model, method, fct_src, *args, **kw)
        return fct_src(cr, uid, model, method, *args, **kw)

    def exec_workflow_cr(self, cr, uid, model, method, *args, **kw):
        fct_src = super(audittrail_objects_proxy_inherit, self).exec_workflow_cr
        if self.check_rules(cr,uid,model,'workflow'):
            return self.log_fct(cr, uid, model, method, fct_src, *args, **kw)
        return fct_src(cr, uid, model, method, *args, **kw)
audittrail_objects_proxy_inherit()
