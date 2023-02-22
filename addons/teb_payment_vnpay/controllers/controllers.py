from odoo import http
from odoo.http import request
import werkzeug
from werkzeug.utils import redirect

import odoo
import json
from ..models import vnpay


class MyController(odoo.http.Controller):
    @odoo.http.route('/foo', auth='public', csrf=False)
    def foo_handler(self, **kwargs):
        return "Welcome to 'foo' API!"

    @odoo.http.route('/vnpay/return', auth='public', csrf=False)
    def vnpay_return(self, **kwargs):
        print('----return-url----')
        # return redirect('/payment/process')
        return redirect('/payment/status')


    @odoo.http.route('/vnpay/ipn', auth='public', csrf=False)
    def demo(self, **kwargs):
        try:
            acquirer = request.env['payment.acquirer'].sudo().search([('vnpay_acquirer_exid', '=', 'vnpay')])

            inputData = kwargs
            vnp_TransactionNo = inputData['vnp_TransactionNo']
            vnp_ResponseCode = inputData['vnp_ResponseCode']
            vnp_BankCode = inputData['vnp_BankCode']
            vnp_Amount = int(inputData['vnp_Amount']) / 100
            vnp_TxnRef = inputData['vnp_TxnRef']
            try:
                vnp_BankTranNo = inputData['vnp_BankTranNo']
            except KeyError:
                vnp_BankTranNo = ""

            vnp = vnpay.vnpay()
            vnp.responseData = inputData

            if vnp.validate_response(acquirer.vnpay_hash_secret):
                transaction = request.env['payment.transaction'].sudo().search([('reference', '=', vnp_TxnRef)])
                if transaction:
                    is_first_update = transaction.vnpay_first_update
                    if is_first_update:
                        if vnp_Amount == transaction.amount:
                            if vnp_ResponseCode == '00':
                                data = {
                                    "acquirer_reference": vnp_TransactionNo,
                                    "bank_tran_no": vnp_BankTranNo,
                                    "bank_code": vnp_BankCode
                                }
                                transaction.vnp_update_done(data)
                            else:
                                transaction.vnp_update_cancel(vnp_ResponseCode)
                            result = {'RspCode': '00', 'Message': 'Confirm Success'}
                        else:
                            result = {'RspCode': '04', 'Message': 'Invalid amount'}
                    else:
                        result = {'RspCode': '02', 'Message': 'Order Already Update'}
                else:
                    result = {'RspCode': '01', 'Message': 'Order not found'}
            else:
                result = {'RspCode': '97', 'Message': 'Invalid Signature'}

        except:
            result = {'RspCode': '99', 'Message': 'Unknown error'}
        return json.dumps(result)
    
    @odoo.http.route('/vnpay/result', type='http', auth='public', website=True)
    def payment_result(self, **post):
        values = {}
        payment_reference = post.get('reference')
        if payment_reference:
            order = request.env['sale.order'].search([('payment_reference', '=', payment_reference)])
            if order:
                values.update({
                    'order': order,
                    'payment_result': post,
                })
        return request.render('payment_module.payment_result_template', values)
