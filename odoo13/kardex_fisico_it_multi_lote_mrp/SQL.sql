CREATE OR REPLACE FUNCTION vst_kardex_fisico_lote (IN company integer) 
  RETURNS TABLE (
    product_uom integer, 
    price_unit double precision, 
    product_qty numeric, 
    location_id integer, 
    location_dest_id integer, 
    picking_type_id integer, 
    product_id integer, 
    picking_id integer, 
    invoice_id integer, 
    date timestamp without time zone, 
    name character varying, 
    partner_id integer, 
    guia text, 
    analitic_id text, 
    id integer, 
    default_code character varying, 
    estado character varying,
    u_origen varchar,
    usage_origen varchar,
    u_destino varchar,
    usage_destino varchar,
    categoria varchar,
    categoria_id integer,
    producto varchar,
    cod_pro varchar,
    unidad varchar,
    lote varchar
) 
AS $$
BEGIN
    IF EXISTS(SELECT *
                   FROM information_schema.tables
                   WHERE table_schema = current_schema()
                         AND table_name = 'vst_mrp_kardex') THEN
                        RETURN QUERY 
      SELECT 
      vst_kardex_fisico1.product_uom , 
    vst_kardex_fisico1.price_unit , 
    vst_kardex_fisico1.product_qty , 
    vst_kardex_fisico1.location_id , 
    vst_kardex_fisico1.location_dest_id , 
    vst_kardex_fisico1.picking_type_id , 
    vst_kardex_fisico1.product_id , 
    vst_kardex_fisico1.picking_id , 
    vst_kardex_fisico1.invoice_id , 
    vst_kardex_fisico1.date , 
    vst_kardex_fisico1.name , 
    vst_kardex_fisico1.partner_id , 
    vst_kardex_fisico1.guia , 
    vst_kardex_fisico1.analitic_id , 
    vst_kardex_fisico1.id , 
    vst_kardex_fisico1.default_code , 
    vst_kardex_fisico1.estado ,
    vst_kardex_fisico1.u_origen ,
    vst_kardex_fisico1.usage_origen ,
    vst_kardex_fisico1.u_destino ,
    vst_kardex_fisico1.usage_destino ,
    vst_kardex_fisico1.categoria ,
    vst_kardex_fisico1.categoria_id ,
    vst_kardex_fisico1.producto ,
    vst_kardex_fisico1.cod_pro ,
    vst_kardex_fisico1.unidad,
    vst_kardex_fisico1.lote  FROM vst_kardex_fisico1_lote as vst_kardex_fisico1
    inner join stock_move sm on sm.id = vst_kardex_fisico1.id
    where sm.company_id = $1

    ;
    ELSE
      RETURN QUERY 
      SELECT 
      vst_kardex_fisico1.product_uom , 
    vst_kardex_fisico1.price_unit , 
    vst_kardex_fisico1.product_qty , 
    vst_kardex_fisico1.location_id , 
    vst_kardex_fisico1.location_dest_id , 
    vst_kardex_fisico1.picking_type_id , 
    vst_kardex_fisico1.product_id , 
    vst_kardex_fisico1.picking_id , 
    vst_kardex_fisico1.invoice_id , 
    vst_kardex_fisico1.date , 
    vst_kardex_fisico1.name , 
    vst_kardex_fisico1.partner_id , 
    vst_kardex_fisico1.guia , 
    vst_kardex_fisico1.analitic_id , 
    vst_kardex_fisico1.id , 
    vst_kardex_fisico1.default_code , 
    vst_kardex_fisico1.estado ,
    vst_kardex_fisico1.u_origen ,
    vst_kardex_fisico1.usage_origen ,
    vst_kardex_fisico1.u_destino ,
    vst_kardex_fisico1.usage_destino ,
    vst_kardex_fisico1.categoria ,
    vst_kardex_fisico1.categoria_id ,
    vst_kardex_fisico1.producto ,
    vst_kardex_fisico1.cod_pro ,
    vst_kardex_fisico1.unidad,
    vst_kardex_fisico1.lote  FROM vst_kardex_fisico1_lote as vst_kardex_fisico1
    inner join stock_move sm on sm.id = vst_kardex_fisico1.id
    where sm.company_id = $1;
    END IF;
END; $$ 

LANGUAGE 'plpgsql';






CREATE OR REPLACE VIEW public.vst_kardex_fisico1_lote AS 
 SELECT stock_move.product_uom,
        CASE
            WHEN sl.usage::text = 'supplier'::text THEN 0::double precision
            ELSE
            CASE
                WHEN uom_uom.id <> uomt.id THEN round((stock_move.price_unit_it::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
                ELSE stock_move.price_unit_it::double precision
            END
        END AS price_unit,
        CASE
            WHEN uom_uom.id <> uomt.id THEN round((sml.qty_done::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
            ELSE sml.qty_done
        END AS product_qty,
    sml.location_id,
    sml.location_dest_id,
    stock_move.picking_type_id,
    stock_move.product_id,
    stock_move.picking_id,
    stock_picking.invoice_id,
        CASE
            WHEN stock_picking.use_kardex_date THEN stock_picking.kardex_date
            ELSE COALESCE(invoice.invoice_date::timestamp without time zone, stock_picking.kardex_date)
        END AS date,
    stock_picking.name,
    stock_picking.partner_id,
        CASE
            WHEN tok.id IS NOT NULL THEN (tok.code::text || '-'::text) || tok.name::text
            ELSE ''::text
        END AS guia,
    aaait.name::text AS analitic_id,
    stock_move.id,
    product_product.default_code,
    stock_move.state AS estado,
    l_o.complete_name AS u_origen,
    l_o.usage AS usage_origen,
    l_d.complete_name AS u_destino,
    l_d.usage AS usage_destino,
    pc.name AS categoria,
    pc.id AS categoria_id,
    pname.new_name AS producto,
    product_product.default_code AS cod_pro,
    uomt.name AS unidad,
    spl.name as lote
   FROM stock_move
    JOIN stock_move_line sml on sml.move_id = stock_move.id
    left join stock_production_lot spl on spl.id = sml.lot_id
     JOIN uom_uom ON stock_move.product_uom = uom_uom.id
     JOIN stock_location l_o ON l_o.id = sml.location_id
     JOIN stock_location l_d ON l_d.id = sml.location_dest_id
     JOIN stock_picking ON stock_move.picking_id = stock_picking.id
     LEFT JOIN account_move invoice ON invoice.id = stock_picking.invoice_id
     JOIN stock_picking_type ON stock_picking.picking_type_id = stock_picking_type.id
     JOIN stock_location sl ON sl.id = sml.location_dest_id
     JOIN product_product ON stock_move.product_id = product_product.id
     LEFT JOIN ( SELECT t_pp.id,
            ((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
           FROM product_product t_pp
             JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
             left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
             LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
             LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
             LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
          GROUP BY t_pp.id) pname ON pname.id = product_product.id
     JOIN product_template ON product_product.product_tmpl_id = product_template.id
     LEFT JOIN ir_translation it ON product_template.id = it.res_id AND it.name::text = 'product.template,name'::text AND it.lang::text = 'es_PE'::text AND it.state::text = 'translated'::text
     JOIN product_category pc ON pc.id = product_template.categ_id
     JOIN uom_uom uomt ON uomt.id = product_template.uom_id
     JOIN uom_uom original ON original.id = product_template.uom_id
     left join account_analytic_account aaait on aaait.id = stock_move.analytic_account_id
     LEFT JOIN type_operation_kardex tok ON stock_picking.type_operation_sunat_id = tok.id
  WHERE (stock_move.state::text = ANY (ARRAY['done'::text, 'assigned'::text])) AND product_template.type::text = 'product'::text AND stock_move.picking_id IS NOT NULL 
 union all

select 
sm.product_uom,

        CASE
                WHEN uom_uom.id <> uomt.id THEN round((sm.price_unit_it::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
                ELSE sm.price_unit_it::double precision
            
        END AS price_unit,
        CASE
            WHEN uom_uom.id <> uomt.id THEN round((sml.qty_done::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
            ELSE sml.qty_done
        END AS product_qty,
        sls.id as location_id,
        sld.id as location_dest_id,
        sm.picking_type_id,
        sm.product_id,
        null::integer as picking_id,
        null::integer as invoice_id,
        sm.date as date,
        sm.name as name,
        null::integer as partner_id,
        ''::text as guia,
        aaait.name::text as analitic_id,
        sm.id,
        pp.default_code,
        sm.state as estado,
        sls.complete_name as u_origen,
        sls.usage as usage_origen,
        sld.complete_name as u_destino,
        sld.usage as usage_destino,
        pc.name as categoria,
        pc.id as categoria_id,
        pname.new_name AS producto,
        pp.default_code as cod_pro,
        uomt.name as unidad,
    spl.name as lote

from stock_move sm 
     JOIN uom_uom ON sm.product_uom = uom_uom.id
inner join stock_move_line sml on sml.move_id = sm.id
    left join stock_production_lot spl on spl.id = sml.lot_id

inner join product_product pp on pp.id = sml.product_id
     LEFT JOIN ( SELECT t_pp.id,
            ((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
           FROM product_product t_pp
             JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
             left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
             LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
             LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
             LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
          GROUP BY t_pp.id) pname ON pname.id = pp.id
inner join product_template pt on pt.id = pp.product_tmpl_id
left join ir_translation it on pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
inner join product_category pc on pc.id = pt.categ_id
inner join uom_uom uomt on uomt.id = pt.uom_id
     left join account_analytic_account aaait on aaait.id = sm.analytic_account_id
inner join stock_location sls on sls.id = sml.location_id
inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done' and sm.picking_type_id is null and sm.picking_id is null and sm.production_id is null and sm.raw_material_production_id is null

 union all

select 
sm.product_uom,

        CASE
                WHEN uom_uom.id <> uomt.id THEN round((sm.price_unit_it::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
                ELSE sm.price_unit_it::double precision
            
        END AS price_unit,
        CASE
            WHEN uom_uom.id <> uomt.id THEN round((sml.qty_done::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
            ELSE sml.qty_done
        END AS product_qty,
        sls.id as location_id,
        sld.id as location_dest_id,
        sm.picking_type_id,
        sm.product_id,
        null::integer as picking_id,
        null::integer as invoice_id,
        mp.kardex_date as date,
        mp.name as name,
        null::integer as partner_id,
        ''::text as guia,
        aaait.name::text as analitic_id,
        sm.id,
        pp.default_code,
        sm.state as estado,
        sls.complete_name as u_origen,
        sls.usage as usage_origen,
        sld.complete_name as u_destino,
        sld.usage as usage_destino,
        pc.name as categoria,
        pc.id as categoria_id,
    pname.new_name AS producto,
        pp.default_code as cod_pro,
        uomt.name as unidad,
        spl.name as lote
from mrp_production mp
inner join stock_move sm on sm.production_id = mp.id  or sm.raw_material_production_id = mp.id
     JOIN uom_uom ON sm.product_uom = uom_uom.id
inner join stock_move_line sml on sml.move_id = sm.id

    left join stock_production_lot spl on spl.id = sml.lot_id
inner join product_product pp on pp.id = sml.product_id
     LEFT JOIN ( SELECT t_pp.id,
            ((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
           FROM product_product t_pp
             JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
             left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
             LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
             LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
             LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
          GROUP BY t_pp.id) pname ON pname.id = pp.id
inner join product_template pt on pt.id = pp.product_tmpl_id
left join ir_translation it on pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
inner join product_category pc on pc.id = pt.categ_id
inner join uom_uom uomt on uomt.id = pt.uom_id
     left join account_analytic_account aaait on aaait.id = sm.analytic_account_id
inner join stock_location sls on sls.id = sml.location_id
inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done'
;
