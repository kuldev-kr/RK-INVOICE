from num2words import num2words
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
import streamlit as st
import os
from PIL import Image as PILImage

st.title("RAJESH Invoice Generator")

# Initialize daily bill counter in session state
today_str = datetime.now().strftime('%d%m%Y')
if 'last_date' not in st.session_state or st.session_state.last_date != today_str:
    st.session_state.last_date = today_str
    st.session_state.bill_counter = 1

# Format: XXDDMM (XX = daily count, DD = date, MM = month)
current_count_str = f"{st.session_state.bill_counter:02d}"
dd_mm = datetime.now().strftime('%d%m')
auto_invoice_no = f"{current_count_str}{dd_mm}"

# User Inputs for Invoice Header
invoice_no = st.text_input("Invoice No (Auto XXDDMM)", value=auto_invoice_no)
invoice_date = st.date_input("Date")
customer_name = st.text_input("Customer Name", "Enter Customer Name")
customer_phone = st.text_input("Customer Phone Number", "Enter Phone Number")
customer_address = st.text_input("Customer Address", "Enter Address")

# Dynamic Items Table input using Session State
if 'invoice_items' not in st.session_state:
    st.session_state.invoice_items = [{'description': '', 'price': 0.0, 'quantity': 1}]

def add_item():
    st.session_state.invoice_items.append({'description': '', 'price': 0.0, 'quantity': 1})

def remove_item(index):
    if len(st.session_state.invoice_items) > 1:
        st.session_state.invoice_items.pop(index)

st.subheader("Description / Items")
for i, item in enumerate(st.session_state.invoice_items):
    cols = st.columns([3, 1, 1, 1])
    with cols[0]:
        st.session_state.invoice_items[i]['description'] = st.text_input(f"Description {i+1}", value=item['description'], key=f"desc_{i}")
    with cols[1]:
        st.session_state.invoice_items[i]['price'] = st.number_input(f"Price (INR) {i+1}", min_value=0.0, value=float(item['price']), key=f"price_{i}")
    with cols[2]:
        st.session_state.invoice_items[i]['quantity'] = st.number_input(f"Quantity {i+1}", min_value=1, value=int(item['quantity']), key=f"qty_{i}")
    with cols[3]:
        if st.button("Delete", key=f"del_{i}"):
            remove_item(i)
            st.rerun()

if st.button("Add Item"):
    add_item()
    st.rerun()

def generate_pdf(filename, inv_no, inv_date, cust_name, cust_phone, cust_address, items_list):
    doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    # Desktop path for logo.png and fixing rotation automatically to 90 degrees
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    logo_path = os.path.join(desktop_path, "logo.png")
    temp_logo_path = os.path.join(desktop_path, "temp_fixed_logo.png")

    if os.path.exists(logo_path):
        try:
            img = PILImage.open(logo_path)
            # Corrected rotation to 90 degrees to make it right-side up horizontally
            img = img.rotate(90, expand=True)
            img.save(temp_logo_path)
            logo_img = Image(temp_logo_path, width=90, height=45)
        except:
            logo_img = Image(logo_path, width=90, height=45)
    else:
        logo_img = Paragraph("<b>RAJESH LOGO</b>", styles['Normal'])

    invoice_title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=26,
        alignment=0,
        textColor=colors.HexColor("#D32F2F")
    )
    invoice_header_text = Paragraph("<b>INVOICE</b>", invoice_title_style)

    # Header Table with INVOICE on left and Logo on right side
    header_table = Table([[invoice_header_text, logo_img]], colWidths=[438, 100])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # Issued To & Details Table with Address field
    issued_text = f"<b>ISSUED TO:</b><br/>{cust_name}<br/><b>Address:</b> {cust_address}<br/><b>Phone:</b> {cust_phone}"
    meta_text = f"<b>Invoice No:</b> {inv_no}<br/><b>Date:</b> {inv_date.strftime('%d-%m-%Y')}"

    info_table = Table([[Paragraph(issued_text, styles['Normal']), Paragraph(meta_text, styles['Normal'])]], colWidths=[300, 238])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAFAFA")),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#00BCD4")),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # Items Table Header & Rows
    table_data = [["DESCRIPTION", "PRICE (INR)", "QUANTITY", "AMOUNT"]]
    
    total_amount = 0.0
    for item in items_list:
        amount = item['price'] * item['quantity']
        total_amount += amount
        table_data.append([
            item['description'],
            f"Rs. {item['price']:,.2f}",
            str(item['quantity']),
            f"Rs. {amount:,.2f}"
        ])

    items_table = Table(table_data, colWidths=[228, 100, 80, 130])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#00838F")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (0,1), (0,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#B2EBF2")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 15))

    # Total Table aligned right under Amount column
    summary_data = [
        ["TOTAL:", f"Rs. {total_amount:,.2f}"]
    ]
    summary_table = Table(summary_data, colWidths=[408, 130])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#E0F7FA")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#00838F")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # Rupee in Word outside below total
    try:
        rupees_in_words = num2words(int(total_amount), lang='en_IN').capitalize() + " Rupees Only"
    except:
        rupees_in_words = ""

    words_text = f"<b>RUPEE IN WORD:</b> {rupees_in_words}"
    story.append(Paragraph(words_text, styles['Normal']))

    doc.build(story)

if st.button("Generate Invoice PDF"):
    pdf_filename = f"invoice_{invoice_no}.pdf"
    generate_pdf(pdf_filename, invoice_no, invoice_date, customer_name, customer_phone, customer_address, st.session_state.invoice_items)
    
    st.session_state.bill_counter += 1
    
    with open(pdf_filename, "rb") as pdf_file:
        st.download_button(
            label="Download Invoice PDF",
            data=pdf_file,
            file_name=pdf_filename,
            mime="application/pdf"
        )
    st.success(f"Invoice {invoice_no} generated successfully as {pdf_filename}!")