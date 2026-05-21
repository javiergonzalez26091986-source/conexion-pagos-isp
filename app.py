import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Conexión Pagos", layout="centered")
st.title("💳 Conexión Pagos")

# --- SIMULACIÓN DE CARGA DE DATOS ---
# NOTA: Cuando conectes tu Google Sheets, reemplaza esto con la carga real
@st.cache_data(ttl=60)
def cargar_clientes():
    # Aquí puedes conectar con Google Sheets más adelante usando gspread o una API
    data = {
        'CODIGO': ['16892013', '12345678'],
        'NOMBRE': ['JANER RODRIGUEZ', 'CLIENTE PRUEBA'],
        'CONTRATO': ['CONT-001', 'CONT-002']
    }
    return pd.DataFrame(data)

df = cargar_clientes()

# --- INTERFAZ ---
cedula_input = st.text_input("Ingresa tu número de cédula:")

if cedula_input:
    # Filtrar cliente en el DataFrame
    cliente = df[df['CODIGO'].astype(str) == str(cedula_input)]
    
    if not cliente.empty:
        nombre = cliente.iloc[0]['NOMBRE']
        st.success(f"Hola, {nombre}")
        
        with st.form("registro_pago"):
            contrato = st.selectbox("Selecciona tu contrato:", cliente['CONTRATO'].tolist())
            valor = st.number_input("Valor pagado:", min_value=0)
            fecha = st.date_input("Fecha de pago")
            mes = st.selectbox("Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                                        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
            archivo = st.file_uploader("Sube tu comprobante:", type=['jpg', 'png', 'pdf'])
            
            submit = st.form_submit_button("Enviar Reporte")
            
            if submit:
                if archivo is not None:
                    # AQUÍ ES DONDE CONECTAREMOS CON EL GOOGLE APPS SCRIPT
                    # Por ahora, simulamos el registro exitoso
                    st.info(f"Enviando datos de {nombre} al servidor...")
                    
                    st.balloons()
                    st.success("¡Pago reportado exitosamente!")
                else:
                    st.warning("Por favor adjunta el comprobante.")
    else:
        st.error("Cédula no encontrada. Por favor verifica el número.")
