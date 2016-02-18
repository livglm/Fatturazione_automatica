from openerp import api, models

class ParticularReport(models.AbstractModel):
    _name = 'report.Fatturazione_automatica.test_report'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('Fatturazione_automatica.test_report')
        #self.env.cr.execute('SELECT * FROM account_invoice WHERE salesagent_id IN (select id from res_partner where salesagent = True) and residual <> 0  ORDER BY salesagent_id,partner_id, date_invoice,number ASC')
        self.env.cr.execute('SELECT * FROM res_partner WHERE salesagent = True order by name ASC')
        agenti = self.env.cr.fetchall()

        print agenti

        docargs = {
        'doc_ids': self._ids,
        'doc_model': report.model,
        'docs': self ##self.env[report.model].search([('salesagent_id','in',agenti),('residual','<>',0)]),
        }
        return report_obj.render('Fatturazione_automatica.test_report', docargs)