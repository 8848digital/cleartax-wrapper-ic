import frappe
import requests
import json
from frappe import *
from gst_india.cleartax_integration.utils import success_response, error_response, response_error_handling, response_logger, get_dict


@frappe.whitelist()
def gstin_info(**kwargs):
    try:
        settings = frappe.get_doc('Cleartax Settings')
        for company in settings.e_invoicing:
            if company.get('company'):
                gstin = frappe.get_value('Company',company.get('company'),'gstin')
                break
        url = settings.host_url
        url+= "/api/method/cleartax.cleartax.API.gst."
        url+= 'gstin_info'
        data = {
            'gstin': kwargs.get('gstin'),
            'company_gstin': gstin
        } 
        headers = {
            'sandbox': str(settings.sandbox),
            'Content-Type': 'application/json'
        }
        if settings.enterprise:
            headers['token'] = settings.get_password('production_auth_token')
            if settings.sandbox:
                headers['token'] = settings.get_password('sandbox_auth_token')
        data = json.dumps(data, indent=4, sort_keys=False, default=str)
        response = requests.request("GET", url, headers=headers, data= data) 
        response = response.json()['message']
        frappe.logger('cleartax').exception(response)
        if response['msg'] != 'Success':
            return "GSTIN Details Not Found!"
        return response['response']
    except Exception as e:
        frappe.logger('cleartax').exception(e)
        return error_response(e)


@frappe.whitelist()
def create_gst_invoice(**kwargs):
    try:
        invoice = kwargs.get('invoice')
        type = kwargs.get('type')
        if  type == "SALE":
            doctype = "Sales Invoice"
        else:
            doctype = "Purchase Invoice"
        invoice = frappe.get_doc(doctype,kwargs.get('invoice'))
        item_list = []
        gst_round_off = 0 #frappe.get_value('GST Settings','round_off_gst_values')
        gst_settings_accounts = frappe.get_all("GST Account",
                filters={'company':invoice.company},
                fields=["cgst_account", "sgst_account", "igst_account", "cess_account"])
        for row in invoice.items:
            item_list.append(get_dict('Item',row.item_code))
        data = {
            'invoice': invoice.as_dict(),
            'type': type,
            'item_list': item_list,
            'gst_accounts':gst_settings_accounts,
            'gst_round_off': gst_round_off
        }
        if type == 'SALE':
            data['company_address'] = get_dict('Address',invoice.company_address)
            data['customer'] = get_dict('Customer',invoice.customer)
            data['customer_address'] = get_dict('Address',invoice.customer_address)
            data['shipping_address'] = get_dict('Address',invoice.shipping_address_name)
        else:
            data['company_address'] = get_dict('Address',invoice.supplier_address)
            data['customer_address'] = get_dict('Address',invoice.billing_address)
            data['shipping_address'] = get_dict('Address',invoice.shipping_address)
        if invoice.is_return:
            data['original_invoice'] = get_dict(doctype,invoice.return_against)

        return gst_invoice_request(data,kwargs.get('invoice'),type)
    except Exception as e:
        frappe.logger('cleartax').exception(e)
        return error_response(e)


def gst_invoice_request(data,id,type):
    try:
        settings = frappe.get_doc('Cleartax Settings')
        url = settings.host_url
        url+= "/api/method/cleartax.cleartax.API.gst."
        headers = {
            'sandbox': str(settings.sandbox),
            'Content-Type': 'application/json'
        }
        if type == 'SALE':
            url+= 'gst_sales'
            gstin = data.get('company_address').get('gstin')
        else:
            url+= 'gst_purchase'
            gstin = data.get('customer_address').get('gstin')
        headers['gstin'] = gstin
        if settings.enterprise:
            headers['token'] = settings.get_password('gst_auth_token')
        if settings.sandbox:
            headers['token'] = settings.get_password('gst_sandbox_token')
        data = json.dumps(data, indent=4, sort_keys=False, default=str)
        response = requests.request("POST", url, headers=headers, data= data) 
        response = response.json()['message']
        if response.get('response').get('error'):
            return error_response(response.get('response').get('error'))
        api = "GENERATE GST SINV" if type == 'SALE' else "GENERATE GST PINV"
        doctype = "Sales Invoice" if type == 'SALE' else "Purchase Invoice"
        response_status = response['msg']
        response_logger(response['request'],response['response'],api,doctype,id,response_status)
        if response_status == "Success":
            if type == 'SALE':
                frappe.db.set_value('Sales Invoice',id,'gst_invoice',1)
            else:
                frappe.db.set_value('Purchase Invoice',id,'gst_invoice',1)
            return success_response()
        return response_error_handling(response.get('response'))
    except Exception as e:
        frappe.logger('cleartax').exception(e)
        return error_response(e)


def gst_cdn_request(data,id,type):
    try:
        settings = frappe.get_doc('Cleartax Settings')
        url = settings.host_url
        url+= "/api/method/cleartax.cleartax.API.gst.create_gst_invoice"
        headers = {
            'sandbox': str(settings.sandbox),
            'Content-Type': 'application/json'
        }
        if type == 'SALE':
            gstin = data.get('company_address').get('gstin')
        else:
            gstin = data.get('customer_address').get('gstin')
        if settings.enterprise:
            headers['token'] = settings.get_password('gst_auth_token')
            #headers['taxid'] = settings.tax_id(gstin)
        data = json.dumps(data, indent=4, sort_keys=False, default=str)
        response = requests.request("PUT", url, headers=headers, data= data)
        response = response.json()['message']
        if response.get('error'):
            return error_response(response.get('error'))
        response_status = response['msg']
        api = "GENERATE GST CDN"
        doctype = "Sales Invoice" if type == 'SALE' else "Purchase Invoice"
        response_logger(response['request'],response['response'],api,doctype,id,response_status)
        if response_status == 'Success':
            if type == 'SALE':
                frappe.db.set_value('Sales Invoice',id,'cdn',1)
            else:
                frappe.db.set_value('Purchase Invoice',id,'cdn',1)
            return success_response(response['response'])
        return response_error_handling(response['response'])
    except Exception as e:
        frappe.logger('cleartax').exception(e)
        return error_response(e)
    
def bulk_gst_processing(**kwargs):
    try:
        data = json.loads(kwargs.get('data'))

        for i in data:
            create_gst_invoice(**{'invoice':i,'type':'PURCHASE'})
        frappe.publish_realtime("bulk_gst")
    except Exception as e:
        frappe.logger('sfa_online').exception(e)


@frappe.whitelist()
def bulk_purchase_gst(**kwargs):
    try:
        frappe.enqueue("gst_india.cleartax_integration.API.gst.bulk_gst_processing",**{'data':kwargs.get('data')})
    except Exception as e:
        frappe.logger('sfa_online').exception(e)


def bulk_gst_processing_sales(**kwargs):
    try:
        data = json.loads(kwargs.get('data'))
        
        for i in data:
            create_gst_invoice(**{'invoice':i,'type':'SALE'})
        frappe.publish_realtime("bulk_gst")
    except Exception as e:
        frappe.logger('sfa_online').exception(e)


@frappe.whitelist()
def bulk_sales_gst(**kwargs):
    try:
        frappe.enqueue("gst_india.cleartax_integration.API.gst.bulk_gst_processing_sales",**{'data':kwargs.get('data')})
    except Exception as e:
        frappe.logger('sfa_online').exception(e)