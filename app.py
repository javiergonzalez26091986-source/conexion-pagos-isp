import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Conexión Pagos", layout="centered")
st.title("💳 Conexión Pagos")

# Configuración de credenciales (asegúrate de tener 'credenciales.json' en la misma carpeta)
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file('credenciales.json', scopes=scope)
    return gspread.authorize(creds)

# Cargar base de datos
@st.cache_data(ttl=60)
def cargar_clientes():
    client = get_gspread_client()
    sheet = client.open("NombreDeTuHoja").worksheet("baseDeDatos") 
    return pd.DataFrame(sheet.get_all_records())

# --- INTERFAZ ---
df = cargar_clientes()
cedula_input = st.text_input("Ingresa tu número de cédula:")

if cedula_input:
    # Filtrar cliente
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
                    # Lógica de registro
                    client = get_gspread_client()
                    sheet = client.open("NombreDeTuHoja").worksheet("RegistroPagos")
                    
                    # Guardar en GSheets
                    sheet.append_row([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        cedula_input,
                        nombre,
                        contrato,
                        valor,
                        str(fecha),
                        mes,
                        "Pendiente"
                    ])
                    st.balloons()
                    st.success("¡Pago reportado exitosamente!")
                else:
                    st.warning("Por favor adjunta el comprobante.")
    else:
        st.error("Cédula no encontrada. Por favor verifica el número.")
