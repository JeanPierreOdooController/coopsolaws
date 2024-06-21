DROP FUNCTION IF EXISTS public.get_bc_register(character varying,character varying, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_bc_register(
    IN period_from character varying,
    IN period_to character varying,
    IN company integer)
  RETURNS TABLE(mayor text, cuenta character varying, nomenclatura text, 
                debe numeric(64,2), haber numeric(64,2), saldo_deudor numeric(64,2), 
                saldo_acreedor numeric(64,2), rubro text) AS
$BODY$
BEGIN

RETURN QUERY 
	select  
	substring(aa.code,0,3) as mayor,
	aa.code as cuenta,
	min(aa.name) as nomenclatura,
	sum(aml.debit) as debe,
	sum(aml.credit) as haber,
	case 
		when sum(aml.debit) > sum(aml.credit)
		then sum(aml.debit) - sum(aml.credit)
		else 0
	end as saldo_deudor,
	case
		when sum(aml.credit) > sum(aml.debit)
		then sum(aml.credit) - sum(aml.debit)
		else 0
	end as saldo_acreedor,
	min(ati.name) as rubro
	from account_move_line aml
	left join account_move am on am.id=aml.move_id
	left join account_account aa on aa.id=aml.account_id
	left join account_type_it ati on ati.id = aa.account_type_it_id
	where aml.company_id=$3 and (CASE
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text
			ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)
		END::integer between $1::integer and $2::integer) and am.state = 'posted' AND aml.display_type IS NULL
	group by aa.code;
                  
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

------------------------------------------account_bc_report---------------------------------------------------------------

------------------------------------------account_efective_rep_it---------------------------------------------------------------


DROP FUNCTION IF EXISTS public.get_efective_flow(character varying,character varying,character varying, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_efective_flow(
	periodo_ini character varying,
	periodo_fin character varying,
	period_saldo_inicial character varying,
	company integer)
    RETURNS TABLE(name character varying, efective_group character varying, total numeric, efective_order integer) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN

RETURN QUERY

SELECT T.* FROM (SELECT aet.name, aet.group as efective_group, SUM(aml.balance)*-1 as total, aet.order as efective_order FROM account_move_line aml
LEFT JOIN account_account aa ON aa.id = aml.account_id
LEFT JOIN account_efective_type aet ON aet.id = aa.account_type_cash_id
WHERE LEFT(aa.code,2) <> '10' AND aa.account_type_cash_id IS NOT NULL AND aml.move_id in (
SELECT
DISTINCT ON (aml.move_id) move_id
FROM account_move_line aml
LEFT JOIN account_account aa ON aa.id = aml.account_id
LEFT JOIN account_move am ON am.id = aml.move_id
WHERE am.state = 'posted' AND am.company_id = $4 AND aml.display_type IS NULL AND am.is_opening_close <> TRUE
AND (am.date BETWEEN $1::date AND $2::date)
AND LEFT(aa.code,2) = '10')
GROUP BY aet.name, aet.group, aet.order

UNION ALL

SELECT 'Saldo EFECT y EQUIV de EFECT al inicio del Ejercicio' as name, 'E7' as efective_group, SUM(aml.balance) as total, -1 as efective_order FROM account_move_line aml
LEFT JOIN account_account aa ON aa.id = aml.account_id
LEFT JOIN account_move am ON am.id = aml.move_id
LEFT JOIN account_efective_type aet ON aet.id = aa.account_type_cash_id
WHERE LEFT(aa.code,2) = '10' AND am.state = 'posted' AND aml.company_id = $4 AND aml.display_type IS NULL
AND (CASE
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text
		ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)
	END = $3)
				)T
ORDER BY T.efective_order;

END;
$BODY$;

-------------------------------------------------account_efective_rep_it------------------------------------------------------------------

-------------------------------------------------account_htf1_report------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_f1_register(character varying,character varying,integer,character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_f1_register(
    IN period_from character varying,
    IN period_to character varying,
    IN company integer,
	IN currency character varying)
  RETURNS TABLE(account_id integer, mayor text, cuenta character varying, nomenclatura character varying, debe numeric, haber numeric, saldo_deudor numeric, saldo_acreedor numeric, activo numeric, pasivo numeric, perdinat numeric, ganannat numeric, perdifun numeric, gananfun numeric, rubro character varying) AS
$BODY$
BEGIN

RETURN QUERY 
    
	select T.account_id, left(aa.code,2) as mayor,aa.code as cuenta,aa.name as nomenclatura,T.debe,T.haber,
		   T.saldo_deudor,T.saldo_acreedor,
	case 
		when T.saldo_deudor > 0 and aa.clasification_sheet = '0'
		then T.saldo_deudor
		else 0
	end as activo,
	case 
		when T.saldo_acreedor > 0 and aa.clasification_sheet = '0'
		then T.saldo_acreedor
		else 0
	end as pasivo,
	case 
		when (T.saldo_deudor > 0 and aa.clasification_sheet = '1') or 
			 (T.saldo_deudor > 0 and aa.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdinat,
	case 
		when (T.saldo_acreedor > 0 and aa.clasification_sheet = '1') or
			 (T.saldo_acreedor > 0 and aa.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as ganannat,
	case 
		when (T.saldo_deudor > 0 and aa.clasification_sheet = '2') or
			 (T.saldo_deudor > 0 and aa.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdifun,
	case 
		when (T.saldo_acreedor > 0 and aa.clasification_sheet = '2') or
			 (T.saldo_acreedor > 0 and aa.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as gananfun,
	ati.name as rubro
	from(select
		aml.account_id,
		sum(aml.debit) as debe,
		sum(aml.credit) as haber,
		case 
			when (sum(aml.debit)) > (sum(aml.credit))
			then (sum(aml.debit)) - (sum(aml.credit))
			else 0
		end as saldo_deudor,
		case
			when (sum(aml.credit)) > (sum(aml.debit))
			then (sum(aml.credit)) - (sum(aml.debit))
			else 0
		end as saldo_acreedor
		from account_move_line aml
		LEFT JOIN account_move am ON am.id = aml.move_id
		where aml.company_id = $3 and 
		(CASE
				WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text
				WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text
				ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)
			END::integer between $1::integer and $2::integer) 
			and am.state = 'posted'
			AND 
			aml.display_type IS NULL
		group by aml.account_id)T
	left join account_account aa on aa.id = T.account_id
	left join account_type_it ati on ati.id = aa.account_type_it_id
	order by left(aa.code,2),aa.code;
                  
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
-------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_f1_balance(character varying,character varying,integer, character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_f1_balance(
    IN period_from character varying,
    IN period_to character varying,
    IN company integer,
	IN currency character varying)
  RETURNS TABLE(mayor text, nomenclatura character varying, debe numeric, haber numeric, saldo_deudor numeric, saldo_acreedor numeric, activo numeric, pasivo numeric, perdinat numeric, ganannat numeric, perdifun numeric, gananfun numeric) AS
$BODY$
BEGIN

RETURN QUERY 
    
	select T.mayor,T.name,T.debe,T.haber,
		   T.saldo_deudor,T.saldo_acreedor,
	case 
		when T.saldo_deudor > 0 and ag.clasification_sheet = '0'
		then T.saldo_deudor
		else 0
	end as activo,
	case 
		when T.saldo_acreedor > 0 and ag.clasification_sheet = '0'
		then T.saldo_acreedor
		else 0
	end as pasivo,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '1') or 
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdinat,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '1') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as ganannat,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdifun,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as gananfun
	from(
		select
		f1r.mayor,
		ag.name,
		ag.id,
		sum(f1r.debe) as debe,
		sum(f1r.haber) as haber,
		case 
			when sum(f1r.debe) > sum(f1r.haber) 
			then sum(f1r.debe) - sum(f1r.haber)
			else 0
		end as saldo_deudor,
		case
			when sum(f1r.haber) > sum(f1r.debe)
			then sum(f1r.haber) - sum(f1r.debe)
			else 0
		end as saldo_acreedor
		from get_f1_register($1,$2,$3,$4) f1r
		left join account_group ag on ag.code_prefix = f1r.mayor
    	group by f1r.mayor,ag.name,ag.id)T
	inner join account_group ag on ag.id = T.id
	order by T.mayor;
                  
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

-------------------------------------------------account_htf1_report------------------------------------------------------------------

-------------------------------------------------account_htf2_report------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_f2_register(character varying,integer,character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_f2_register(
	IN period character varying,
	IN company integer,
	IN currency character varying)
    RETURNS TABLE(mayor text, cuenta character varying, nomenclatura character varying, debe_inicial numeric, haber_inicial numeric, debe numeric, haber numeric, saldo_deudor numeric, saldo_acreedor numeric, activo numeric, pasivo numeric, perdinat numeric, ganannat numeric, perdifun numeric, gananfun numeric, rubro character varying) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
    
AS $BODY$
BEGIN
RETURN QUERY 
	select 
		left(cta.code,2) as mayor,
		cta.code as cuenta,
		cta.name as nomenclatura,
		t.debeini as debe_inicial,
		t.haberini as haber_inicial,
		t.debep as debe,
		t.haberp as haber,
		t.saldo_deudor,
		t.saldo_acreedor,
			case 
				when t.saldo_deudor > 0 and cta.clasification_sheet = '0'
				then t.saldo_deudor
				else 0.00
			end as activo,
			case 
				when t.saldo_acreedor > 0 and cta.clasification_sheet = '0'
				then t.saldo_acreedor
				else 0.00
			end as pasivo,
			case 
				when (t.saldo_deudor > 0 and cta.clasification_sheet = '1') or 
					 (t.saldo_deudor > 0 and cta.clasification_sheet = '3')
				then t.saldo_deudor
				else 0.00
			end as perdinat,
			case 
				when (t.saldo_acreedor > 0 and cta.clasification_sheet = '1') or
					 (t.saldo_acreedor > 0 and cta.clasification_sheet = '3')
				then t.saldo_acreedor
				else 0.00
			end as ganannat,
			case 
				when (t.saldo_deudor > 0 and cta.clasification_sheet = '2') or
					 (t.saldo_deudor > 0 and cta.clasification_sheet = '3')
				then T.saldo_deudor
				else 0.00
			end as perdifun,
			case 
				when (t.saldo_acreedor > 0 and cta.clasification_sheet = '2') or
					 (t.saldo_acreedor > 0 and cta.clasification_sheet = '3')
				then t.saldo_acreedor
				else 0.00
			end as gananfun,
			tipo.name as rubro
		from 
		(

		select 
		distinct aml.account_id,
		coalesce(saldoini.debeini,0.00) as debeini,
		coalesce(saldoini.haberini,0.00) as haberini,
		coalesce(saldoac.debeac,0.00) as debep,
		coalesce(saldoac.haberac,0.00) as haberp,
		case when 
			coalesce(saldoini.debeini,0.00)+ coalesce(saldoac.debeac,0.00) > coalesce(saldoini.haberini,0.00)+ coalesce(saldoac.haberac,0.00)
		then
			(coalesce(saldoini.debeini,0.00)+ coalesce(saldoac.debeac,0.00)) - (coalesce(saldoini.haberini,0.00)+ coalesce(saldoac.haberac,0.00))
		else	0.00
		end as saldo_deudor,

		case when 
			  coalesce(saldoini.haberini,0.00)+ coalesce(saldoac.haberac,0.00) > coalesce(saldoini.debeini,0.00)+ coalesce(saldoac.debeac,0.00)
		then 
			 ( coalesce(saldoini.haberini,0.00)+ coalesce(saldoac.haberac,0.00)) - (coalesce(saldoini.debeini,0.00)+ coalesce(saldoac.debeac,0.00))
		else 0.00
		end as saldo_acreedor
		from account_move_line aml 
		LEFT JOIN account_move am ON am.id = aml.move_id
		left join 
		-- ACA PONER LOS PARAMETROS PARA COMPAÑIA Y PERIODO INICIAL QUE SERA EL AÑO DEL PERIODO ELEGIDO ( CUATRO DIGITOS PRIMERO) CONCATENADO CON '00'
		(SELECT aml.account_id,
		sum(aml.debit) AS debeini,
		sum(aml.credit) AS haberini
		FROM account_move_line aml
		LEFT JOIN account_move am ON am.id = aml.move_id
		WHERE aml.company_id = $2
		AND (CASE
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text
			ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)
			END::integer = (left($1,4) || '00')::integer) 
			AND am.state = 'posted'
			AND aml.display_type IS NULL
		group by aml.account_id)
		saldoini on saldoini.account_id=aml.account_id
		left join 
		-- ACA PONER LOS PARAMETROS PARA COMPAÑIA Y PERIODO HASTA EL CUAL SE QUIERE ,  SIN CONSIDERAR EL PERIODO INICIAL 
		(SELECT aml.account_id,
		sum(aml.debit) AS debeac,
		sum(aml.credit) AS haberac
		FROM account_move_line aml 
		LEFT JOIN account_move am ON am.id = aml.move_id
		where aml.company_id = $2 AND (CASE
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text
			ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)
			END::integer BETWEEN (left($1,4) || '01')::integer AND $1::integer)
		AND (CASE
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text
			ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)
			END::integer <> (left($1,4) || '00')::integer)
		AND am.state = 'posted'
		AND aml.display_type IS NULL
		group by aml.account_id)
		saldoac on saldoac.account_id=aml.account_id
		-- EN ESTE WHERE VA EL PARAMETRO DE LA COMPAÑIA Y DE LOS PERIODOS INICAL SIEMPRE 00  Y FINAL PORQUE SE NECESITA EL ACUMULADO DE LAS CUENTAS 
		where aml.company_id=$2 and (CASE
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text
			ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)
			END::integer BETWEEN (left($1,4) || '00')::integer AND $1::integer)
			AND am.state = 'posted'
			AND aml.display_type IS NULL
		) t
		left join account_account cta on cta.id=t.account_id                 
		left join account_type_it tipo on tipo.id=cta.account_type_it_id
		order by left(cta.code,2),cta.code;              
END; $BODY$;
-------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_f2_balance(character varying,integer, character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_f2_balance(
	IN period character varying,
	IN company integer,
	IN currency character varying)
    RETURNS TABLE(mayor text, nomenclatura character varying, debe_inicial numeric, haber_inicial numeric, debe numeric, haber numeric, saldo_deudor numeric, saldo_acreedor numeric, activo numeric, pasivo numeric, perdinat numeric, ganannat numeric, perdifun numeric, gananfun numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
    
AS $BODY$
BEGIN

RETURN QUERY 
    
	select T.mayor,T.name,T.debe_inicial,T.haber_inicial,
		   T.debe,T.haber,T.saldo_deudor,T.saldo_acreedor,
	case 
		when T.saldo_deudor > 0 and ag.clasification_sheet = '0'
		then T.saldo_deudor
		else 0
	end as activo,
	case 
		when T.saldo_acreedor > 0 and ag.clasification_sheet = '0'
		then T.saldo_acreedor
		else 0
	end as pasivo,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '1') or 
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdinat,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '1') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as ganannat,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdifun,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as gananfun
	from(
		select
		f2r.mayor,
		ag.name,
		ag.id,
		sum(f2r.debe_inicial) as debe_inicial,
		sum(f2r.haber_inicial) as haber_inicial,
		sum(f2r.debe) as debe,
		sum(f2r.haber) as haber,
		case 
			when sum(f2r.debe) + sum(f2r.debe_inicial) > sum(f2r.haber) + sum(f2r.haber_inicial) 
			then (sum(f2r.debe) + sum(f2r.debe_inicial)) - (sum(f2r.haber) + sum(f2r.haber_inicial))
			else 0
		end as saldo_deudor,
		case
			when sum(f2r.haber) + sum(f2r.haber_inicial) > sum(f2r.debe) + sum(f2r.debe_inicial)
			then (sum(f2r.haber) + sum(f2r.haber_inicial)) - (sum(f2r.debe) + sum(f2r.debe_inicial))
			else 0
		end as saldo_acreedor
		from get_f2_register($1,$2,$3) f2r
		left join account_group ag on ag.code_prefix = f2r.mayor
    	group by f2r.mayor,ag.name,ag.id)T
	inner join account_group ag on ag.id = T.id
	order by T.mayor;
                  
END; $BODY$;

-------------------------------------------------account_htf2_report------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.periodo_de_fecha(
date,boolean)
    RETURNS integer
    LANGUAGE 'sql'
    COST 100
    VOLATILE 
AS $BODY$
 
select 
CASE
	WHEN $2 = true AND to_char($1, 'mmdd'::text) = '0101'::text THEN (to_char($1, 'yyyy'::text) || '00'::text)::integer
	WHEN $2 = true AND to_char($1, 'mmdd'::text) = '1231'::text THEN (to_char($1, 'yyyy'::text) || '13'::text)::integer
	ELSE to_char($1, 'yyyymm'::text)::integer
END AS periodo
 
$BODY$;