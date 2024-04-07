from odoo import models, fields

class ContractPart(models.Model):
    _name = 'contacts_contract.contract_part'
    _description = 'Contract part'

    name = fields.Char(required=True)