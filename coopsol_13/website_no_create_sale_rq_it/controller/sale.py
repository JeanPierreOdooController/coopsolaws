from odoo.http import Controller
from odoo.http import request
from odoo import fields, http, SUPERUSER_ID, tools, _

from odoo.addons.website_sale.controllers.main import WebsiteSale


class MyWebsiteSale(WebsiteSale):

    def _get_products_recently_viewed(self):
        if not request.env.user.id or request.env.user.name == 'Public user for PROFESSIONAL CLEANING S.A.':
            return request.redirect("/web/login")
        return super(MyWebsiteSale, self)._get_products_recently_viewed()

    @http.route(['/shop/cart'], type='http', auth="public", website=True, sitemap=False)
    def cart(self, access_token=None, revive='', **post):
        if not request.env.user.id or request.env.user.name == 'Public user for PROFESSIONAL CLEANING S.A.':
            return request.redirect("/web/login")
        if access_token and revive:
            return super(MyWebsiteSale, self).cart(access_token, revive, **post)
        elif not access_token and revive:
            return super(MyWebsiteSale, self).cart(revive, **post)
        elif access_token and not revive:
            return super(MyWebsiteSale, self).cart(access_token, **post)
        else:
            return super(MyWebsiteSale, self).cart(**post)

    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['GET', 'POST'], website=True, csrf=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        if not request.env.user.id or request.env.user.name == 'Public user for PROFESSIONAL CLEANING S.A.':
            return request.redirect("/web/login")
        return super(MyWebsiteSale, self).cart_update(product_id, add_qty, set_qty, **kw)
