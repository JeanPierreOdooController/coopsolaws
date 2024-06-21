DROP FUNCTION IF EXISTS public.get_destinos_range(text,text,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_destinos_range(
    IN var_periodo_from text,
    IN var_periodo_to text,
    IN var_company_id integer)
  RETURNS TABLE(periodo text, fecha date, libro character varying, voucher character varying, cuenta character varying, debe numeric, haber numeric, balance numeric, cta_analitica character varying, des_debe character varying, des_haber character varying, am_id integer, aml_id integer, company_id integer) AS
$BODY$
BEGIN
RETURN QUERY 
SELECT vst_d.periodo, vst_d.fecha::date as fecha, 
vst_d.libro, vst_d.voucher, vst_d.cuenta, vst_d.debe,
vst_d.haber, vst_d.balance, vst_d.cta_analitica, vst_d.des_debe,
vst_d.des_haber, vst_d.am_id,
vst_d.aml_id, vst_d.company_id FROM vst_destinos vst_d where (vst_d.periodo::integer between $1::integer and $2::integer) and vst_d.company_id = $3;
END;
$BODY$
LANGUAGE plpgsql VOLATILE
COST 100
ROWS 1000;