from gst_india.cleartax_integration.API.ewb import ewb_without_irn
import frappe 

def delivery_note_submit(doc, method=None):
    if frappe.db.get_single_value('Cleartax Settings','automate'):
        ewb_without_irn(**{'delivery_note':doc.name})

def delivery_note_save(doc,method=None):
    if not doc.shipping_address_name:
        doc.shipping_address_name = doc.customer_address
    if not doc.dispatch_address_name:
        doc.dispatch_address_name = doc.company_address

def delivery_note_cancel(doc, method=None):
    if doc.ewaybill and not doc.eway_bill_cancelled:
        frappe.throw("Please Cancel EWB!")