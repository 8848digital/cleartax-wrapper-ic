from gst_india.cleartax_integration.API.irn import generate_irn, e_invoicing_enabled
from gst_india.cleartax_integration.API.gst import create_gst_invoice
import frappe
from frappe.utils import flt
import secrets
import string
def sales_invoice_submit(doc, method=None):
    if frappe.db.get_single_value('Cleartax Settings','automate'):
        if e_invoicing_enabled(company=doc.company):
            generate_irn(**{'invoice':doc.name})
        else:
            create_gst_invoice(**{'invoice':doc.name,'type':"SALE"})
        

def sales_invoice_cancel(doc, method=None):
    if not e_invoicing_enabled(company=doc.company):
        create_gst_invoice(**{'invoice':doc.name,'type': "SALE",'cancel':1})
    else:
        if doc.ewaybill and not doc.eway_bill_cancelled:
            frappe.throw("Please Cancel EWB!")
        if doc.irn and not doc.irn_cancelled:
            frappe.throw("Please Cancel IRN!")
            

def sales_invoice_save(doc,method=None):
    if not doc.shipping_address_name:
        doc.shipping_address_name = doc.customer_address
    if not doc.dispatch_address_name:
        doc.dispatch_address_name = doc.company_address
    if doc.gst_category == "Unregistered":
        if flt(doc.taxes_and_charges_added) <= 0:
            doc.custom_non_gst = 1


def generate_random_id(length=12):
    characters = string.ascii_letters + string.digits
    random_id = ''.join(secrets.choice(characters) for _ in range(length))
    return random_id


def group_id(doc,method=None):
    pan_no=frappe.db.get_value("Customer",doc.customer,'pan')

    random_id = generate_random_id()
    exist=frappe.db.exists("Generate Group ID", {"pan": pan_no,"party_type":"Customer"})
    if exist:
        doc.custom_group_id=frappe.db.get_value("Generate Group ID",exist,"random_id")
        # frappe.msgprint('Alredy exist the Pan')
    else:
        new_doc=frappe.new_doc("Generate Group ID")
        new_doc.pan=pan_no
        new_doc.pan_no=pan_no
        new_doc.random_id = random_id
        new_doc.document_no=doc.name
        new_doc.party_type="Customer"
        new_doc.dacument_type='Sales Invoice'
        new_doc.save()
        doc.custom_group_id = random_id

