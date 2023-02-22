# -*- coding: utf-8 -*-

from werkzeug import urls
import datetime

from . import vnpay

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.http import request, _logger

import hashlib
import urllib
import urllib.parse 
import hmac
import urllib.request

# from odoo.addons.teb_payment_vnpay.controllers.controllers import MyController


VNP_ERROR_CODE = {
    "05": """Giao dịch không thành công do: Quý khách nhập sai mật khẩu thanh toán
quá số lần quy định.""",
    "06": """Giao dịch không thành công do khách nhập sai mật khẩu xác thực giao
dịch (OTP).""",
    "07": """Trừ tiền thành công, giao dịch bị nghi ngờ (liên quan tới lừa đảo, giao dịch bất thường...).""",
    "12": """Giao dịch không thành công do: Thẻ/Tài khoản của khách hàng bị khóa.""",
    "09": """Giao dịch không thành công do: Thẻ/Tài khoản của khách hàng chưa đăng
ký dịch vụ InternetBanking tại ngân hàng.""",
    "10": """Giao dịch không thành công do: Khách hàng xác thực thông tin thẻ/tài
khoản không đúng quá 3 lần""",
    "11": "Giao dịch không thành công do: Đã hết hạn chờ thanh toán",
    "24": """Giao dịch không thành công do: Khách hàng hủy giao dịch""",
    "51": """Giao dịch không thành công do: Tài khoản của khách hàng không đủ số dư
để thực hiện giao dịch.""",
    "65": """Giao dịch không thành công do: Tài khoản của khách hàng đã vượt quá hạn
mức giao dịch trong ngày.""",
    "75": """Ngân hàng thanh toán đang bảo trì""",
    "99": """Thanh toán thất bại."""
}

class VNPayTransaction(models.Model):
    _inherit = 'payment.transaction'

    bank_tran_no = fields.Char(string="Bank transaction")
    bank_code = fields.Char(string="Bank")
    vnpay_first_update = fields.Boolean(default=True)

    @api.model

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Paypal-specific rendering values.
        Note: self.ensure_one() from `_get_processing_values`
        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'vnpay':
            return res
       
        vnpay_api_url = self.env['payment.provider'].search([('code','=','vnpay')])._vnpay_get_api_url()
        createDate = datetime.datetime.now().strftime(
                '%Y%m%d%H%M%S')
        print("--amount--")
        orderId = datetime.datetime.now().strftime('%H%M%S')
        
        vnp = vnpay.vnpay()
        vnp.requestData.update({
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_OrderType': 'topup',
            'vnp_TmnCode': self.env['payment.provider'].search([('code','=','vnpay')]).vnpay_website_code,
            'vnp_Amount': str(int(self.amount * 100)),
            'vnp_CurrCode': 'VND',
            'vnp_TxnRef': orderId,
            'vnp_OrderInfo': "Thanh toan don hang thoi gian " + orderId,
            'vnp_Locale': 'vn',
            'vnp_CreateDate': createDate,
            'vnp_IpAddr': str(
                    request.httprequest.environ['REMOTE_ADDR']),
            'vnp_ReturnUrl': self.provider_id.get_base_url() + 'vnpay/return'
        })
       
        print('????111')
        print(vnp.requestData)
        # query_params = urllib.parse.urlencode(vnp.requestData, quote_via=urllib.parse.quote, safe='=&')
        # vnp_url += '?' + query_params
        # print('vnpUrl:', vnp_url)
        url = vnp.get_payment_url(vnpay_api_url, "FWBUUIGSRCATAEKPZDSXYIAVQMTSLKYY")
        
        
        print('-----url----')
        print(url)
        

        data = vnp.requestData
        data.update({
            'vnpay_api_url': url
        })
        print("data =>>>>>> ")
        print(data)
        return data

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on Paypal data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        print('-----_process_notification_data-----')
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'vnpay' or len(tx) == 1:
            return tx

        reference = notification_data.get('item_number')
        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'paypal')])
        if not tx:
            raise ValidationError(
                "VnPay: " + _("No transaction found matching reference %s.", reference)
            )
        return tx

    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on Paypal data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider
        :return: None
        :raise: ValidationError if inconsistent data were received
        """
        print('-----_process_notification_data-----')
        super()._process_notification_data(notification_data)
        print(self.read())
        if self.provider_code != 'vnpay':
            return

        txn_id = notification_data.get('txn_id')
        txn_type = notification_data.get('txn_type')
        if not all((txn_id, txn_type)):
            raise ValidationError(
                "VnPay: " + _(
                    "Missing value for txn_id (%(txn_id)s) or txn_type (%(txn_type)s).",
                    txn_id=txn_id, txn_type=txn_type
                )
            )
        self.provider_reference = txn_id
        self.paypal_type = txn_type

        payment_status = notification_data.get('payment_status')

        if payment_status in PAYMENT_STATUS_MAPPING['pending'] + PAYMENT_STATUS_MAPPING['done'] \
            and not (self.provider_id.paypal_pdt_token and self.provider_id.paypal_seller_account):
            # If a payment is made on an account waiting for configuration, send a reminder email
            self.provider_id._paypal_send_configuration_reminder()

        if payment_status in PAYMENT_STATUS_MAPPING['pending']:
            self._set_pending(state_message=notification_data.get('pending_reason'))
        elif payment_status in PAYMENT_STATUS_MAPPING['done']:
            self._set_done()
        elif payment_status in PAYMENT_STATUS_MAPPING['cancel']:
            self._set_canceled()
        else:
            _logger.info(
                "received data with invalid payment status (%s) for transaction with reference %s",
                payment_status, self.reference
            )
            self._set_error(
                "PayPal: " + _("Received data with invalid payment status: %s", payment_status)
            )

    def _vnpay_form_get_tx_from_data(self, data):
        """ Given a data dict coming from stripe, verify it and find the related
        transaction record. """
        reference = data.get('vnp_TxnRef')
        if not reference:
            vnp_error = data.get('error', {}).get('message', '')
            _logger.error('VNPay: invalid reply received from vnpay API, looks like '
                          'the transaction failed. (error: %s)', vnp_error or 'n/a')
            error_msg = _(
                "We're sorry to report that the transaction has failed.")
            if vnp_error:
                error_msg += " " + (_("VNPAy gave us the following info about the problem: '%s'") %
                                    vnp_error)
            error_msg += " " + _("Perhaps the problem can be solved by double-checking your "
                                 "credit card details, or contacting your bank?")
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference)])
        if not tx:
            error_msg = (
                _('VNPay: no order found for reference %s') % reference)
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        elif len(tx) > 1:
            error_msg = (_('VNPay: %s orders found for reference %s') %
                         (len(tx), reference))
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        return tx[0]

    def _vnpay_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        if data.get('vnp_ResponseCode') != '00':
            invalid_parameters.append(
                "Response not 00: %s" % data.get('vnp_ResponseCode'))
        # if data.get('vnp_Amount') != int(
        #         self.amount if self.currency_id.name in INT_CURRENCIES else float_round(self.amount * 100, 2)):
        #     invalid_parameters.append(('Amount', data.get('amount'), self.amount * 100))
        # if data.get('payment_intent') and data.get('payment_intent') != self.stripe_payment_intent:
        #     invalid_parameters.append(('Payment Intent', data.get('payment_intent'), self.stripe_payment_intent))
        return invalid_parameters

    # def vnp_check_valid(self, data=None):
    #     self._set_transaction_done()
    #     return True

    def vnp_update_done(self, data):
        self._set_transaction_done()
        data.update({
            'vnpay_first_update': False
        })
        self.write(data)

    def vnp_update_cancel(self, code):
        self._set_transaction_cancel()
        data = {
            'state_message': VNP_ERROR_CODE[code],
            'vnpay_first_update': False
        }
        self.write(data)

    def __hash(self, input):
        byteInput = input.encode('utf-8')
        return hashlib.sha256(byteInput).hexdigest()
    
    def hmacsha512(key, data):
        byteKey = key.encode('utf-8')
        byteData = data.encode('utf-8')
        return hmac.new(byteKey, byteData, hashlib.sha512).hexdigest()
