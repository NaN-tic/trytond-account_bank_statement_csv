# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from datetime import datetime
from trytond.model import ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.wizard import Button, StateTransition, StateView, Wizard


__all__ = ['CSVProfile', 'AccountBankStatementCSVImportStart',
    'AccountBankStatementCSVImport']
__metaclass__ = PoolMeta


class CSVProfile():
    __name__ = 'csv.profile'

    @classmethod
    def __setup__(cls):
        super(CSVProfile, cls).__setup__()
        cls._error_messages.update({
                'required_fields':
                    'Fields %s are required.',
                })
        cls.model.domain.extend(('model', '=', 'account.bank.statement.line'))

    @classmethod
    def validate(cls, records):
        super(CSVProfile, cls).validate(records)
        cls.check_required(records)

    @classmethod
    def check_required(cls, records):
        for record in records:
            required_fields = ['date', 'description', 'amount']
            for column in record.columns:
                field = column.field.name
                if field in required_fields:
                    required_fields.remove(field)
            if required_fields:
                cls.raise_user_error('required_fields',
                    error_args=(required_fields))


class AccountBankStatementCSVImportStart(ModelView):
    'Account Bank Statement CSV Import start'
    __name__ = 'account.bank.statement.csv.import.start'
    csv_profile = fields.Many2One('csv.profile', 'CSV',
        required=True)
    import_file = fields.Binary('Import File', required=True)
    header = fields.Boolean('Headers',
        help='Set this check box to true if CSV file has headers.')
    attachment = fields.Boolean('Attachment',
        help='Attach CSV file after import.')
    confirm = fields.Boolean('Confirm',
        help='Confirm Bank Statement after import.')
    character_encoding = fields.Selection([
            ('utf-8', 'UTF-8'),
            ('latin-1', 'Latin-1'),
            ], 'Character Encoding')
    skip_repeated = fields.Boolean('Skip Repeated',
        help='If any line of the csv file is already imported, skip it.')

    @classmethod
    def default_csv_profile(cls):
        CSVProfile = Pool().get('csv.profile')
        csv_profiles = CSVProfile.search([])
        if len(csv_profiles) == 1:
            return csv_profiles[0].id

    @classmethod
    def default_header(cls):
        return True

    @classmethod
    def default_attachment(cls):
        return True

    @classmethod
    def default_confirm(cls):
        return True

    @classmethod
    def default_character_encoding(cls):
        CSVProfile = Pool().get('csv.profile')
        csv_profiles = CSVProfile.search([])
        if len(csv_profiles) == 1:
            return csv_profiles[0].character_encoding
        return 'utf-8'

    @fields.depends('csv_profile')
    def on_change_csv_profile(self):
        changes = {}
        if self.csv_profile:
            changes['character_encoding'] = (
                self.csv_profile.character_encoding)
        return changes


class AccountBankStatementCSVImport(Wizard):
    'Account Bank Statement CSV Import'
    __name__ = 'account.bank.statement.csv.import'
    start = StateView('account.bank.statement.csv.import.start',
        'account_bank_statement_csv.import_csv_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Import File', 'import_file', 'tryton-ok', default=True),
            ])
    import_file = StateTransition()

    @classmethod
    def __setup__(cls):
        super(AccountBankStatementCSVImport, cls).__setup__()
        cls._error_messages.update({
                'general_failure': 'Please, check that the CSV file is '
                    'effectively a CSV file.',
                'csv_format_error': 'Please, check that the Statement CSV '
                    'configuration matches with the format of the CSV file.',
                'database_general_failure': 'Database general failure.\n'
                    'Error raised: %s.',
                'statement_already_has_lines':
                    'You cannot import a CSV statement because "%s" '
                    'have lines.',
                'statement_not_draft':
                    'You cannot import a CSV statement because "%s" '
                    'is not draft state.',
                })

    def transition_import_file(self):
        pool = Pool()
        BankStatement = pool.get('account.bank.statement')
        BankStatementLine = pool.get('account.bank.statement.line')
        Attachment = pool.get('ir.attachment')
        context = Transaction().context

        company = context.get('company')
        csv_profile = self.start.csv_profile
        import_file = self.start.import_file
        has_header = self.start.header
        has_attachment = self.start.attachment
        has_confirm = self.start.confirm
        skip_repeated = self.start.skip_repeated

        statement = BankStatement(context['active_id'])
        if statement.lines:
            self.raise_user_error('statement_already_has_lines',
                (statement.rec_name,))
        if statement.state != 'draft':
            self.raise_user_error('statement_not_draft',
                (statement.rec_name,))

        data = csv_profile.read_csv_file(import_file)

        if has_header:
            next(data, None)

        vlist = []
        for row in list(data):
            if not row:
                continue
            values = {}
            domain = []
            for column in csv_profile.columns:
                cells = column.column.split(',')
                try:
                    value = ','.join(row[int(c)] for c in cells)
                except IndexError:
                    self.raise_user_error('csv_format_error')
                values[column.field.name] = column.get_value(value)
                domain.append(
                    (column.field.name, '=', values[column.field.name])
                    )
            if skip_repeated:
                domain.append(
                    ('state', 'in', ('confirmed', 'posted')),
                    )
                if BankStatementLine.search(domain):
                    continue
            values['statement'] = statement.id
            values['state'] = 'draft'
            values['company'] = company
            vlist.append(values)
        BankStatementLine.create(vlist)

        if has_confirm:
            BankStatement.confirm([statement])
            statement.search_reconcile()

        if has_attachment:
            attach = Attachment(
                name=datetime.now().strftime("%y/%m/%d %H:%M:%S"),
                type='data',
                data=import_file,
                resource=str(statement))
            attach.save()

        return 'end'
