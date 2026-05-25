import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import requests
import time  # <-- Nueva librería para la recarga automática

# --- CONFIGURACIÓN DE APIS ---
CLOUDINARY_CLOUD_NAME = "dgdtwbmot"
CLOUDINARY_PRESET = "conexion_pagos_preset1"
URL_APP_SCRIPT = "https://script.google.com/macros/s/AKfycbzcAnlhqTu-gAxteS-14UpE8UIMUxVDLztnO6a8Vx9Xaqg_uso__qJqQBgzBB0ePIUnNA/exec"

# --- CARGAR IMÁGENES ---
try:
    logo_completo = Image.open('logoSenalMas.jpeg')
    isotipo = Image.open('logoSenalMas.ico')
except Exception:
    logo_completo = None
    isotipo = "💳"

st.set_page_config(page_title="Señal Más | Portal de Pagos", page_icon=isotipo, layout="centered")

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stAppDeployButton {display:none;}
        div[data-testid="stToolbar"] { visibility: hidden !important; }

        .main { background-color: #00233c; }
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
        
        h1, h3 { text-align: center !important; }
        h1 { color: #ffffff; font-size: 2.2rem; margin-top: 0; font-weight: 700; }
        h3 { color: #b0c4de; font-size: 1.1rem; font-weight: 400; margin-bottom: 2.5rem; }
        .stMarkdown p { color: #ffffff; text-align: center; }
        
        .stTextInput > div > div > input { background-color: #ffffff; color: #00233c; border-radius: 8px; border: 2px solid #00a896; }
        
        .stForm { border: none; border-radius: 12px; background-color: #ffffff; padding: 2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        .stForm label, .stForm p { color: #00233c !important; font-weight: 600; text-align: left; }
        
        div[data-testid="stFormSubmitButton"] button {
            background-color: #00a896 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            font-size: 1.1rem !important;
            border: none !important;
            padding: 0.7rem 2rem !important;
            width: 100% !important;
            box-shadow: 0 4px 10px rgba(0,168,150,0.3) !important;
            text-shadow: none !important;
            display: inline-block !important;
        }
        
        div[data-testid="stFormSubmitButton"] button p {
            color: #ffffff !important;
            font-weight: 700 !important;
        }
        
        div[data-testid="stFormSubmitButton"] button:hover {
            background-color: #02c3b1 !important;
            color: #ffffff !important;
            box-shadow: 0 6px 15px rgba(2,195,177,0.5) !important;
        }
        
        .stMarkdown hr { border: 0; height: 1px; background: linear-gradient(to right, transparent, #b0c4de, transparent); margin-top: 3rem; }
    </style>
    """, unsafe_allow_html=True)

# --- ENCABEZADO CON LOGO CENTRADO ---
if logo_completo is not None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(logo_completo, use_column_width=True)

st.title("Portal de Pagos")
st.subheader("Gestión automatizada de soporte para nuestros clientes")

# --- FUNCIONES DE CONEXIÓN ---
@st.cache_data(ttl=60)
def cargar_clientes():
    try:
        response = requests.get(URL_APP_SCRIPT)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def guardar_registro_pago(cedula, nombre, contrato, valor, fecha, mes, url_comprobante):
    payload = {
        "cedula": str(cedula),
        "nombre": str(nombre),
        "contrato": str(contrato),
        "valor": valor,
        "fecha": str(fecha),
        "mes": str(mes),
        "url_comprobante": str(url_comprobante)
    }
    try:
        response = requests.post(URL_APP_SCRIPT, json=payload)
        if response.status_code == 200:
            return response.json().get("status") == "success"
        return False
    except Exception:
        return False

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

# --- FLUJO PRINCIPAL ---
df = cargar_clientes()

if not df.empty:
    cedula_input = st.text_input("Ingrese su número de cédula para continuar:", placeholder="Ej: 16892013")

    if cedula_input:
        cliente = df[df['CODIGO'].astype(str) == str(cedula_input)]
        
        if not cliente.empty:
            nombre = cliente.iloc[0]['NOMBRE']
            lista_contratos = cliente['CONTRATO'].astype(str).tolist()
            
            st.success(f"Bienvenido/a, **{nombre}**")
            
            # --- FORMULARIO (Agregamos clear_on_submit=True) ---
            with st.form("registro_pago", clear_on_submit=True):
                contrato = st.selectbox("Seleccione el contrato a reportar:", lista_contratos)
                valor = st.number_input("Valor pagado (COP):", min_value=0, step=1000, value=0)
                fecha = st.date_input("Fecha de realización del pago")
                mes = st.selectbox("Mes correspondiente:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=datetime.now().month-1)
                archivo = st.file_uploader("Adjuntar comprobante (JPG, PNG, PDF):", type=['jpg', 'png', 'pdf'])
                
                submit = st.form_submit_button("Enviar Reporte de Pago")
            
            # --- PROCESAMIENTO FUERA DEL FORMULARIO (Se renderiza abajo) ---
            if submit:
                if archivo is not None and valor > 0:
                    with st.spinner("Procesando información y guardando comprobante..."):
                        url_comprobante = subir_a_cloudinary(archivo)
                        
                        if url_comprobante:
                            guardado_exitoso = guardar_registro_pago(
                                cedula_input, nombre, contrato, valor, fecha, mes, url_comprobante
                            )
                            
                            if guardado_exitoso:
                                st.success("¡Reporte enviado y registrado exitosamente!")
                                st.info(f"**Referencia:** {datetime.now().strftime('%Y%m%d%H%M%S')}")
                                st.caption("Su comprobante ha sido almacenado de forma segura.")
                                
                                # Anuncio y pausa antes de la recarga
                                st.warning("🔄 Actualizando el portal por seguridad en 4 segundos...")
                                time.sleep(4)
                                st.rerun()
                            else:
                                st.error("Error al registrar en la base de datos de Google Sheets.")
                        else:
                            st.error("Fallo al subir la imagen a Cloudinary. Intente de nuevo.")
                else:
                    st.warning("Debe ingresar un valor mayor a 0 y adjuntar el soporte de pago.")
        else:
            st.error("Cédula no encontrada en nuestra base de datos.")
else:
    st.warning("Conectando con la base de datos o base de datos vacía...")

st.markdown("---")
st.markdown('<p style="color: #b0c4de; text-align: center; font-size: 0.9rem;">Señal Más | Innovación y Conectividad | senalmas.florida@gmail.com | +57 300 3190253</p>', unsafe_allow_html=True)
