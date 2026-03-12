from odoo import models, fields

class ContractMilestone(models.Model):
    _name = 'contacts_contract.contract_milestone'
    _description = 'Contract Milestone'
    _order = 'sequence'

    name = fields.Char(string="Description", required=True)
    date = fields.Date('Date', required=True)
    sequence = fields.Integer(default=1)
    contract_id = fields.Many2one('contacts_contract.contract', string='contract')