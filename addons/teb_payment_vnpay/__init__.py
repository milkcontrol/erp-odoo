# -*- coding: utf-8 -*-

from . import controllers
from . import models
# from odoo.addons.payment.models.payment_acquirer import create_missing_journal_for_acquirers
from odoo.addons.payment import setup_provider, reset_payment_provider

def post_init_hook(cr, registry):
    setup_provider(cr, registry, 'vnpay')


def uninstall_hook(cr, registry):
    reset_payment_provider(cr, registry, 'vnpay')