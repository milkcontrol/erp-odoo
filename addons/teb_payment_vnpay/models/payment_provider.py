# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import vnpay
import datetime
from odoo.http import request, _logger

    
vnpay_sandbox_url = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"

class AcquirerVNPay(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('vnpay', 'VNPay')], ondelete={
                            'vnpay': 'set default'})
    vnpay_acquirer_exid = fields.Char(readonly=True)
    vnpay_api_url = fields.Char(string='API Url', groups='base.group_system')
    vnpay_website_code = fields.Char(
        string='Website Code', groups='base.group_system')
    vnpay_hash_secret = fields.Char(string='Hash Secret', groups='base.group_system')

    _sql_constraints = [
        ('vnpay_acquirer_exid', 'unique(vnpay_acquirer_exid)', 'Extend id must be unique!')]

    def vnpay_form_generate_values(self, values):
        print('jump here vnpay_form_generate_values')
        base_url = self.get_base_url()
        vnp = vnpay.vnpay()
        vnp.requestData['vnp_Version'] = '2.1.0'
        vnp.requestData['vnp_Command'] = 'pay'
        vnp.requestData['vnp_OrderType'] = 'shopping'
        vnp.requestData['vnp_TmnCode'] = self.vnpay_website_code
        vnp.requestData['vnp_Amount'] = self._format_amount(values['amount'])
        vnp.requestData['vnp_CurrCode'] = 'VND'
        vnp.requestData['vnp_TxnRef'] = values['reference']
        vnp.requestData['vnp_OrderInfo'] = "Thanh toan don hang " + \
            values['reference']
        vnp.requestData['vnp_Locale'] = 'vn'
        vnp.requestData['vnp_CreateDate'] = datetime.datetime.now().strftime(
            '%Y%m%d%H%M%S')
        vnp.requestData['vnp_IpAddr'] = str(
            request.httprequest.environ['REMOTE_ADDR'])
        vnp.requestData['vnp_ReturnUrl'] = base_url + 'vnpay/return'

        url = vnp.get_payment_url(self.vnpay_api_url, self.vnpay_hash_secret)
        data = dict()
        data.update({
            'checkout_link': url,
        })
        return data
    

    def _format_amount(self, values):
        return str(int(values * 100))
    
    def _vnpay_get_api_url(self):
        """ Return the API URL according to the provider state.

        Note: self.ensure_one()

        :return: The API URL
        :rtype: str
        """
        self.ensure_one()

        if self.state == 'enabled':
            return vnpay_sandbox_url
        else:
            return vnpay_sandbox_url


