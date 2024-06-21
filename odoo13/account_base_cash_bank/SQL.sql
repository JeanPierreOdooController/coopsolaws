DROP FUNCTION IF EXISTS public.base_ple_caja_bancos(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.base_ple_caja_bancos(
	date_from date,
	date_to date,
	company_id integer)
RETURNS TABLE(id_linea integer, id_asiento integer, periodo text, libro character varying, asiento character varying, cuenta character varying, debe numeric, haber numeric, 
    code_banco character varying, nro_cuenta character varying, medio_de_pago character varying, nro_operacion character varying) AS
	$BODY$
	BEGIN
	RETURN QUERY 
select
aml.id as id_linea,
am.id as id_asiento,
CASE
    WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text
    WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text
    ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)
END AS periodo,
aj.code as libro,
am.name as asiento,
aa.code as cuenta,
aml.debit as debe,
aml.credit as haber,
aa.code_bank as code_banco,  --campo22
aa.account_number as nro_cuenta,--campo23
ecp.code as medio_de_pago,--campo24
case when aml.nro_comp is null then am.name else aml.nro_comp end as nro_operacion--campo25
from account_move_line aml
left join account_move am on am.id=aml.move_id
left join account_account aa on aa.id=aml.account_id
left join account_journal aj on aj.id=am.journal_id
LEFT JOIN einvoice_catalog_payment ecp ON ecp.id = am.td_payment_id
where aa.internal_type='liquidity'
order by (date_part('month'::text, am.date)),aj.code,am.name,aa.code;
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;