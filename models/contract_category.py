from odoo import models, fields

class ContractCategory(models.Model):
    _name = 'contacts_contract.contract_category'
    _description = 'Contract category'

    name = fields.Char(required=True)