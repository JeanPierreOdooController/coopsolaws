odoo.define('ecommerce_select_address_js_it.portal', function(require) {
    "use strict";

    var publicWidget = require('web.public.widget');
    require('portal.portal');

    //funcion para reemplzar al onchange de la ciudad
    publicWidget.registry.portalDetails.include({

    start: function () {
        var def = this._super.apply(this, arguments);
        return def;
    },

    _adaptAddressForm: function () {},


     _onCountryChange: function () {
        if (!$("#country_id").val()) {
            return;
        }
        this._rpc({
            route: "/shop/country_infos/" + $("#country_id").val(),
            params: {
                mode: 'shipping',
            },
        }).then(function (data) {
            // placeholder phone_code
            //$("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+'+ data.phone_code : '');

            // populate states and display
            var selectStates = $("select[name='state_id']");
            // dont reload state at first loading (done in qweb)
            if (selectStates.data('init')===0 || selectStates.find('option').length===1) {
                if (data.states.length) {
                    selectStates.html('');
                    var init_data = $('<option>').attr('value','').text('Departamento ...');
                    selectStates.append(init_data);
                    _.each(data.states, function (x) {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0])
                            .attr('data-code', x[2]);

                        selectStates.append(opt);
                    });
                    selectStates.parent('div').show();
                } else {
                    selectStates.val('').parent('div').hide();
                    $("select[name='province_id']").parent('div').hide();

                    $("select[name='district_id']").parent('div').hide();

                }
                selectStates.data('init', 0);
            } else {
                selectStates.data('init', 0);
            }
            // manage fields order / visibility
            if (data.fields) {
                if ($.inArray('zip', data.fields) > $.inArray('city', data.fields)){
                    $(".div_zip").before($(".div_city"));
                } else {
                    $(".div_zip").after($(".div_city"));
                }
                var all_fields = ["street", "zip", "city", "country_name","province"]; // "state_code"];
                _.each(all_fields, function (field) {
                    $(".checkout_autoformat .div_" + field.split('_')[0]).toggle($.inArray(field, data.fields)>=0);
                });
            }
        });

    },

   });

   //nuevas funciones

    publicWidget.registry.portalDetailsjs = publicWidget.Widget.extend({
    selector: '.o_portal_details',
    events: {
        'change select[name="state_id"]': '_onChangeState',
        'change select[name="province_id"]': '_onChangeProvince',
        'change select[name="district_id"]': '_onChangeDistrict',
        'change select[name="l10n_latam_identification_type_id"]': '_onChangeDocvat',
        'change input[name="vat"]': '_onChangeDocvat',

    },

    start: function () {
        var def = this._super.apply(this, arguments);
        this.$('select[name="state_id"]').change();
        this.$('select[name="province_id"]').change();
        this.$('select[name="district_id"]').change();
        //this.$('select[name="l10n_latam_identification_type_id"]').change();
        //this.$('input[name="vat"]').change();
        return def;
    },
    _onChangeDocvat: function () {
      if (!$("#vat").val()) {

            return;
        }
      if (!$("#l10n_latam_identification_type_id").val()) {

            return;
        }

      this._rpc({
            route: "/shop/verify_doc/" + $("#l10n_latam_identification_type_id").val(),
            params: {
                mode: 'shipping',
                vat: $("#vat").val()
            },
        }).then(function (data) {

            if (data.state == 'error') {
               return
               //alert(data.msg);
            }else{
              var dx = data.data;


              if (dx.name){
                $('#name').val(dx.name);
              }
              if (dx.street){
                $('#street').val(dx.street);
              }
              if (dx.zip){
                $('#zipcode').val(dx.zip).attr('readonly','1');
              }

              if (dx.country_id){
                $('#country_id').data('init',dx.country_id);
                $('#country_id').val(dx.country_id);


                if (dx.state_id){
                  var selectStates = $('#state_id');
                  $('#state_id').attr('data-init',dx.state_id);
                  selectStates.html('');
                  var init_data = $('<option>').attr('value',dx.state_id).text(dx.state_name).attr('selected', '1');
                  selectStates.append(init_data);
                  selectStates.parent().show();

                  if (dx.province_id){
                    $('#province_id').val(dx.province_id);
                    var selectStatesx = $('#province_id');
                    selectStatesx.html('');
                    var init_datax = $('<option>').attr('value',dx.province_id).text(dx.province_name).attr('selected', '1');
                    selectStatesx.append(init_datax);
                    selectStatesx.parent().show();


                    if (dx.district_id){
                        $('#district_id').val(dx.district_id);
                        var selectStatesy = $('#district_id');
                        selectStatesy.html('');
                        var init_datay = $('<option>').attr('value',dx.district_id).text(dx.district_name).attr('selected', '1');
                        selectStatesy.append(init_datay);
                        selectStatesy.parent().show();
                    }
                   }

                  }
                }

              }

        });


    },
    _onChangeState: function () {

        if (!$("#state_id").val()) {

            return;
        }else{

          var vv = $("#state_id").val();
          var dd = "#state_id option[value='"+vv+"']"
          var code = $(dd).data('code')
          if (code != '15'){
             $('.ship_to_otherx').toggle($('#shipping_use_same').prop('checked'));
          }else{
             $('.ship_to_otherx').hide();
           }
        }



        this._rpc({
            route: "/shop/states_infos/" + $("#state_id").val(),
            params: {
                mode: 'shipping',
            },
        }).then(function (data) {

            // placeholder phone_code
            //$("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+'+ data.phone_code : '');

            // populate states and display
            var selectStates = $("select[name='province_id']");
            // dont reload state at first loading (done in qweb)

            if (1==1) {
                if (data.states.length) {
                    selectStates.html('');
                    var init_data = $('<option>').attr('value','').text('Provincia ...');
                    selectStates.append(init_data);

                    _.each(data.states, function (x) {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0])
                            .attr('data-code', x[2]);
                        if (selectStates.data('init')===x[0]){
                           opt.attr('selected', '1');

                        }
                        selectStates.append(opt);
                    });
                    selectStates.parent('div').show();
                } else {
                    selectStates.val('').parent('div').hide();
                }

            }


        });

    },

    _onChangeProvince: function () {
        if (!$("#province_id").val()) {
            return;
        }



        this._rpc({
            route: "/shop/province_infos/" + $("#province_id").val(),
            params: {
                mode: 'shipping',
            },
        }).then(function (data) {
            var selectStates = $("select[name='district_id']");
            // dont reload state at first loading (done in qweb)
            if (1==1) {
                if (data.states.length) {
                    selectStates.html('');
                    var init_data = $('<option>').attr('value','').text('Distrito ...');
                    selectStates.append(init_data);
                    _.each(data.states, function (x) {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0])
                            .attr('data-code', x[2]);
                        if (selectStates.data('init')===x[0]){
                           opt.attr('selected', '1');

                        }
                        selectStates.append(opt);
                    });
                    selectStates.parent('div').show();
                } else {
                    selectStates.val('').parent('div').hide();
                }

            }
        });
    },

    _ChangeZip: function (id) {
        if (!$(id).val()) {
            return
        }else{

          this._rpc({
            route: "/shop/district/" + $("#district_id").val(),
            params: {
                mode: 'shipping',
            },
        }).then(function (data) {
            if(data){
               $('input[name="zipcode"]').val(data).attr('readonly','1');

            }
        });



        }


    },

    _onChangeDistrict: function () {
       this._ChangeZip("#district_id");
    },


    });


});