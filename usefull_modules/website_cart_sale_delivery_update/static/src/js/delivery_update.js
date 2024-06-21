odoo.define('website_cart_sale_delivery_update.cart_sale_delivery_update', function(require) {
    'use strict';
    
    var core = require('web.core');
    var publicWidget = require('web.public.widget');
    var _t = core._t;
    var concurrency = require('web.concurrency');
    var dp = new concurrency.DropPrevious();
    var ajax = require('web.ajax');
    

    publicWidget.registry.websiteSaleDelivery = publicWidget.Widget.extend({
        selector: '.oe_website_sale',
        events: {
            'change select[name="shipping_id"]': '_onSetAddress',
            'click #delivery_carrier .o_delivery_carrier_select ' : '_onCarrierClick',
            'click input[name="delivery_type"]':'ShowDetails',
        },
    
        /**
         * @override
         */
        start: function () {

            console.log("INICIALIZANDO EL WIDGET");

            var self = this;
            var $carriers = $('#delivery_carrier input[name="delivery_type"]');
            var $payButton = $('#o_payment_form_pay');
    
            // Workaround to:
            // - update the amount/error on the label at first rendering
            // - prevent clicking on 'Pay Now' if the shipper rating fails
            console.log("$carriers.length > 0  ->", $carriers.length ," > 0")
            if ($carriers.length > 0) {
                if ($carriers.filter(':checked').length === 0) {
                    $payButton.prop('disabled', true);
                    var disabledReasons = $payButton.data('disabled_reasons') || {};
                    disabledReasons.carrier_selection = true;
                    $payButton.data('disabled_reasons', disabledReasons);
                }
                $carriers.filter(':checked').click();
            }
    
            // Asincronamente actualizar el precio de los envios
            _.each($carriers, function (carrierInput, k) {
                self._showLoading($(carrierInput));

                var url = '/shop/carrier_rate_shipment';
                var parameters={
                    'carrier_id': carrierInput.value
                };
                ajax.jsonRpc(url, 'call', parameters).then((result)=>{
                    // Manejar el resultado de la llamada a la URL
                    console.log(result);
                    console.log("_handleCarrierUpdateResultBadge");
                    var $carrierBadge = $('#delivery_carrier input[name="delivery_type"][value=' + result.carrier_id + '] ~ .o_wsale_delivery_badge_price');
            
                    if (result.status === true) {
                        // if free delivery (`free_over` field), show 'Free', not '$0'
                        if (result.is_free_delivery) {
                            $carrierBadge.text(_t('Free'));
                        } else {
                            $carrierBadge.html(result.new_amount_delivery);
                        }
                        $carrierBadge.removeClass('o_wsale_delivery_carrier_error');
                    } else {
                        $carrierBadge.addClass('o_wsale_delivery_carrier_error');
                        $carrierBadge.text(result.error_message);
                    }

                });

            });
            // Cada vez que una clase o_delivery_carrier_select sea escogida
            var selects = document.querySelectorAll('.o_delivery_carrier_select');
            selects.forEach((select) => {
                select.addEventListener('click',(ev)=>{

                    var $radio = $(ev.currentTarget).find('input[type="radio"]');
                    this._showLoading($radio);
                    console.log($radio)
                    console.log($radio[0].value)
                    $radio.prop("checked", true);
                    var $payButton = $('#o_payment_form_pay');
                    $payButton.prop('disabled', true);
                    var disabledReasons = $payButton.data('disabled_reasons') || {};
                    disabledReasons.carrier_selection = true;
                    $payButton.data('disabled_reasons', disabledReasons);

                    var url = '/shop/update_carrier';
                    var parameters={
                        'carrier_id': $radio[0].value
                    };
                    console.log("--------------------------------------------")
                    dp.add(
                        ajax.jsonRpc(url, 'call', parameters)
                        .then((result)=>{
                            console.log("result ",result);
                            return result;
                        })
                    ).then((result)=>{
                        console.log("_handleCarrierUpdateResult");
                        this._handleCarrierUpdateResultBadge(result);
                        var $payButton = $('#o_payment_form_pay');
                        var $amountDelivery = $('#order_delivery .monetary_field');
                        var $amountUntaxed = $('#order_total_untaxed .monetary_field');
                        var $amountTax = $('#order_total_taxes .monetary_field');
                        var $amountTotal = $('#order_total .monetary_field, #amount_total_summary.monetary_field');
                
                        if (result.status === true) {
                            $amountDelivery.html(result.new_amount_delivery);
                            $amountUntaxed.html(result.new_amount_untaxed);
                            $amountTax.html(result.new_amount_tax);
                            $amountTotal.html(result.new_amount_total);
                            var disabledReasons = $payButton.data('disabled_reasons') || {};
                            disabledReasons.carrier_selection = false;
                            $payButton.data('disabled_reasons', disabledReasons);
                            $payButton.prop('disabled', _.contains($payButton.data('disabled_reasons'), true));
                        } else {
                            $amountDelivery.html(result.new_amount_delivery);
                            $amountUntaxed.html(result.new_amount_untaxed);
                            $amountTax.html(result.new_amount_tax);
                            $amountTotal.html(result.new_amount_total);
                        }
                    })
                    console.log("--------------------------------------------");
                });
            });
            return this._super.apply(this, arguments);
        },
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------
    
        /**
         * @private
         * @param {jQuery} $carrierInput
         */
        _showLoading: function ($carrierInput) {
            $carrierInput.siblings('.o_wsale_delivery_badge_price').html('<span class="fa fa-spinner fa-spin"/>');
        },
        /**
         * @private
         * @param {Object} result
         */
        _handleCarrierUpdateResult: function (result) {
            console.log("_handleCarrierUpdateResult");
            this._handleCarrierUpdateResultBadge(result);
            var $payButton = $('#o_payment_form_pay');
            var $amountDelivery = $('#order_delivery .monetary_field');
            var $amountUntaxed = $('#order_total_untaxed .monetary_field');
            var $amountTax = $('#order_total_taxes .monetary_field');
            var $amountTotal = $('#order_total .monetary_field, #amount_total_summary.monetary_field');
    
            if (result.status === true) {
                $amountDelivery.html(result.new_amount_delivery);
                $amountUntaxed.html(result.new_amount_untaxed);
                $amountTax.html(result.new_amount_tax);
                $amountTotal.html(result.new_amount_total);
                var disabledReasons = $payButton.data('disabled_reasons') || {};
                disabledReasons.carrier_selection = false;
                $payButton.data('disabled_reasons', disabledReasons);
                $payButton.prop('disabled', _.contains($payButton.data('disabled_reasons'), true));
            } else {
                $amountDelivery.html(result.new_amount_delivery);
                $amountUntaxed.html(result.new_amount_untaxed);
                $amountTax.html(result.new_amount_tax);
                $amountTotal.html(result.new_amount_total);
            }
        },
        /**
         * @private
         * @param {Object} result
         */
        _handleCarrierUpdateResultBadge: function (result) {
            console.log("_handleCarrierUpdateResultBadge");
            var $carrierBadge = $('#delivery_carrier input[name="delivery_type"][value=' + result.carrier_id + '] ~ .o_wsale_delivery_badge_price');
    
            if (result.status === true) {
                 // if free delivery (`free_over` field), show 'Free', not '$0'
                 if (result.is_free_delivery) {
                     $carrierBadge.text(_t('Free'));
                 } else {
                     $carrierBadge.html(result.new_amount_delivery);
                 }
                 $carrierBadge.removeClass('o_wsale_delivery_carrier_error');
            } else {
                $carrierBadge.addClass('o_wsale_delivery_carrier_error');
                $carrierBadge.text(result.error_message);
            }
        },
    
        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------
        /**
         * @private
         * @param {Event} ev
         */
        _onSetAddress: function (ev) {
            var value = $(ev.currentTarget).val();
            var $providerFree = $('select[name="country_id"]:not(.o_provider_restricted), select[name="state_id"]:not(.o_provider_restricted)');
            var $providerRestricted = $('select[name="country_id"].o_provider_restricted, select[name="state_id"].o_provider_restricted');
            if (value === 0) {
                // Ship to the same address : only show shipping countries available for billing
                $providerFree.hide().attr('disabled', true);
                $providerRestricted.show().attr('disabled', false).change();
            } else {
                // Create a new address : show all countries available for billing
                $providerFree.show().attr('disabled', false).change();
                $providerRestricted.hide().attr('disabled', true);
            }
        },
    });
    var PublicWidgetMyAccountExtend = new publicWidget.registry.websiteSaleDelivery(this);
    PublicWidgetMyAccountExtend.appendTo($(".oe_website_sale"));
    return publicWidget.registry.websiteSaleDelivery;
});