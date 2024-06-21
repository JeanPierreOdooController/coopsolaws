# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import *
from math import modf
import base64

class HrResumenPlanilla(models.Model):
    _name = 'hr.resumen.planilla'
    _description = 'Hr Resumen Planilla'
    _rec_name = 'periodo_id'
    _order = 'periodo_id desc'

    periodo_id = fields.Many2one('hr.period',string=u'Periodo',required=True, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('verify', 'En Proceso'),
        ('close', 'Hecho'),
    ], string='Estado', index=True, readonly=True, copy=False, default='draft')
    slip_ids = fields.One2many('hr.resumen.planilla.line', 'resumen_plani_id', string='Recibos', readonly=True,
                               states={'draft': [('readonly', False)]})
    date_start = fields.Date(string='Desde', required=True, readonly=True, states={'draft': [('readonly', False)]})
    date_end = fields.Date(string='Hasta', required=True, readonly=True, states={'draft': [('readonly', False)]})
    payslip_count = fields.Integer(compute='_compute_payslip_count')
    # account_move_id = fields.Many2one('account.move', string='Asiento Contable', readonly=True)
    company_id = fields.Many2one('res.company',string=u'Compañia', default=lambda self: self.env.company)

    # _sql_constraints = [
    #     ('uniq_planilla', 'unique(periodo_id)', "Ya existe una planilla para este periodo. ¡El mes debe ser único!"),
    # ]

    @api.onchange('periodo_id')
    def onchange_periodo(self):
        for rec in self:
            rec.date_start = rec.periodo_id.date_start
            rec.date_end = rec.periodo_id.date_end

    def _compute_payslip_count(self):
        for payslip_run in self:
            payslip_run.payslip_count = len(payslip_run.slip_ids)

    def set_draft(self):
        self.slip_ids.slip_wd_ids.unlink()
        self.slip_ids.slip_salary_ids.unlink()
        self.slip_ids.unlink()
        self.state = 'draft'

    def close_payroll(self):
        self.state = 'close'

    def reopen_payroll(self):
        self.state = 'verify'

    def action_open_payslips(self):
        self.ensure_one()
        return {
			"type": "ir.actions.act_window",
			"res_model": "hr.resumen.planilla.line",
			"views": [[False, "tree"], [False, "form"]],
			"domain": [['id', 'in', self.slip_ids.ids]],
			"name": "Nominas",
		}

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('¡No puede eliminar una planilla que no este en estado borrador!'))
        return super(HrResumenPlanilla, self).unlink()

    def get_consolidado(self):
        for record in self:
            self.env.cr.execute(self._get_sql_employee())
            res_employees = self.env.cr.dictfetchall()
            # print(res_employees)
            for employee in res_employees:
                self.env.cr.execute(self._get_sql_salary(employee['employee_id']))
                res_salarys = self.env.cr.dictfetchall()
                # print(res_salarys)
                self.env.cr.execute(self._get_sql_wd(employee['employee_id']))
                res_wds = self.env.cr.dictfetchall()

                # base_essalud = 0
                # for line in res_salarys:
                #     if line['code']== 'AESSALUD':
                #         if line['total'] <= 1025:
                #             base_essalud= 1025
                #         else:
                #             base_essalud = line['total']

                data={
                    'resumen_plani_id': record.id,
                    'periodo_id':record.periodo_id.id,
                    'identification_id':employee['identification_id'],
                    'employee_id': employee['employee_id'],
                    'contract_id': employee['contract_id'],
                    'holidays': employee['holidays'],
                    'slip_salary_ids': [(0, 0, {
                        'periodo_id': record.periodo_id.id,
                        'identification_id': line['identification_id'],
                        'employee_id': line['employee_id'],
                        'salary_rule_id': line['salary_rule_id'] or '',
                        'category_id' : line['category_id'] or '',
                        'code': line['code'] or '',
                        'sequence': line['sequence'],
                        'amount': line['total']
                        # 'amount': line['total'] if line['code']!='ESSALUD' else base_essalud *0.09
                    }) for line in res_salarys
                    ],
                    'slip_wd_ids': [(0, 0, {
                        'periodo_id': record.periodo_id.id,
                        'identification_id': line['identification_id'],
                        'employee_id': line['employee_id'],
                        'wd_type_id': line['wd_type_id'] or '',
                        'code': line['code'] or '',
                        'number_of_days': line['wd_total_dias'] if line['wd_total_dias'] else 0,
                        'number_of_hours': line['wd_total_horas'] if line['wd_total_horas'] else 0
                    }) for line in res_wds
                    ]
                }
                # print("data",data)
                self.env['hr.resumen.planilla.line'].create(data)
            record.state = 'verify'
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "Generacion exitosa",
                'type': 'rainbow_man',
            }
        }

    def _get_sql_employee(self):
        sql = """
            select
			he.id as employee_id,
			he.identification_id,
			he.name,
			max(hp.contract_id) as contract_id,
			sum(hp.holidays) as holidays
			from hr_payslip hp 
			inner join hr_employee he on he.id = hp.employee_id 
--			inner join hr_contract hc on hc.id = hp.contract_id
			where 
			hp.company_id = %d
			and extract(month from hp.date_to) = %d
			and extract(year from hp.date_to) = %d
			and hp.payslip_run_id is not null
			group by he.id,he.identification_id,he.name
			order by he.name
			"""%(self.company_id.id,int(self.date_start.month),
                 int(self.periodo_id.fiscal_year_id.name))
        return sql

    def _get_sql_salary(self,employee):
        sql = """
            select
			he.id as employee_id,
			he.identification_id,
			he.name,
--			hc.id as contract_id,
			hsr.sequence,
			hsr.code,
			hsr.id as salary_rule_id,
			hsr.category_id,
			sum(hpl.total) as total
			from hr_payslip hp 
			inner join hr_payslip_line hpl on hpl.slip_id = hp.id
			inner join hr_salary_rule hsr on hsr.id = hpl.salary_rule_id
			inner join hr_employee he on he.id = hp.employee_id 
--			inner join hr_contract hc on hc.id = hp.contract_id
			where 
--			hsr.appears_on_payslip = true
			hsr.active = true
			and hsr.company_id = %d
			and extract(month from hp.date_to) = %d
			and extract(year from hp.date_to) = %d
--			and hpl.total <> 0
			and he.id = %d
			and hp.payslip_run_id is not null
			group by he.id,he.identification_id,he.name,
			hsr.sequence,hsr.code,hsr.id,hsr.category_id
			order by he.name, hsr.sequence
			"""%(self.company_id.id,int(self.date_start.month),
                 int(self.periodo_id.fiscal_year_id.name), int(employee))
        return sql

    def _get_sql_wd(self,employee):
        sql = """
			select
			he.id as employee_id,
			he.identification_id,
			he.name,
--			hc.id as contract_id,
			hpwdt.code as code,
			hpwdt.id as wd_type_id,
			sum(hpwd.number_of_days) as wd_total_dias,
			sum(hpwd.number_of_hours) as wd_total_horas
			from hr_payslip hp 
			inner join hr_employee he on he.id = hp.employee_id 
--			inner join hr_contract hc on hc.id = hp.contract_id
			left join hr_payslip_worked_days hpwd on hpwd.payslip_id=hp.id
			left join hr_payslip_worked_days_type hpwdt on hpwdt.id=hpwd.wd_type_id
			where 
			hp.company_id = %d
			and extract(month from hp.date_to) = %d
			and extract(year from hp.date_to) = %d
--			and(hpwd.number_of_days <> 0 or hpwd.number_of_hours <> 0)
			and he.id = %d
			and hp.payslip_run_id is not null
			group by he.id,he.identification_id,he.name,hpwdt.code,hpwdt.id
			order by he.name
			""" %(self.company_id.id,int(self.date_start.month),
                  int(self.periodo_id.fiscal_year_id.name), int(employee))
        return sql

    def tab_payroll(self):
        return {
            'name': 'Planilla Tabular',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.planilla.tabular.resumen.wizard',
            'context': {'default_resumen_plani_id': self.id},
            'target': 'new',
        }

    def generate_afp_net(self):
        import io
        from xlsxwriter.workbook import Workbook
        if len(self.ids) > 1:
            raise UserError('No se puede seleccionar mas de un registro para este proceso')
        ReportBase = self.env['report.base']
        MainParameter = self.env['hr.main.parameter'].get_main_parameter()
        directory = MainParameter.dir_create_file
        insurable_remuneration = MainParameter.insurable_remuneration
        if not directory:
            raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

        workbook = Workbook(directory + 'AFP_NET.xlsx')
        workbook, formats = ReportBase.get_formats(workbook)

        import importlib
        import sys
        importlib.reload(sys)

        worksheet = workbook.add_worksheet("AFP NET")
        worksheet.set_tab_color('blue')
        x = 0

        for c, slip in enumerate(self.slip_ids):
            # print("slip.contract_id",slip.contract_id)
            if slip.contract_id.membership_id.is_afp:
                Contract = slip.contract_id
                Employee = slip.contract_id.employee_id
                FirstContract = self.env['hr.contract'].get_first_contract(Employee, Contract)
                ir_line = self.env['hr.resumen.planilla.line.salary'].search([('salary_rule_id', '=', insurable_remuneration.id),('resumen_salary_line_id', '=', slip.id)])
                # print("ir_line",ir_line)
                worksheet.write(x, 0, c)
                worksheet.write(x, 1, Contract.cuspp if Contract.cuspp else '')
                worksheet.write(x, 2, Employee.type_document_id.afp_code if Employee.type_document_id.afp_code else '')
                worksheet.write(x, 3, Employee.identification_id if Employee.identification_id else '')
                worksheet.write(x, 4, Employee.last_name if Employee.last_name else '')
                worksheet.write(x, 5, Employee.m_last_name if Employee.m_last_name else '')
                worksheet.write(x, 6, Employee.names if Employee.names else '')
                worksheet.write(x, 7, 'N' if Contract.situation_id.code == '0' else 'S')
                worksheet.write(x, 8, 'S' if FirstContract.date_start >= self.periodo_id.date_start and FirstContract.date_start <= self.periodo_id.date_end else 'N')
                worksheet.write(x, 9, 'S' if FirstContract.date_end and FirstContract.date_end >= self.periodo_id.date_start and FirstContract.date_end <= self.periodo_id.date_end else 'N')
                worksheet.write(x, 10, Contract.exception if Contract.exception else '')
                worksheet.write(x, 11, ir_line.amount if ir_line.amount else 0.00, formats['numberdosespecial'])
                worksheet.write(x, 12, 0.00, formats['numberdosespecial'])
                worksheet.write(x, 13, 0.00, formats['numberdosespecial'])
                worksheet.write(x, 14, 0.00, formats['numberdosespecial'])
                worksheet.write(x, 15, Contract.work_type if Contract.work_type else 'N')
                x += 1

        widths = [2, 15, 2, 12, 20, 20, 20, 2, 2, 2, 2, 8, 8, 8, 8, 2]
        worksheet = ReportBase.resize_cells(worksheet,widths)
        workbook.close()
        f = open(directory + 'AFP_NET.xlsx', 'rb')
        return self.env['popup.it'].get_file('AFP_NET.xlsx',base64.encodebytes(b''.join(f.readlines())))

    def vouchers_by_lot(self):
        if len(self.ids) > 1:
            raise UserError('No se puede seleccionar mas de un registro para este proceso')
        return self.env['hr.resumen.planilla.line'].get_vouchers(self.slip_ids)

    def generate_plame_rem(self):
        if len(self.ids) > 1:
            raise UserError('Solo se puede mostrar una planilla a la vez, seleccione solo una Planilla')
        MainParameter = self.env['hr.main.parameter'].get_main_parameter()
        if not MainParameter.dir_create_file:
            raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

        first = datetime.strftime(self.periodo_id.date_end, '%Y-%m-%d')[:4]
        second = datetime.strftime(self.periodo_id.date_end, '%Y-%m-%d')[5:7]
        doc_name = '%s0601%s%s%s.rem' % (MainParameter.dir_create_file, first, second, self.company_id.vat)

        f = open(doc_name, 'w+')
        for payslip_run in self.browse(self.ids):
            employees = []
            for payslip in payslip_run.slip_ids:
                if payslip.employee_id.id not in employees:
                    sql = """
							select min(a1.doc_type) as doc_type,
								a1.dni,
								a1.sunat,
								sum(a1.amount_earn) as amount_earn,
								sum(a1.amount_paid) as amount_paid
							from (
							select
							htd.sunat_code as doc_type,
							he.identification_id as dni,
							sr.sunat_code as sunat,
							hpl.amount as amount_earn,
							hpl.amount as amount_paid
							from hr_resumen_planilla hpr
							inner join hr_resumen_planilla_line hp on hpr.id = hp.resumen_plani_id
							inner join hr_resumen_planilla_line_salary hpl on hp.id = hpl.resumen_salary_line_id
							inner join (select * from hr_salary_rule where company_id= %d) as sr on sr.code = hpl.code
							inner join hr_employee he on he.id = hpl.employee_id
							left join hr_type_document htd on htd.id = he.type_document_id
							where  hpr.id =  %d
							and he.id =  %d
							and sr.sunat_code != ''
							and sr.sunat_code not in ('0804','0607','0605','0601')
							and hpl.amount != 0
							union all 
							select
							htd.sunat_code as doc_type,
							he.identification_id as dni,
							sr.sunat_code as sunat,
							hpl.amount as amount_earn,
							hpl.amount as amount_paid
							from hr_resumen_planilla hpr
							inner join hr_resumen_planilla_line hp on hpr.id = hp.resumen_plani_id
							inner join hr_resumen_planilla_line_salary hpl on hp.id = hpl.resumen_salary_line_id
							inner join (select * from hr_salary_rule where company_id= %d) as sr on sr.code = hpl.code
							inner join hr_employee he on he.id = hpl.employee_id
							left join hr_type_document htd on htd.id = he.type_document_id
							where  hpr.id =  %d
							and he.id =  %d
							and sr.sunat_code in ('0605','0601')) a1
							group by a1.sunat, a1.dni
							order by a1.sunat 
							""" % (self.company_id.id,payslip_run.id, payslip.employee_id.id,
                                   self.company_id.id,payslip_run.id, payslip.employee_id.id)
                    self._cr.execute(sql)
                    data = self._cr.dictfetchall()
                    # print("data",data)
                    for line in data:
                        f.write("%s|%s|%s|%s|%s|\r\n" % (
                            line['doc_type'],
                            line['dni'],
                            line['sunat'],
                            line['amount_earn'],
                            line['amount_paid']
                        ))
                employees.append(payslip.employee_id.id)
        f.close()
        f = open(doc_name, 'rb')
        return self.env['popup.it'].get_file('0601%s%s%s.rem' % (first, second, self.company_id.vat),base64.encodebytes(b''.join(f.readlines())))

    def generate_plame_jor(self):
        if len(self.ids) > 1:
            raise UserError('Solo se puede mostrar una planilla a la vez, seleccione solo una Planilla')
        MainParameter = self.env['hr.main.parameter'].get_main_parameter()
        if not MainParameter.dir_create_file:
            raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

        first = datetime.strftime(self.periodo_id.date_end, '%Y-%m-%d')[:4]
        second = datetime.strftime(self.periodo_id.date_end, '%Y-%m-%d')[5:7]
        doc_name = '%s0601%s%s%s.jor' % (MainParameter.dir_create_file, first, second, self.company_id.vat)

        f = open(doc_name, 'w+')
        for payslip_run in self.browse(self.ids):
            employees = []
            for payslip in payslip_run.slip_ids:
                if payslip.employee_id.id not in employees:
                    sql = """
							select
							min(htd.sunat_code) as doc_type,
							he.identification_id as dni,
							sum(case when hpwd.wd_type_id in ({dlab}) then hpwd.number_of_days else 0 end) as dlab,
							sum(case when hpwd.wd_type_id in ({fal}) then hpwd.number_of_days else 0 end) as fal,
							sum(case when hpwd.wd_type_id in ({hext}) then hpwd.number_of_hours else 0 end) as hext,
							sum(case when hpwd.wd_type_id in ({dvac}) then hpwd.number_of_days else 0 end) as dvac,
							min(rc.hours_per_day) as hours_per_day
							from hr_resumen_planilla_line hp
							inner join hr_employee he on he.id = hp.employee_id
							inner join hr_contract hc on hc.id = hp.contract_id
							inner join resource_calendar rc on rc.id = hc.resource_calendar_id
							inner join hr_resumen_planilla_line_wd hpwd on hpwd.resumen_wd_line_id = hp.id
							inner join hr_payslip_worked_days_type hpwdt on hpwdt.id = hpwd.wd_type_id
							left join hr_type_document htd on htd.id = he.type_document_id
							where hp.resumen_plani_id = {pr_id}
							and hp.employee_id = {emp_id}
							and hpwd.wd_type_id in ({dlab},{fal},{hext},{dvac})
							group by htd.sunat_code, he.identification_id
							""".format(
                        pr_id = payslip_run.id,
                        emp_id = payslip.employee_id.id,
                        dlab = ','.join(str(id) for id in MainParameter.wd_dlab.ids),
                        fal = ','.join(str(id) for id in MainParameter.wd_dnlab.ids),
                        hext = ','.join(str(id) for id in MainParameter.wd_ext.ids),
                        dvac = ','.join(str(id) for id in MainParameter.wd_dvac.ids)
                    )
                    self._cr.execute(sql)
                    data = self._cr.dictfetchall()
                    # print("data",data)
                    for line in data:
                        # dlab = payslip.get_dlabs()
                        hlab = modf(line['dlab'] * line['hours_per_day'])
                        # print("hlab",hlab)
                        f.write("%s|%s|%d|0|%d|0|\r\n" % (
                            line['doc_type'],
                            line['dni'],
                            hlab[1],
                            line['hext']
                        ))
                employees.append(payslip.employee_id.id)
        f.close()
        f = open(doc_name, 'rb')
        return self.env['popup.it'].get_file('0601%s%s%s.jor' % (first, second, self.company_id.vat),base64.encodebytes(b''.join(f.readlines())))
