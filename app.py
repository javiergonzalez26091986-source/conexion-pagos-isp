import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import requests
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN DE CLOUDINARY ---
CLOUDINARY_CLOUD_NAME = "ddouzzs1i"
CLOUDINARY_PRESET = "conexion_pagos_preset"

# --- CARGAR IMÁGENES ---
try:
    logo_completo = Image.open('logoSenalMas.jpeg')
    isotipo = Image.open('logoSenalMas.ico')
except Exception:
    logo_completo = None
    isotipo = "💳"

st.set_page_config(page_title="Señal Más | Portal de Pagos", page_icon=isotipo, layout="centered")

# --- CONEXIÓN A GOOGLE SHEETS ---
def obtener_cliente_gsheets():
    """Autentica y retorna el cliente de gspread usando st.secrets"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # Se obtienen las credenciales desde los secretos de Streamlit
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=60) # Refresca la base de datos cada 60 segundos
def cargar_clientes():
    """Lee la pestaña 'baseDeDatos' y retorna un DataFrame"""
    try:
        cliente_gs = obtener_cliente_gsheets()
        sheet = cliente_gs.open("Conexión Pagos").worksheet("baseDeDatos")
        # get_all_records usa la primera fila como encabezados (CODIGO, NOMBRE, CONTRATO)
        datos = sheet.get_all_records()
        df = pd.DataFrame(datos)
        # Limpiar filas vacías por si acaso
        df = df.dropna(subset=['CODIGO'])
        return df
    except Exception as e:
        st.error(f"No se pudo conectar con la base de datos: {e}")
        return pd.DataFrame()

def guardar_registro_pago(cedula, nombre, contrato, valor, fecha, mes, url_comprobante):
    """Inserta una nueva fila en la pestaña 'RegistroPagos'"""
    try:
        cliente_gs = obtener_cliente_gsheets()
        sheet = cliente_gs.open("Conexión Pagos").worksheet("RegistroPagos")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        estado_inicial = "Por Verificar"
        
        # El orden debe coincidir exactamente con tus columnas:
        # Timestamp | Cedula | NombreCliente | Contrato | ValorPagado | FechaPago | MesPago | Estado | Soporte de pago
        fila = [
            timestamp, 
            str(cedula), 
            nombre, 
            str(contrato), 
            valor, 
            str(fecha), 
            mes, 
            estado_inicial, 
            url_comprobante
        ]
        
        sheet.append_row(fila)
        return True
    except Exception as e:
        st.error(f"Error al guardar el registro en Google Sheets: {e}")
        return False

# --- FUNCIÓN PARA SUBIR ARCHIVOS A CLOUDINARY ---
def subir_a_cloudinary(archivo_subido):
    url_api = f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD_NAME}/image/upload"
    payload = {"upload_preset": CLOUDINARY_PRESET}
    files = {"file": (archivo_subido.name, archivo_subido.getvalue(), archivo_subido.type)}
    try:
        response = requests.post(url_api, data=payload, files=files)
        if response.status_code == 200:
            return response.json().get("secure_url")
        return None
    except Exception:
        return None

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
        .main { background-color: #00233c; }
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        h1 { color: #ffffff; text-align: center; font-size: 2.2rem; margin-top: 0; font-weight: 700; }
        h3 { color: #b0c4de; text-align: center; font-size: 1.1rem; font-weight: 400; margin-bottom: 2.5rem; }
        .stMarkdown p { color: #ffffff; text-align: center; }
        .stTextInput > div > div > input { background-color: #ffffff; color: #00233c; border-radius: 8px; border: 2px solid #00a896; }
        .stForm { border: none; border-radius: 12px; background-color: #ffffff; padding: 2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        .stForm label, .stForm p { color: #00233c !important; font-weight: 600; text-align: left; }
        .stButton>button { background-color: #00233c; color: white; border-radius: 8px; font-weight: 600; width: 100%; transition: 0.3s; }
        .stButton>button:hover { background-color: #00a896; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- ENCABEZADO CON LOGO CENTRADO (MÉTODO INFALIBLE CON COLUMNAS) ---
if logo_completo is not None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(logo_completo, use_column_width=True)

st.title("Portal de Pagos")
st.subheader("Gestión automatizada de soporte para nuestros clientes")

# --- FLUJO PRINCIPAL ---
df = cargar_clientes()

if not df.empty:
    cedula_input = st.text_input("Ingrese su número de cédula para continuar:", placeholder="Ej: 16892013")

    if cedula_input:
        # Filtramos como string para evitar errores con los tipos de datos de Sheets
        cliente = df[df['CODIGO'].astype(str) == str(cedula_input)]
        
        if not cliente.empty:
            # Si una cédula tiene varios contratos, extraemos la lista de contratos
            nombre = cliente.iloc[0]['NOMBRE']
            lista_contratos = cliente['CONTRATO'].astype(str).tolist()
            
            st.success(f"Bienvenido/a, **{nombre}**")
            
            with st.form("registro_pago"):
                contrato = st.selectbox("Seleccione el contrato a reportar:", lista_contratos)
                valor = st.number_input("Valor pagado (COP):", min_value=0, step=1000, value=0)
                fecha = st.date_input("Fecha de realización del pago")
                mes = st.selectbox("Mes correspondiente:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=datetime.now().month-1)
                archivo = st.file_uploader("Adjuntar comprobante (JPG, PNG, PDF):", type=['jpg', 'png', 'pdf'])
                submit = st.form_submit_button("Enviar Reporte de Pago")
                
                if submit:
                    if archivo is not None and valor > 0:
                        with st.spinner("Procesando información..."):
                            url_comprobante = subir_a_cloudinary(archivo)
                            
                            if url_comprobante:
                                # Llamamos a la función que inserta en la hoja RegistroPagos
                                guardado_exitoso = guardar_registro_pago(
                                    cedula_input, nombre, contrato, valor, fecha, mes, url_comprobante
                                )
                                
                                if guardado_exitoso:
                                    st.success("¡Reporte enviado y registrado exitosamente!")
                                    st.info(f"**Referencia:** {datetime.now().strftime('%Y%m%d%H%M%S')}")
                                    st.caption("Su comprobante ha sido almacenado de forma segura.")
                            else:
                                st.error("Fallo al subir la imagen. Intente de nuevo.")
                    else:
                        st.warning("Debe ingresar un valor mayor a 0 y adjuntar el soporte de pago.")
        else:
            st.error("Cédula no encontrada en nuestra base de datos.")
else:
    st.warning("Conectando con la base de datos o base de datos vacía...")

st.markdown("---")
st.markdown('<p style="color: #b0c4de; text-align: center; font-size: 0.9rem;">Señal Más | Innovación y Conectividad</p>', unsafe_allow_html=True)
