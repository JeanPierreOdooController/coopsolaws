DROP FUNCTION IF EXISTS public.get_distinto_tc_apertura(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_distinto_tc_apertura(
	  date_from date,
    date_to date,
	  company_id integer)
    RETURNS TABLE(account_id integer, partner_id integer, type_document_id integer, nro_comp character varying, min integer, 
debe numeric, haber numeric, saldo_mn numeric, saldo_me numeric) AS
    $BODY$
    BEGIN
    RETURN QUERY 
select a.account_id,a.partner_id,a.type_document_id,a.nro_comp,min(a.id) as min,
sum(a.debit) as debe,
sum(a.credit) as haber,
sum(a.debit-a.credit) as saldo_mn,
sum(a.amount_currency) as saldo_me from account_move_line a
left join account_move b on b.id=a.move_id
left join account_account c on c.id=a.account_id
left join account_account_type d on d.id=c.user_type_id
left join res_currency e on e.id=c.currency_id
where d.type in ('receivable','payable')  and
e.name='USD' and
(b.date between $1 and $2) and b.company_id = $3
and a.account_id is not null and a.partner_id is not null and a.type_document_id is not null and a.nro_comp is not null 
group by a.account_id,a.partner_id,a.type_document_id,a.nro_comp
having sum(a.amount_currency)=0 and sum(a.debit-a.credit)<>0;
END;
    $BODY$
    LANGUAGE plpgsql VOLATILE
    COST 100
    ROWS 1000;