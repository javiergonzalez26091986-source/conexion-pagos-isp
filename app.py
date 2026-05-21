import streamlit as st
import pandas as pd
import gspread
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Conexión Pagos", layout="centered")
st.title("💳 Conexión Pagos")

# Nota: En Streamlit Cloud, usarás st.connection("gsheets") 
# para una integración nativa más rápida sin necesidad de JSON.
# Aquí está la lógica de tu formulario:

cedula = st.text_input("Ingresa tu número de cédula:")

if cedula:
    # (Aquí iría la carga de tu base de datos)
    st.success(f"Hola, cliente con cédula {cedula}") 
    
    with st.form("registro_pago"):
        contrato = st.text_input("Contrato:")
        valor = st.number_input("Valor pagado:", min_value=0)
        fecha = st.date_input("Fecha de pago")
        mes = st.selectbox("Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"])
        archivo = st.file_uploader("Sube tu comprobante:", type=['jpg', 'png', 'pdf'])
        
        if st.form_submit_button("Enviar Reporte"):
            if archivo:
                # Aquí iría tu lógica de append_row
                st.success("¡Pago reportado con éxito!")
            else:
                st.error("Debes adjuntar el comprobante.")