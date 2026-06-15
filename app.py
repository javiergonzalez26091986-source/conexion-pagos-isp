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
OCR_SPACE_API_KEY = "helloworld" 

# --- INICIALIZACIÓN DE ESTADOS ---
if "run_id" not in st.session_state: st.session_state.run_id = 0
if "ocr_valor" not in st.session_state: st.session_state.ocr_valor = 0
if "ocr_ref" not in st.session_state: st.session_state.ocr_ref = ""
if "ultimo_archivo" not in st.session_state: st.session_state.ultimo_archivo = None

# --- CARGAR IMÁGENES ---
try:
    logo_completo = Image.open('logoSenalMas.jpeg')
    isotipo = Image.open('logoSenalMas.ico')
except Exception:
    logo_completo = None; isotipo = "💳"

st.set_page_config(page_title="Señal Más | Portal de Pagos", page_icon=isotipo, layout="centered")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        .stAppDeployButton {display:none;} div[data-testid="stToolbar"] { visibility: hidden !important; }
        
        /* Forzamos el fondo negro puro en la app completa y contenedor principal */
        .stApp, .main { background-color: #000000 !important; } 
        
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
        h1, h3 { text-align: center !important; }
        h1 { color: #ffffff; font-size: 2.2rem; margin-top: 0; font-weight: 700; }
        h3 { color: #b0c4de; font-size: 1.1rem; font-weight: 400; margin-bottom: 2.5rem; }
        .stMarkdown p { color: #ffffff; text-align: center; }
        .stTextInput > div > div > input { background-color: #ffffff; color: #000000; border-radius: 8px; border: 2px solid #00a896; }
        .stForm { border: none; border-radius: 12px; background-color: #ffffff; padding: 2rem; box-shadow: 0 4px 15px rgba(255,255,255,0.1); }
        .stForm label, .stForm p { color: #000000 !important; font-weight: 600; text-align: left; }
        div[data-testid="stFormSubmitButton"] button {
            background-color: #00a896 !important; color: #ffffff !important; border-radius: 8px !important;
            font-weight: 700 !important; font-size: 1.1rem !important; border: none !important;
            padding: 0.7rem 2rem !important; width: 100% !important; box-shadow: 0 4px 10px rgba(0,168,150,0.3) !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover { background-color: #02c3b1 !important; box-shadow: 0 6px 15px rgba(2,195,177,0.5) !important; }
        .stMarkdown hr { border: 0; height: 1px; background: linear-gradient(to right, transparent, #b0c4de, transparent); margin-top: 3rem; }
    </style>
    """, unsafe_allow_html=True)

if logo_completo is not None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2: st.image(logo_completo, use_column_width=True)

st.title("Portal de Pagos")
st.subheader("Gestión automatizada de soporte para nuestros clientes")

# --- FUNCIONES DE CONEXIÓN ---
@st.cache_data(ttl=30)
def cargar_datos_y_referencias():
    try:
        response = requests.get(URL_APP_SCRIPT)
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data.get("clientes", [])), data.get("referencias", [])
        return pd.DataFrame(), []
    except Exception:
        return pd.DataFrame(), []

def guardar_registro_pago(cedula, nombre, contrato, valor, fecha, mes, referencia_pago, referencia_sistema, url_comprobante):
    payload = {
        "cedula": str(cedula), "nombre": str(nombre), "contrato": str(contrato),
        "valor": valor, "fecha": str(fecha), "mes": str(mes),
        "referencia_pago": str(referencia_pago), "referencia_sistema": str(referencia_sistema),
        "url_comprobante": str(url_comprobante)
    }
    try:
        response = requests.post(URL_APP_SCRIPT, json=payload)
        return response.json().get("status") == "success" if response.status_code == 200 else False
    except Exception:
        return False

def subir_a_cloudinary(archivo_subido):
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
    if archivo.type == "application/pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(archivo)
            for page in reader.pages: texto_completo += page.extract_text() or ""
        except Exception: pass
            
    if not texto_completo.strip():
        try:
            url_ocr = "https://api.ocr.space/parse/image"
            payload = {"apikey": OCR_SPACE_API_KEY, "language": "spa", "isOverlayRequired": False}
            files = {"file": (archivo.name, archivo.getvalue(), archivo.type)}
            res = requests.post(url_ocr, data=payload, files=files, timeout=12)
            if res.status_code == 200 and not res.json().get("IsErroredOnProcessing"):
                texto_completo = res.json()["ParsedResults"][0]["ParsedText"]
        except Exception: pass
            
    valor_detectado = 0; ref_detectada = ""
    
    if texto_completo:
        # Limpieza inicial para leer de corrido
        texto_clean = texto_completo.lower().replace('\n', ' ').replace('\r', ' ')
        
        # 1. Extracción de Valor Monetario (Omitiendo los céntimos de Nequi/Bancolombia)
        valores = re.findall(r'\$\s*([\d\.,]+)', texto_clean)
        if valores:
            raw_val = valores[0]
            raw_val = re.sub(r'[,.]\d{2}$', '', raw_val) # Elimina los ,00 o .00 finales
            num_clean = raw_val.replace(".", "").replace(",", "")
            if num_clean.isdigit(): valor_detectado = int(num_clean)
            
        # 2. Extracción de Referencia (Ajustado para Nequi/Bancolombia)
        # Prioridad 1: Buscar "número de referencia" seguido de una secuencia alfanumérica.
        match_ref = re.search(r'n[uú]mero de referencia\s*([a-z0-9]{5,20})', texto_clean)
        
        if match_ref:
            ref_detectada = match_ref.group(1).upper()
        else:
            # Prioridad 2: Buscar otras palabras clave (ref, aprobacion) y capturar letras+números
            match_otras = re.search(r'(?:referencia|ref\.|aprobaci[óo]n|autorizaci[óo]n).{0,15}?([a-z0-9]{5,20})', texto_clean)
            if match_otras and match_otras.group(1) != "movimiento": # Evitamos falsos positivos
                 ref_detectada = match_otras.group(1).upper()
            else:
                 # Prioridad 3: Buscar un patrón clásico de Nequi (M seguido de números) suelto en el texto
                 match_nequi = re.search(r'\b(m\d{5,10})\b', texto_clean)
                 if match_nequi:
                     ref_detectada = match_nequi.group(1).upper()
            
    return valor_detectado, ref_detectada

# --- FLUJO PRINCIPAL ---
df, referencias_existentes = cargar_datos_y_referencias()

if not df.empty:
    cedula_input = st.text_input("Ingrese su número de cédula para continuar:", placeholder="Ej: 16892013", key=f"ced_in_{st.session_state.run_id}")

    if cedula_input:
        cliente = df[df['CODIGO'].astype(str) == str(cedula_input)]
        
        if not cliente.empty:
            nombre = cliente.iloc[0]['NOMBRE']
            lista_contratos = cliente['CONTRATO'].astype(str).tolist()
            
            st.success(f"Bienvenido/a, **{nombre}**")
            st.markdown("---")
            
            st.markdown("<p style='text-align:left; font-weight:bold; color:#b0c4de;'>1️⃣ Adjunte su soporte de pago para auto-llenar los campos:</p>", unsafe_allow_html=True)
            archivo = st.file_uploader("", type=['jpg', 'png', 'pdf', 'jpeg'], key=f"file_{st.session_state.run_id}")
            
            if archivo and (st.session_state.ultimo_archivo != archivo.name):
                with st.spinner("🔍 Lector óptico analizando el comprobante..."):
                    v_opt, r_opt = ejecutar_lector_optico(archivo)
                    st.session_state.ocr_valor = v_opt
                    st.session_state.ocr_ref = r_opt
                    st.session_state.ultimo_archivo = archivo.name
                    st.toast("✅ ¡Comprobante leído de forma óptica!", icon="🤖")

            st.markdown("<br><p style='text-align:left; font-weight:bold; color:#b0c4de;'>2️⃣ Verifique o complete la información del reporte:</p>", unsafe_allow_html=True)
            
            with st.form("registro_pago"):
                contrato = st.selectbox("Seleccione el contrato a reportar:", lista_contratos)
                
                # Etiqueta actualizada con el símbolo $
                valor = st.number_input("Valor pagado ($ COP):", min_value=0, step=1000, value=st.session_state.ocr_valor)
                referencia_pago = st.text_input("Referencia o N° de operación del pago:", value=st.session_state.ocr_ref, placeholder="Ej: 1948204812")
                
                fecha = st.date_input("Fecha de realización del pago")
                mes = st.selectbox("Mes correspondiente:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=datetime.now().month-1)
                
                submit = st.form_submit_button("Enviar Reporte de Pago")
                
                if submit:
                    ref_limpia = referencia_pago.strip()
                    
                    if ref_limpia != "" and str(ref_limpia) in [str(r) for r in referencias_existentes]:
                        st.error(f"⚠️ Atención: El comprobante con referencia '{ref_limpia}' ya se encuentra registrado en el sistema. Por favor, verifique para evitar un doble reporte.")
                    
                    elif archivo is not None and valor > 0 and ref_limpia != "":
                        with st.spinner("Procesando información y subiendo archivos administrativos..."):
                            url_comprobante = subir_a_cloudinary(archivo)
                            
                            if url_comprobante:
                                ref_sistema_generada = datetime.now().strftime('%Y%m%d%H%M%S')
                                guardado_exitoso = guardar_registro_pago(
                                    cedula_input, nombre, contrato, valor, fecha, mes, 
                                    ref_limpia, ref_sistema_generada, url_comprobante
                                )
                                
                                if guardado_exitoso:
                                    st.success("¡Reporte enviado y registrado exitosamente!")
                                    st.info(f"**Referencia del sistema:** {ref_sistema_generada}")
                                    
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
