import frappe 
from gst_india.cleartax_integration.API.gst import create_gst_invoice 


def purchase_invoice_submit(doc, method=None):
    if frappe.db.get_single_value('Cleartax Settings','automate'):
        r = create_gst_invoice(**{'invoice':doc.name,'type': "PURCHASE"})
        if r.get('msg') == "success":
            doc.gst_invoice = 1
            

def purchase_invoice_cancel(doc, method=None):
    if frappe.db.get_single_value('Cleartax Settings','automate'):
        create_gst_invoice(**{'invoice':doc.name,'type': "PURCHASE",'cancel':1})

def purchase_invoice_save(doc,method=None):
    if not doc.shipping_address:
        doc.shipping_address = doc.billing_address
    if doc.import_supplier ==1:
        if doc.gst_import_supplier_gst_details:
            for item in doc.gst_import_supplier_gst_details:
                # if item.item_rate and not item.item_amount:
                #     item.item_amount=float(item.qty)*float(item.item_rate)
                if item.item_rate and item.item_amount and item.qty:
                    item.item_rate=float(item.item_amount)/float(item.qty)
    if doc.gst_category == "Unregistered":
        if doc.taxes_and_charges_added <= 0:
            doc.custom_non_gst = 1



    