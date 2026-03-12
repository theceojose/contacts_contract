from odoo import fields, models

class ResParnertInherit(models.Model):
    _inherit = 'res.partner'

    related_contract_count = fields.Integer(string='Contract', compute='_compute_related_contract_count')

    def action_redirect_to_contract(self):
        return {
            'name': ('Contract'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'contacts_contract.contract',
            'domain': [('partner_id', '=', self.id), ('state', '=', 'open')],
            'context': {'default_partner_id': self.id}
            }  
    def _compute_related_contract_count(self):
        for cont in self:
            cont.related_contract_count = self.env['contacts_contract.contract'].search_count([('partner_id', '=', cont.id), ('state', '=', 'open')])