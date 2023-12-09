from odoo import _, api, fields, models
from dateutil.relativedelta import relativedelta

class Contract(models.Model):
    _name = 'contacts_contract.contract'
    _description = 'Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'state desc,expiration_date'
    
    def compute_next_year_date(self, strdate):
        oneyear = relativedelta(years=1)
        start_date = fields.Date.from_string(strdate)
        return fields.Date.to_string(start_date + oneyear)

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    name = fields.Char(string='Name', compute='_compute_contract_name', store=True, required=True)
    active = fields.Boolean(default=True)
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user, index=True, help='Responsible for the document', required=True)
    start_date = fields.Date(
        'Document Start Date', default=fields.Date.context_today,
        help='Date when the coverage of the document begins')
    expiration_date = fields.Date(
        'Document Expiration Date', default=lambda self:
        self.compute_next_year_date(fields.Date.context_today(self)),
        help='Date when the coverage of the document expirates (by default, one year after begin date)')
    days_left = fields.Integer(compute='_compute_days_left', string='Warning Date')
    expires_today = fields.Boolean(compute='_compute_days_left')
    partner_id = fields.Many2one('res.partner', 'Contact', required=True)
    ins_ref = fields.Char('Reference', size=64, copy=False, required=True)
    state = fields.Selection(
        [('futur', 'Incoming'),
         ('open', 'In Progress'),
         ('expired', 'Expired'),
         ('closed', 'Closed')
        ], 'Status', default='futur', readonly=True,
        help='Choose whether the document is still valid or not',
        tracking=True,
        copy=False)
    contract_type_id = fields.Many2one('contacts_contract.contract_type', string='Document Type', required=True)
    contract_category_id = fields.Many2one('contacts_contract.contract_category', string='Document category')
    contract_part_id = fields.Many2one('contacts_contract.contract_part', string='Part')
    document = fields.Binary('Documents', copy=False)
    notes = fields.Html('Terms and Conditions', copy=False)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    amount_contract = fields.Monetary('Amount', help='Amount of the document')
    payment_date = fields.Date('Payment Date')
    finance_note = fields.Html('Note', copy=False)
    milestones_ids = fields.One2many('contacts_contract.contract_milestone', 'contract_id', string='milestones')
    contract_relational_id = fields.Many2one('contacts_contract.contract', string='Relational agreements')
    contract_add_note = fields.Html('Note', copy=False)

    contract_add_count = fields.Integer(string='Additional document', compute='_compute_additional_contract_count')

    _sql_constraints = [("ins_ref_uniq", "unique(ins_ref)", "The are other document with this Reference")]

    @api.depends('expiration_date', 'state')
    def _compute_days_left(self):
        """return a dict with as value for each contract an integer
        if contract is in an open state and is overdue, return 0
        if contract is in a closed state, return -1
        otherwise return the number of days before the contract expires
        """
        today = fields.Date.from_string(fields.Date.today())
        for record in self:
            if record.expiration_date and record.state in ['open', 'expired']:
                renew_date = fields.Date.from_string(record.expiration_date)
                diff_time = (renew_date - today).days
                record.days_left = diff_time if diff_time > 0 else 0
                record.expires_today = diff_time == 0
            else:
                record.days_left = -1
                record.expires_today = False

    def write(self, vals):
        res = super(Contract, self).write(vals)
        if 'start_date' in vals or 'expiration_date' in vals:
            date_today = fields.Date.today()
            future_contracts, running_contracts, expired_contracts = self.env[self._name], self.env[self._name], self.env[self._name]
            for contract in self.filtered(lambda c: c.start_date and c.state != 'closed'):
                if date_today < contract.start_date:
                    future_contracts |= contract
                elif not contract.expiration_date or contract.start_date <= date_today <= contract.expiration_date:
                    running_contracts |= contract
                else:
                    expired_contracts |= contract
            future_contracts.action_draft()
            running_contracts.action_open()
            expired_contracts.action_expire()
        if vals.get('expiration_date') or vals.get('user_id'):
            self.activity_reschedule(['contacts_contract.mail_act_contacts_contract_contract_to_renew'], date_deadline=vals.get('expiration_date'), new_user_id=vals.get('user_id'))
        return res

    def action_close(self):
        self.write({'state': 'closed'})

    def action_draft(self):
        self.write({'state': 'futur'})

    def action_open(self):
        self.write({'state': 'open'})

    def action_expire(self):
        self.write({'state': 'expired'})

    @api.model
    def scheduler_manage_contract_expiration(self):
        # This method is called by a cron task
        # It manages the state of a contract, possibly by posting a message on the vehicle concerned and updating its status
        params = self.env['ir.config_parameter'].sudo()
        delay_alert_contract = int(params.get_param('contacts_contract.delay_alert_contract', default=30))
        date_today = fields.Date.from_string(fields.Date.today())
        outdated_days = fields.Date.to_string(date_today + relativedelta(days=+delay_alert_contract))
        reminder_activity_type = self.env.ref('contacts_contract.mail_act_contacts_contract_contract_to_renew', raise_if_not_found=False) or self.env['mail.activity.type']
        nearly_expired_contracts = self.search([
            ('state', '=', 'open'),
            ('expiration_date', '<', outdated_days),
            ('user_id', '!=', False)
        ]
        ).filtered(
            lambda nec: reminder_activity_type not in nec.activity_ids.activity_type_id
        )

        for contract in nearly_expired_contracts:
            contract.activity_schedule(
                'contacts_contract.mail_act_contacts_contract_contract_to_renew', contract.expiration_date,
                user_id=contract.user_id.id)

        expired_contracts = self.search([('state', 'not in', ['expired', 'closed']), ('expiration_date', '<',fields.Date.today() )])
        expired_contracts.write({'state': 'expired'})

        futur_contracts = self.search([('state', 'not in', ['futur', 'closed']), ('start_date', '>', fields.Date.today())])
        futur_contracts.write({'state': 'futur'})

        now_running_contracts = self.search([('state', '=', 'futur'), ('start_date', '<=', fields.Date.today())])
        now_running_contracts.write({'state': 'open'})

    def run_scheduler(self):
        self.scheduler_manage_contract_expiration()

    def action_redirect_to_additional_contract(self):
        return {
            'name': ('Additional contract'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'contacts_contract.contract',
            'domain': [('contract_relational_id', '=', self.ids)],
            'context': {'default_partner_id': self.partner_id.id, 'default_contract_relational_id': self.id}
            }  
    def _compute_additional_contract_count(self):
        self.contract_add_count = self.env['contacts_contract.contract'].search_count([('contract_relational_id', '=', self.ids)])