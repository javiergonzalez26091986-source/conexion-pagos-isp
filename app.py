import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import requests
import time
import re

# --- CONFIGURACIÓN DE APIS ---
CLOUDINARY_CLOUD_NAME = "dgdtwbmot"
CLOUDINARY_PRESET = "conexion_pagos_preset1"
URL_APP_SCRIPT = "https://script.google.com/macros/s/AKfycbzcAnlhqTu-gAxteS-14UpE8UIMUxVDLztnO6a8Vx9Xaqg_uso__qJqQBgzBB0ePIUnNA/exec"

# API Key gratuita de OCR.space para el lector óptico (Puedes usar 'helloworld' para pruebas básicas)
OCR_SPACE_API_KEY = "helloworld" 

# --- INICIALIZACIÓN DE ESTADOS ---
if "run_id" not in st.session_state:
    st.session_state.run_id = 0
if "ocr_valor" not in st.session_state:
    st.session_state.ocr_valor = 0
if "ocr_ref" not in st.session_state:
    st.session_state.ocr_ref = ""
if "ultimo_archivo" not in st.session_state:
    st.session_state.ultimo_archivo = None

# --- CARGAR IMÁGENES DE INTERFAZ ---
try:
    logo_completo = Image.open('logoSenalMas.jpeg')
    isotipo = Image.open('logoSenalMas.ico')
except Exception:
    logo_completo = None
    isotipo = "💳"

st.set_page_config(page_title="Señal Más | Portal de Pagos", page_icon=isotipo, layout="centered")

# --- ESTILOS CSS UNIFICADOS ---
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
        }
        div[data-testid="stFormSubmitButton"] button:hover {
            background-color: #02c3b1 !important;
            box-shadow: 0 6px 15px rgba(2,195,177,0.5) !important;
        }
        .stMarkdown hr { border: 0; height: 1px; background: linear-gradient(to right, transparent, #b0c4de, transparent); margin-top: 3rem; }
    </style>
    """, unsafe_allow_html=True)

if logo_completo is not None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2: st.image(logo_completo, use_column_width=True)

st.title("Portal de Pagos")
st.subheader("Gestión automatizada de soporte para nuestros clientes")

# --- FUNCIONES DE CONEXIÓN Y PROCESAMIENTO ---
@st.cache_data(ttl=60)
def cargar_clientes():
    try:
        response = requests.get(URL_APP_SCRIPT)
        return pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def guardar_registro_pago(cedula, nombre, contrato, valor, fecha, mes, referencia, url_comprobante):
    payload = {
        "cedula": str(cedula), "nombre": str(nombre), "contrato": str(contrato),
        "valor": valor, "fecha": str(fecha), "mes": str(mes),
        "referencia": str(referencia), "url_comprobante": str(url_comprobante)
    }
    try:
        response = requests.post(URL_APP_SCRIPT, json=payload)
        return response.json().get("status") == "success" if response.status_code == 200 else False
    except Exception:
        return False

def subir_a_cloudinary(archivo_subido):
    # SOLUCIÓN BUG PDF: Cambiado /image/ a /auto/ para soportar cualquier formato y fotos de cámara
    url_api = f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD_NAME}/auto/upload"
    payload = {"upload_preset": CLOUDINARY_PRESET}
    files = {"file": (archivo_subido.name, archivo_subido.getvalue(), archivo_subido.type)}
    try:
        response = requests.post(url_api, data=payload, files=files)
        return response.json().get("secure_url") if response.status_code == 200 else None
    except Exception:
        return None

def ejecutar_lector_optico(archivo):
    texto_completo = ""
    # 1. Si es PDF Digital, extraemos texto nativo directamente
    if archivo.type == "application/pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(archivo)
            for page in reader.pages:
                texto_completo += page.extract_text() or ""
        except Exception:
            pass
            
    # 2. Si es imagen o el PDF no arrojó texto, usamos el motor OCR en la nube
    if not texto_completo.strip():
        try:
            url_ocr = "https://api.ocr.space/parse/image"
            payload = {"apikey": OCR_SPACE_API_KEY, "language": "spa", "isOverlayRequired": False}
            files = {"file": (archivo.name, archivo.getvalue(), archivo.type)}
            res = requests.post(url_ocr, data=payload, files=files, timeout=12)
            if res.status_code == 200 and not res.json().get("IsErroredOnProcessing"):
                texto_completo = res.json()["ParsedResults"][0]["ParsedText"]
        except Exception:
            pass
            
    # --- INTELIGENCIA DE EXTRACCIÓN (REGEX) ---
    valor_detectado = 0
    ref_detectada = ""
    
    if texto_completo:
        texto_clean = texto_completo.lower()
        
        # Buscar estructuras de dinero (ej: $ 85.000 o $85000)
        valores = re.findall(r'\$\s*([\d\.,]+)', texto_clean)
        if valores:
            num_clean = valores[0].replace(".", "").replace(",", "")
            if num_clean.isdigit(): valor_detectado = int(num_clean)
            
        # Buscar números de referencia comunes (ej: Referencia, Operación, Transacción de 6 a 12 dígitos)
        referencias = re.findall(r'\b\d{6,14}\b', texto_clean)
        if referencias:
            ref_detectada = referencias[0]
            
    return valor_detectado, ref_detectada

# --- FLUJO PRINCIPAL ---
df = cargar_clientes()

if not df.empty:
    cedula_input = st.text_input("Ingrese su número de cédula para continuar:", placeholder="Ej: 16892013", key=f"ced_in_{st.session_state.run_id}")

    if cedula_input:
        cliente = df[df['CODIGO'].astype(str) == str(cedula_input)]
        
        if not cliente.empty:
            nombre = cliente.iloc[0]['NOMBRE']
            lista_contratos = cliente['CONTRATO'].astype(str).tolist()
            
            st.success(f"Bienvenido/a, **{nombre}**")
            st.markdown("---")
            
            # --- PASO 1: EL COMPROBANTE VA PRIMERO ---
            st.markdown("<p style='text-align:left; font-weight:bold; color:#b0c4de;'>1️⃣ Adjunte su soporte de pago para auto-llenar los campos:</p>", unsafe_allow_html=True)
            archivo = st.file_uploader("", type=['jpg', 'png', 'pdf', 'jpeg'], key=f"file_{st.session_state.run_id}")
            
            # Disparador del Lector Óptico Inteligente
            if archivo and (st.session_state.ultimo_archivo != archivo.name):
                with st.spinner("🔍 Lector óptico analizando el comprobante..."):
                    v_opt, r_opt = ejecutar_lector_optico(archivo)
                    st.session_state.ocr_valor = v_opt
                    st.session_state.ocr_ref = r_opt
                    st.session_state.ultimo_archivo = archivo.name
                    st.toast("✅ ¡Comprobante leído de forma óptica!", icon="🤖")

            # --- PASO 2: FORMULARIO DE VERIFICACIÓN ---
            st.markdown("<br><p style='text-align:left; font-weight:bold; color:#b0c4de;'>2️⃣ Verifique o complete la información del reporte:</p>", unsafe_allow_html=True)
            
            # SOLUCIÓN BUG VALIDACIÓN: Eliminado clear_on_submit=True para evitar pérdida de datos
            with st.form("registro_pago"):
                contrato = st.selectbox("Seleccione el contrato a reportar:", lista_contratos)
                
                # Campos precargados dinámicamente con los resultados de la IA
                valor = st.number_input("Valor pagado (COP):", min_value=0, step=1000, value=st.session_state.ocr_valor)
                referencia_pago = st.text_input("Referencia o N° de operación del pago:", value=st.session_state.ocr_ref, placeholder="Ej: 1948204812")
                
                fecha = st.date_input("Fecha de realización del pago")
                mes = st.selectbox("Mes correspondiente:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=datetime.now().month-1)
                
                submit = st.form_submit_button("Enviar Reporte de Pago")
                
                if submit:
                    if archivo is not None and valor > 0 and referencia_pago.strip() != "":
                        with st.spinner("Procesando información y subiendo archivos administrativos..."):
                            url_comprobante = subir_a_cloudinary(archivo)
                            
                            if url_comprobante:
                                guardado_exitoso = guardar_registro_pago(
                                    cedula_input, nombre, contrato, valor, fecha, mes, referencia_pago, url_comprobante
                                )
                                
                                if guardado_exitoso:
                                    st.success("¡Reporte enviado y registrado exitosamente!")
                                    st.info(f"**Referencia del sistema:** {datetime.now().strftime('%Y%m%d%H%M%S')}")
                                    st.caption("Los datos coinciden con su comprobante digital adjunto.")
                                    
                                    # Reseteo total controlado tras éxito
                                    st.session_state.run_id += 1
                                    st.session_state.ocr_valor = 0
                                    st.session_state.ocr_ref = ""
                                    st.session_state.ultimo_archivo = None
                                    
                                    st.warning("🔄 Limpiando formulario para un nuevo registro en 4 segundos...")
                                    time.sleep(4)
                                    st.rerun()
                                else:
                                    st.error("Error al registrar en la base de datos de Google Sheets.")
                            else:
                                st.error("Fallo al subir el archivo (Formato o peso no admitido). Intente de nuevo.")
                    else:
                        st.warning("Verifique los campos: El valor debe ser mayor a 0, debe indicar la Referencia de pago y tener el soporte adjunto.")
        else:
            st.error("Cédula no encontrada en nuestra base de datos.")
else:
    st.warning("Conectando con la base de datos o base de datos vacía...")

st.markdown("---")
st.markdown('<p style="color: #b0c4de; text-align: center; font-size: 0.9rem;">Señal Más | Innovación y Conectividad | senalmas.florida@gmail.com | +57 300 3190253</p>', unsafe_allow_html=True)
