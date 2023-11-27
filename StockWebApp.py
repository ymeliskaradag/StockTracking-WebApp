#import the libraries
import streamlit as st
import pandas as pd
import sqlite3 as sql
import random
import string
from PIL import Image
from datetime import date

today = date.today()
show_products = False

#for products' id
def generate_alphanumeric_id(length):
    characters = string.ascii_letters + string.digits
    alphanumeric_id = ''.join(random.choice(characters) for i in range(length))
    return alphanumeric_id

#a connection to a database where data is saved
conn = sql.connect("stock_set.db")
cursor = conn.cursor()

#to add a title
st.write(""" **Welcome to enter products into the warehouse** """)

#to show the image on the page
image = Image.open("C:/Users/micym/PycharmProjects/pythonProject/stock_image.png")
st.image(image, use_column_width=True)

#input from the user for products
st.title('Ürün Ekleme Formu')
product_id = generate_alphanumeric_id(12)
product_time = st.date_input('Ürünün Eklenme Tarihi', min_value= today)  #so that past dates cannot be selected
product_brand = st.text_input('Ürün Markası')
product_title = st.text_input('Ürün Adı')
product_exp = st.text_input('Ürün Açıklaması')
product_total = st.number_input('Ürün Miktarı', value= 0)

if product_brand:
    product_brand = product_brand.upper()
if product_title:
    product_title = product_title.upper()  #its important because it will be the table name
#columns on the tables
columns = "product_id TEXT PRIMARY KEY, product_time DATE, product_brand TEXT, product_title TEXT, product_exp TEXT, product_total INTEGER"

#the query to create a table
table_name = product_title.replace(' ', '_') #if there is a space in the name entered by the user, replace it with an underscore
query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
try:
    cursor.execute(query)
    print(f"{table_name} tablosu oluşturuldu veya zaten mevcut.")
except sql.Error as e:
    print(f"Hata oluştu: {e}")
conn.commit()

#to add the products to database
col1, col2, col3 = st.columns([3,3,3])
with col1:
    if st.button('Ürün Ekle', key='centered_button', help="Ürün eklemek için tıklayın"):
        #to check whether the product info is filled when the 'ürün ekle' button is pressed
        if not product_time or not product_brand or not product_title or not product_exp:
            st.warning('Ürün bilgileri boş bırakılamaz!')
        else:
            cursor.execute(f'''
            INSERT INTO {table_name} (product_id, product_time, product_brand, product_title, product_exp, product_total)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (product_id, product_time.strftime("%Y-%m-%d"), product_brand, product_title, product_exp, product_total))
            conn.commit()
            st.success('Ürün başarıyla eklendi.')
            product_time = None
            product_brand = ""
            product_title = ""
            product_exp = ""
            product_total = 0
            st.empty()

#to save an excel file to db
with col3:
    if st.button('Excel Dosyası Ekle', help="Excel dosyasından veri eklemek için tıklayın"):
        uploaded_file = st.file_uploader("Excel Dosyasını Yükleyin", type=["xlsx"])
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                for index, row in df.iterrows():
                    product_id = row['product_id']
                    product_time = row['product_time']
                    product_brand = row['product_brand']
                    product_title = row['product_title']
                    product_exp = row['product_exp']
                    product_total = row['product_total']

                    if product_brand:
                        product_brand = product_brand.upper()
                    if product_title:
                        product_title = product_title.upper()

                    table_name = product_title.replace(' ', '_')
                    cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        product_id TEXT PRIMARY KEY, 
                        product_time DATE,
                        product_brand TEXT,
                        product_title TEXT,
                        product_exp TEXT,
                        product_total INTEGER
                    )
                    ''')
                    cursor.execute(f'''
                    INSERT INTO {table_name} (product_id, product_time, product_brand, product_title, product_exp, product_total)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (product_id, product_time, product_brand, product_title, product_exp, product_total))
                    conn.commit()
                    st.success("Excel dosyası başarıyla veritabanına eklenmiştir.")
            except Exception as e:
                st.error(f"Hata oluştu: {e}")

#for all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
table_names = [table[0] for table in cursor.fetchall()]

#to choose how many products to show on each page
products_number_on_page = st.number_input('Her Sayfada Görünen Ürün Sayısı ', min_value=1, value=20)

#for all products
products = []
for table_name in table_names:
    cursor.execute(f'SELECT * FROM {table_name}')
    products.extend(cursor.fetchall())
total_products = len(products)

st.sidebar.header('Kategoriler')

#to identify brands and subcategories
for table_name in table_names:
    cursor.execute(f"SELECT DISTINCT product_brand FROM {table_name}")
    brands = cursor.fetchall()

    for brand in brands:
        brand_name = brand[0]
        expander = st.sidebar.expander(f"Marka: {brand_name}", expanded=True)

        cursor.execute(f"SELECT DISTINCT product_title FROM {table_name} WHERE product_brand = ?", (brand_name,))
        titles = cursor.fetchall()

        with expander:
            #st.sidebar.text(f"Ürün Başlıkları:")
            for title in titles:
                title_name = title[0]
                st.sidebar.text(f"{title_name}")

#to view all products in a list
if st.sidebar.button("Ürünleri Görüntüle"):
    show_products = True
    page_no = 1
    st.subheader('Ürünler')
    while (page_no - 1) * products_number_on_page < total_products:
        start = (page_no - 1) * products_number_on_page
        end = start + products_number_on_page

        if show_products:
            for i, prdct in enumerate(products[start:end], start=start + 1):
                product_id, product_time, product_brand, product_title, product_exp, product_total = prdct

                expander = st.expander(f"Ürün: {product_title}")
                with expander:
                    st.write(f"Marka: {product_brand}")
                    st.write(f"Açıklama: {product_exp}")
                    st.write(f"Toplam: {product_total}")

                    if st.button(f"Sil - {product_id}"):
                        cursor.execute(f"DELETE FROM {table_name} WHERE product_id = ?", (product_id,))
                        conn.commit()
                        st.success(f"{product_title} başarıyla silindi.")

                    if st.button(f"Güncelle - {product_id}"):
                        updated_brand = st.text_input("Yeni Marka", value=product_brand)
                        updated_title = st.text_input("Yeni Ürün Adı", value=product_title)
                        updated_exp = st.text_input("Yeni Açıklama", value=product_exp)
                        updated_total = st.number_input("Yeni Toplam Miktar", value=product_total)

                        if st.button("Onayla"):
                            cursor.execute(
                                f"UPDATE {table_name} SET product_brand = ?, product_title = ?, product_exp = ?, product_total = ? WHERE product_id = ?",
                                (updated_brand, updated_title, updated_exp, updated_total, product_id))
                            conn.commit()
                            st.success(f"{product_title} başarıyla güncellendi.")
        page_no += 1

conn.close()
