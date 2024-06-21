DROP FUNCTION IF EXISTS public.get_saldos_anexos(date, date, integer,character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_anexos(
    date_from date,
	date_to date,
	id_company integer,
	prefix character varying)
  	RETURNS TABLE(id bigint, periodo text, fecha_con date, libro character varying, voucher character varying, td_partner character varying, 
	doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, 
	fecha_ven date, cuenta character varying, moneda character varying, debe numeric, haber numeric, saldo_mn numeric, saldo_me numeric,
	aml_ids integer[], journal_id integer, account_id integer, partner_id integer, move_id integer, move_line_id integer, company_id integer)
	LANGUAGE 'plpgsql'
		COST 100
		VOLATILE 
		ROWS 1000
	AS $BODY$
	BEGIN
		RETURN QUERY 
		SELECT row_number() OVER () AS id,t.*
		   FROM ( select 
		b2.periodo, 
		b2.fecha::date as fecha_con, 
		b2.libro, 
		b2.voucher, 
		b2.td_partner, 
		b2.doc_partner, 
		b2.partner, 
		b2.td_sunat,
		b2.nro_comprobante, 
		b2.fecha_doc,
		b2.fecha_ven,
		b2.cuenta,
		b2.moneda,
		b1.sum_debe as debe,
		b1.sum_haber as haber,
		b1.sum_balance as saldo_mn,
		b1.sum_importe_me as saldo_me,
		b1.aml_ids,
		b2.journal_id,
		b2.account_id,
		b2.partner_id,
		b2.move_id,
		b2.move_line_id,
		b2.company_id
		from(
		select a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante,
		sum(a1.debe) as sum_debe, sum(a1.haber) as sum_haber, sum(a1.balance) as sum_balance, 
		sum(a1.importe_me) as sum_importe_me, min(a1.move_line_id) as min_line_id,
		array_agg(aml.id) as aml_ids
		from vst_diariog a1
		inner join account_move_line aml on aml.id = a1.move_line_id
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = a1.account_id
		where left(a2.code,2) = $4 and (a1.fecha::date between $1::date and $2::date) and a1.company_id = $3
		group by a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante
		having sum(a1.balance) <> 0)b1
		left join vst_diariog  b2 on b2.move_line_id = b1.min_line_id
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc) t;
		END;
		$BODY$;