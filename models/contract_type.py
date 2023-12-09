from odoo import models, fields

class ContractType(models.Model):
    _name = 'contacts_contract.contract_type'
    _description = 'Contract type'

    name = fields.Char(required=True)