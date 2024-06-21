------------------------------------------account_balance_doc_rep_it---------------------------------------------------------------
----------Obtenemos los saldos por fecha de documento,fecha de documento y si el balance es 0 , fecha contable ,fecha contable y si el balance es 0
DROP FUNCTION IF EXISTS public.get_pre_saldos(date, date, integer, character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_pre_saldos(
	date_from date,
	date_to date,
	company_id integer,
	type character varying)
    RETURNS TABLE(partner_id integer, account_id integer, type_document_id integer, nro_comp character varying, move_line_id integer) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY 

select  a1.account_id,a1.partner_id,a1.type_document_id,a1.nro_comp,a1.id as move_line_id from account_move_line a1
left join account_move a2 on a2.id=a1.move_id
left join account_account a3 on a3.id=a1.account_id
left join account_account_type a4 on a4.id=a3.user_type_id
where a2.company_id=$3 and a2.type in ('in_invoice','in_refund','out_invoice','out_refund') and a4.type in ('payable','receivable')
and ((case when $4 = 'invoice_date' then a2.invoice_date else a2.date end) between $1 and $2);
END;
$BODY$;
------------------------------------------------------------------------------------------------------------------------------

DROP FUNCTION IF EXISTS public.get_saldos(date, date, integer, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos(
    IN date_ini date,
    IN date_fin date,
    IN id_company integer,
    IN query_type integer)
  RETURNS TABLE(id bigint, periodo text, fecha_con date, libro character varying, voucher character varying, td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, fecha_ven date, cuenta character varying, moneda character varying, debe numeric, haber numeric, saldo_mn numeric, saldo_me numeric,aml_ids integer[], journal_id integer, account_id integer, partner_id integer, move_id integer, move_line_id integer, company_id integer) AS
$BODY$
BEGIN
	IF query_type = 0 THEN
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
		$3 as company_id
from(
		select aml.partner_id, aml.account_id, ei.code as td_sunat, TRIM(aml.nro_comp) as nro_comprobante,
		sum(aml.debit) as sum_debe, sum(aml.credit) as sum_haber, sum(aml.balance) as sum_balance, 
		sum(aml.amount_currency) as sum_importe_me, min(aml.id) as min_line_id,
		array_agg(aml.id) as aml_ids
		from account_move_line aml
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = aml.account_id
		LEFT JOIN einvoice_catalog_01 ei ON ei.id = aml.type_document_id
		where (a2.is_document_an = True) and am.state::text = 'posted'::text AND aml.display_type IS NULL AND aml.account_id IS NOT NULL AND (am.date::date BETWEEN $1 and $2) AND am.company_id = $3
		group by aml.partner_id, aml.account_id, ei.code, TRIM(aml.nro_comp)
)b1
		left join get_diariog($1,$2,$3) b2 on b2.move_line_id = b1.min_line_id
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc) t;
ELSIF query_type = 1 THEN
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
		$3 as company_id
from(
		select aml.partner_id, aml.account_id, ei.code as td_sunat, TRIM(aml.nro_comp) as nro_comprobante,
		sum(aml.debit) as sum_debe, sum(aml.credit) as sum_haber, sum(aml.balance) as sum_balance, 
		sum(aml.amount_currency) as sum_importe_me, min(aml.id) as min_line_id,
		array_agg(aml.id) as aml_ids
		from account_move_line aml
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = aml.account_id
		LEFT JOIN einvoice_catalog_01 ei ON ei.id = aml.type_document_id
		where (a2.is_document_an = True) and am.state::text = 'posted'::text AND aml.display_type IS NULL AND aml.account_id IS NOT NULL AND (am.date::date BETWEEN $1 and $2) AND am.company_id = $3
		group by aml.partner_id, aml.account_id, ei.code, TRIM(aml.nro_comp)
		having sum(aml.balance) <> 0
)b1
		left join get_diariog($1,$2,$3)  b2 on b2.move_line_id = b1.min_line_id
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc) t;
ELSIF query_type = 2 THEN 
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
		$3 as company_id
from(
		select aml.partner_id, aml.account_id, ei.code as td_sunat, TRIM(aml.nro_comp) as nro_comprobante,
		sum(aml.debit) as sum_debe, sum(aml.credit) as sum_haber, sum(aml.balance) as sum_balance, 
		sum(aml.amount_currency) as sum_importe_me, min(aml.id) as min_line_id,
		array_agg(aml.id) as aml_ids
		from account_move_line aml
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = aml.account_id
		LEFT JOIN einvoice_catalog_01 ei ON ei.id = aml.type_document_id
		where (a2.is_document_an = True) and am.state::text = 'posted'::text AND aml.display_type IS NULL AND aml.account_id IS NOT NULL AND (am.invoice_date::date BETWEEN $1 and $2) AND am.company_id = $3
		group by aml.partner_id, aml.account_id, ei.code, TRIM(aml.nro_comp)
)b1
		left join get_diariog($1,$2,$3)  b2 on b2.move_line_id = b1.min_line_id
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc) t;
ELSIF query_type = 3 THEN 
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
		$3 as company_id
from(
		select aml.partner_id, aml.account_id, ei.code as td_sunat, TRIM(aml.nro_comp) as nro_comprobante,
		sum(aml.debit) as sum_debe, sum(aml.credit) as sum_haber, sum(aml.balance) as sum_balance, 
		sum(aml.amount_currency) as sum_importe_me, min(aml.id) as min_line_id,
		array_agg(aml.id) as aml_ids
		from account_move_line aml
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = aml.account_id
		LEFT JOIN einvoice_catalog_01 ei ON ei.id = aml.type_document_id
		where (a2.is_document_an = True) and am.state::text = 'posted'::text AND aml.display_type IS NULL AND aml.account_id IS NOT NULL AND (am.invoice_date::date BETWEEN $1 and $2) AND am.company_id = $3
		group by aml.partner_id, aml.account_id, ei.code, TRIM(aml.nro_comp)
		having sum(a1.balance) <> 0
)b1
		left join get_diariog($1,$2,$3)  b2 on b2.move_line_id = b1.min_line_id
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc) t;
END IF;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

---------------------------------------------------------------------------------------------------------------------------------------------------------------
----------Con esta funcion obtenemos el detalle de comprobante, donde los parametros son fecha inicial, fecha final y company_id

DROP FUNCTION IF EXISTS public.get_saldo_detalle(date, date, integer) CASCADE;
CREATE OR REPLACE FUNCTION public.get_saldo_detalle(
	date_from date,
	date_to date,
	company_id integer)
	RETURNS TABLE(periodo character varying, fecha date, libro character varying, voucher character varying,td_partner character varying, 
	doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, 
	fecha_ven date, cuenta character varying, moneda character varying, debe numeric, haber numeric,balance numeric,importe_me numeric, 
	saldo numeric, saldo_me numeric, partner_id integer, account_id integer) AS
	$BODY$
	BEGIN
	RETURN QUERY 
select 
CASE
	WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::character varying
	WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::character varying
	ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::character varying
END AS periodo,
T.fecha,
aj.code as libro,
am.name AS voucher,
llit.code_sunat as td_partner,
rp.vat as doc_partner,
rp.name as partner,
ei.code as td_sunat,
TRIM(aml.nro_comp) as nro_comprobante,
am.invoice_date AS fecha_doc,
aml.date_maturity AS fecha_ven,
aa.code as cuenta,
CASE
	WHEN rc.name IS NULL THEN 'PEN'::character varying
	ELSE rc.name
END AS moneda,
T.debit as debe,
T.credit as haber,
T.balance,
T.balance_me as importe_me,
sum(coalesce(T.balance,0)) OVER (partition by aml.partner_id, T.account_id,ei.code, TRIM(aml.nro_comp) order by aml.partner_id, T.account_id,ei.code,TRIM(aml.nro_comp), T.fecha) as saldo,
sum(coalesce(T.balance_me,0)) OVER (partition by aml.partner_id, T.account_id,ei.code, TRIM(aml.nro_comp) order by aml.partner_id, T.account_id,ei.code, TRIM(aml.nro_comp), T.fecha) as saldo_me,
aml.partner_id,
T.account_id from (
select 
am.id as move_id,
aml.id as move_line_id,
am.date as fecha,
aml.account_id,
aml.debit,
aml.credit,
coalesce(aml.balance,0) as balance,
aml.amount_currency as balance_me
from account_move_line aml
left join account_move am on am.id=aml.move_id
LEFT JOIN account_account aa ON aa.id = aml.account_id
where (am.date between date_from and date_to)
and  am.state='posted'
and aml.display_type is NULL
and aa.is_document_an = True
and am.company_id=$3
)T
LEFT JOIN account_move_line aml ON T.move_line_id = aml.id
LEFT JOIN account_move am ON T.move_id = am.id
LEFT JOIN account_journal aj ON aj.id = am.journal_id
LEFT JOIN account_account aa ON aa.id = T.account_id
LEFT JOIN res_currency rc ON rc.id = aml.currency_id
LEFT JOIN res_partner rp ON rp.id = aml.partner_id
LEFT JOIN l10n_latam_identification_type llit ON llit.id = rp.l10n_latam_identification_type_id
LEFT JOIN einvoice_catalog_01 ei ON ei.id = aml.type_document_id
order by aml.partner_id, T.account_id,ei.code, TRIM(aml.nro_comp), T.fecha;
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;

------------------------------------------account_balance_doc_rep_it---------------------------------------------------------------
UPDATE account_account SET is_document_an=TRUE WHERE internal_type IN ('payable','receivable');
UPDATE account_account SET is_document_an=FALSE WHERE internal_type NOT IN ('payable','receivable');
------------------------------------------exchange_diff_config_it--------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.get_saldos_me_global(
	periodo_apertura character,
	periodo character,
	company_id integer)
    RETURNS TABLE(account_id integer, debe numeric, haber numeric, saldomn numeric, saldome numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY   
	SELECT a1.account_id,
		sum(a1.debe) AS debe,
		sum(a1.haber) AS haber,
		sum(coalesce(a1.balance,0)) AS saldomn,
		sum(coalesce(a1.importe_me,0)) AS saldome
	   	FROM vst_diariog a1
		LEFT JOIN account_account a2 ON a2.id = a1.account_id
		LEFT JOIN res_currency a4 on a4.id = a2.currency_id
	  	WHERE a4.name = 'USD' AND
		a2.is_document_an <> TRUE AND a1.periodo::integer >= $1::integer AND a1.periodo::integer <= $2::integer AND a1.company_id = $3
	  	GROUP BY a1.account_id;
END;
$BODY$;

--------------------------------------------------------------------------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.get_saldos_me_global_2(
	periodo_apertura character,
	periodo character,
	company_id integer)
    RETURNS TABLE(account_id integer, debe numeric, haber numeric, saldomn numeric, saldome numeric, group_balance character varying, tc numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
 SELECT
    b1.account_id,
    b1.debe,
    b1.haber,
    b1.saldomn,
    b1.saldome,
    b3.group_balance,
        CASE
            WHEN b3.group_balance::text = ANY (ARRAY['B1'::character varying, 'B2'::character varying]::text[]) THEN ( SELECT edcl.compra
               FROM exchange_diff_config_line edcl
                 LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
                 LEFT JOIN account_period ap ON ap.id = edcl.period_id
              WHERE edc.company_id = $3 AND ap.code::text = $2::text)
            ELSE ( SELECT edcl.venta
               FROM exchange_diff_config_line edcl
                 LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
                 LEFT JOIN account_period ap ON ap.id = edcl.period_id
              WHERE edc.company_id = $3 AND ap.code::text = $2::text)
        END AS tc
   FROM get_saldos_me_global($1,$2,$3) b1
     LEFT JOIN account_account b2 ON b2.id = b1.account_id
     LEFT JOIN account_type_it b3 ON b3.id = b2.account_type_it_id;
END;
$BODY$;

----------------------------------------------------------------------------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.get_saldos_me_global_final(
	fiscal_year character,
	periodo character,
	company_id integer)
    RETURNS TABLE(account_id integer, debe numeric, haber numeric, saldomn numeric, saldome numeric, group_balance character varying, tc numeric, saldo_act numeric, diferencia numeric, difference_account_id integer) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
	SELECT *,
	round(coalesce(vst.tc,0) * vst.saldome,2) AS saldo_act,
	vst.saldomn - round(coalesce(vst.tc,0) * vst.saldome,2) AS diferencia,
	CASE 
	WHEN vst.saldomn < round(vst.tc * vst.saldome,2) AND vst.group_balance IN ('B1','B2') THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN vst.saldomn > round(vst.tc * vst.saldome,2) AND vst.group_balance IN ('B1','B2') THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (-1 * vst.saldomn) > (-1 * round(vst.tc * vst.saldome,2)) AND vst.group_balance IN ('B3','B4','B5') THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (-1 * vst.saldomn) < (-1 * round(vst.tc * vst.saldome,2)) AND vst.group_balance IN ('B3','B4','B5') THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3) END AS difference_account_id
	FROM get_saldos_me_global_2($1||'00',$2,$3) vst
	WHERE vst.saldomn - round(coalesce(vst.tc,0) * vst.saldome,2) <> 0;
END;
$BODY$;
----------------------------------------------------------------------------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.get_saldos_me_documento(
	periodo_apertura character,
	periodo character,
	company_id integer)
    RETURNS TABLE(partner integer, account_id integer, td_sunat character varying, nro_comprobante character varying, debe numeric, haber numeric, saldomn numeric, saldome numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY   
	select a1.partner_id,
	a1.account_id,
	a1.td_sunat,
	a1.nro_comprobante,
	sum(a1.debe) debe,
	sum(a1.haber) haber,
	sum(coalesce(a1.balance,0))as saldomn,
	sum(coalesce(a1.importe_me,0)) as saldome 
	from vst_diariog a1
	left join account_account a2 on a2.id=a1.account_id
	left join account_type_it a3 on a3.id=a2.account_type_it_id
	left join res_currency a4 on a4.id = a2.currency_id
	where 
	a2.is_document_an = TRUE and
	a4.name = 'USD' and
	a1.td_sunat is not null and
	a1.nro_comprobante is not null and
	a1.company_id = $3 and
	(a1.periodo::int between $1::int and $2::int)
	group by a1.partner_id,a1.account_id,a1.td_sunat,a1.nro_comprobante
	having (sum(a1.balance)+sum(a1.importe_me)) <> 0;
END;
$BODY$;

----------------------------------------------------------------------------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.get_saldos_me_documento_2(
	periodo_apertura character,
	periodo character,
	company_id integer)
    RETURNS TABLE(partner integer, account_id integer, td_sunat character varying, nro_comprobante character varying, debe numeric, haber numeric, saldomn numeric, saldome numeric, group_balance character varying, tc numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
select b1.partner,
b1.account_id,
b1.td_sunat,
b1.nro_comprobante,
b1.debe,
b1.haber,
b1.saldomn,
b1.saldome,
b3.group_balance,
CASE
		WHEN b3.group_balance::text = ANY (ARRAY['B1'::character varying, 'B2'::character varying]::text[]) THEN ( SELECT edcl.compra
		   FROM exchange_diff_config_line edcl
			 LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
			 LEFT JOIN account_period ap ON ap.id = edcl.period_id
		  WHERE edc.company_id = $3 AND ap.code::text = $2::text)
		ELSE ( SELECT edcl.venta
		   FROM exchange_diff_config_line edcl
			 LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
			 LEFT JOIN account_period ap ON ap.id = edcl.period_id
		  WHERE edc.company_id = $3 AND ap.code::text = $2::text)
	END AS tc
from get_saldos_me_documento($1,$2,$3) b1
LEFT JOIN account_account b2 ON b2.id = b1.account_id
LEFT JOIN account_type_it b3 ON b3.id = b2.account_type_it_id;
END;
$BODY$;

----------------------------------------------------------------------------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.get_saldos_me_documento_final(
	fiscal_year character,
	periodo character,
	company_id integer)
    RETURNS TABLE(partner integer, account_id integer, td_sunat character varying, nro_comprobante character varying, debe numeric, haber numeric, saldomn numeric, saldome numeric, group_balance character varying, tc numeric, saldo_act numeric, diferencia numeric, difference_account_id integer) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
	SELECT *,
	round(coalesce(vst.tc,0) * vst.saldome,2) AS saldo_act,
	vst.saldomn - round(coalesce(vst.tc,0) * vst.saldome,2) AS diferencia,
	CASE 
	WHEN vst.saldomn < round(vst.tc * vst.saldome,2) AND vst.group_balance IN ('B1','B2') THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN vst.saldomn > round(vst.tc * vst.saldome,2) AND vst.group_balance IN ('B1','B2') THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (-1 * vst.saldomn) > (-1 * round(vst.tc * vst.saldome,2)) AND vst.group_balance IN ('B3','B4','B5') THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (-1 * vst.saldomn) < (-1 * round(vst.tc * vst.saldome,2)) AND vst.group_balance IN ('B3','B4','B5') THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3) END AS difference_account_id
	FROM get_saldos_me_documento_2($1||'00',$2,$3) vst
	WHERE vst.saldomn - round(coalesce(vst.tc,0) * vst.saldome,2) <> 0;
END;
$BODY$;

------------------------------------------exchange_diff_config_it--------------------------------------------------------------------------------------
------------------------------------------maturity_analysis_rep_it------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_maturity_analysis(date, date, integer, character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_maturity_analysis(
	first_date date,
	end_date date,
	company_id integer,
	type character varying)
    RETURNS TABLE(fecha_emi date, fecha_ven date, cuenta character varying, divisa character varying, tdp character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, saldo_mn numeric, saldo_me numeric, partner_id integer, move_line_id integer, cero_treinta numeric, treinta1_sesenta numeric, sesenta1_noventa numeric, noventa1_ciento20 numeric, ciento21_ciento50 numeric, ciento51_ciento80 numeric, ciento81_mas numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
	select 
	b1.fecha_emi,
	b1.fecha_ven,
	b1.cuenta,
	b1.divisa,
	b1.tdp,
	b1.doc_partner,
	b1.partner,
	b1.td_sunat,
	b1.nro_comprobante,
	b1.saldo_mn,
	b1.saldo_me,
	b1.partner_id,
	b1.move_line_id,
	case when b1.atraso between 1 and 30 then b1.saldo_mn else 0 end as cero_treinta,
	case when b1.atraso between 31 and 60 then b1.saldo_mn else 0 end as treinta1_sesenta,
	case when b1.atraso between 61 and 90 then b1.saldo_mn else 0 end as sesenta1_noventa,
	case when b1.atraso between 91 and 120 then b1.saldo_mn else 0 end as noventa1_ciento20,
	case when b1.atraso between 121 and 150 then b1.saldo_mn else 0 end as ciento21_ciento50,
	case when b1.atraso between 151 and 180 then b1.saldo_mn else 0 end as ciento51_ciento80,
	case when b1.atraso >180 then b1.saldo_mn else 0 end as ciento81_mas 
	from
	(
	select 
	case when a1.fecha_doc::date is null then a1.fecha_con::date else a1.fecha_doc::date end as fecha_emi,
	a1.fecha_ven as fecha_ven,
	a1.cuenta as cuenta,
	case when a3.name is not null then a3.name else 'PEN' end as divisa,
	a1.td_partner as tdp,
	a1.doc_partner as doc_partner,
	a1.partner,
	a1.td_sunat,
	a1.nro_comprobante,
	case when  a2.internal_type='receivable' then a1.saldo_mn else -a1.saldo_mn end as saldo_mn,
	case when  a2.internal_type='receivable' then a1.saldo_me else -a1.saldo_me end as saldo_me,
	case when a1.fecha_ven is not null then $2 - a1.fecha_ven else 0 end as atraso,
	a1.account_id,
	a2.internal_type,
	a1.partner_id,
	a1.move_line_id
	from 
	get_saldos($1,$2,$3,1) a1
	left join account_account a2 on a2.id=a1.account_id
	left join res_currency a3 on a3.id=a2.currency_id
	where a1.nro_comprobante is not null
	)b1
	where b1.internal_type = $4;
END;
$BODY$;
--------------------.....................-----------......-----------maturity_analysis_rep_it----------------------------------------------------------------------
-------------------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_sin_cierre(date, date, integer) CASCADE;
CREATE OR REPLACE FUNCTION public.get_saldos_sin_cierre(
    IN date_ini date,
    IN date_fin date,
    IN id_company integer)
  RETURNS TABLE(id bigint, periodo text, fecha_con date, libro character varying, voucher character varying, td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, fecha_ven date, cuenta character varying, moneda character varying, debe numeric, haber numeric, saldo_mn numeric, saldo_me numeric,aml_ids integer[], journal_id integer, account_id integer, partner_id integer, move_id integer, move_line_id integer, company_id integer) AS
$BODY$
BEGIN
	RETURN QUERY
	SELECT row_number() OVER () AS id,t.*
		FROM ( select 
	b2.periodo,
	coalesce(b2.fecha::date, b3.fecha_contable::date) as fecha_con,
	b2.libro, 
	b2.voucher, 
	b2.td_partner, 
	b2.doc_partner, 
	b2.partner, 
	b2.td_sunat,
	b2.nro_comprobante, 
	coalesce(b2.fecha_doc::date,b3.fecha_emision::date) as fecha_doc,
	coalesce(b2.fecha_ven::date,b3.fecha_vencimiento::date) as fecha_ven,
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
	select aml.partner_id, aml.account_id, ei.code as td_sunat, aml.nro_comp as nro_comprobante,
	sum(aml.debit) as sum_debe, sum(aml.credit) as sum_haber, sum(aml.balance) as sum_balance, 
	sum(aml.amount_currency) as sum_importe_me, min(aml.id) as min_line_id,
	array_agg(aml.id) as aml_ids
	from account_move_line aml
	inner join account_move am on am.id = aml.move_id
	left join account_account a2 on a2.id = aml.account_id
	LEFT JOIN einvoice_catalog_01 ei ON ei.id = aml.type_document_id
	where (a2.is_document_an = True) and am.state::text = 'posted'::text AND aml.display_type IS NULL AND aml.account_id IS NOT NULL AND (am.date::date BETWEEN $1 and $2) AND am.company_id = $3
	and (am.is_opening_close<>TRUE or (am.is_opening_close = TRUE AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text))
	group by aml.partner_id, aml.account_id, ei.code, aml.nro_comp
	)b1
	left join vst_diariog  b2 on b2.move_line_id = b1.min_line_id
	left join (select a1.account_id, a1.partner_id, ei.code as td_sunat,a1.nro_comp,
	min(a2.date) as fecha_contable,
	min(a2.invoice_date) as fecha_emision,
	min(a1.date_maturity) as fecha_vencimiento
	from account_move_line a1
	left join account_move a2 on a2.id=a1.move_id
	left join account_account a3 on a3.id=a1.account_id
	left join res_currency rc on rc.id = a1.currency_id
	LEFT JOIN einvoice_catalog_01 ei ON ei.id = a1.type_document_id
	where a2.type in ('out_receipt','in_receipt','out_invoice','in_invoice','out_refund','in_refund') and
	a3.internal_type in ('payable','receivable') and a2.state='posted' and a1.company_id=$3
	group by  a1.account_id, a1.partner_id, ei.code,a1.nro_comp
	)b3 on (b3.account_id=b1.account_id and b3.partner_id=b1.partner_id and b3.td_sunat=b1.td_sunat and b3.nro_comp=b1.nro_comprobante)
	order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc)t;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;