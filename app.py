import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import requests

# --- CONFIGURACIÓN DE CLOUDINARY ---
CLOUDINARY_CLOUD_NAME = "ddouzzs1i"
CLOUDINARY_PRESET = "conexion_pagos_preset"

# --- CARGAR IMÁGENES DESDE EL REPOSITORIO ---
try:
    logo_completo = Image.open('logoSenalMas.jpeg')
    isotipo = Image.open('logoSenalMas.ico')
except Exception:
    logo_completo = None
    isotipo = "💳"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Señal Más | Portal de Pagos", 
    page_icon=isotipo, 
    layout="centered"
)

# --- ESTILOS PERSONALIZADOS (Centrado absoluto y diseño corporativo) ---
st.markdown("""
    <style>
        .main { background-color: #00233c; }
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        
        /* Ajuste clave para centrado absoluto del logo en Streamlit */
        .logo-container {
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 280px;
            text-align: center;
            margin-bottom: 1.5rem;
        }
        
        /* Forzar que la imagen interna de Streamlit siga el centrado */
        [data-testid="stMarkdownContainer"] .logo-container img {
            margin: 0 auto;
            display: block;
        }

        h1 { color: #ffffff; text-align: center; font-size: 2.2rem; margin-top: 0; font-weight: 700; }
        h3 { color: #b0c4de; text-align: center; font-size: 1.1rem; font-weight: 400; margin-bottom: 2.5rem; }
        .stMarkdown p { color: #ffffff; text-align: center; }
        
        /* Estilos de formulario e inputs */
        .stTextInput > div > div > input { background-color: #ffffff; color: #00233c; border-radius: 8px; border: 2px solid #00a896; }
        .stForm { border: none; border-radius: 12px; background-color: #ffffff; padding: 2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        .stForm label { color: #00233c !important; font-weight: 600; }
        .stForm p { color: #00233c !important; text-align: left; }
        
        /* Botón de envío */
        .stButton>button { background-color: #00233c; color: white; border-radius: 8px; font-weight: 600; border: none; padding: 0.6rem 2rem; width: 100%; transition: all 0.3s ease; }
        .stButton>button:hover { background-color: #00a896; color: white; box-shadow: 0 4px 10px rgba(0,168,150,0.4); }
        
        .stMarkdown hr { border: 0; height: 1px; background: linear-gradient(to right, transparent, #b0c4de, transparent); margin-top: 3rem; }
        .caption-footer { color: #b0c4de; text-align: center; font-size: 0.9rem; margin-top: 1rem; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN PARA SUBIR ARCHIVOS A CLOUDINARY ---
def subir_a_cloudinary(archivo_subido):
    url_api = f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD_NAME}/image/upload"
    payload = {"upload_preset": CLOUDINARY_PRESET}
    files = {"file": (archivo_subido.name, archivo_subido.getvalue(), archivo_subido.type)}
    
    try:
        response = requests.post(url_api, data=payload, files=files)
        if response.status_code == 200:
            return response.json().get("secure_url")
        else:
            st.error(f"Error en Cloudinary ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        st.error(f"Error de conexión al subir el archivo: {e}")
        return None

# --- ENCABEZADO CON LOGO CENTRADO ---
if logo_completo is not None:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(logo_completo, width=280)
    st.markdown('</div>', unsafe_allow_html=True)

st.title("Portal de Pagos")
st.subheader("Gestión automatizada de soporte para nuestros clientes")

# --- SIMULACIÓN DE CARGA DE DATOS ---
@st.cache_data(ttl=60)
def cargar_clientes():
    data = {
        'CODIGO': ['16892013', '12345678'],
        'NOMBRE': ['JANER RODRIGUEZ', 'CLIENTE PRUEBA'],
        'CONTRATO': ['CONT-001', 'CONT-002']
    }
    return pd.DataFrame(data)

df = cargar_clientes()

# --- INTERFAZ DE USUARIO ---
cedula_input = st.text_input("Ingrese su número de cédula para continuar:", placeholder="Ej: 16892013")

if cedula_input:
    cliente = df[df['CODIGO'].astype(str) == str(cedula_input)]
    
    if not cliente.empty:
        nombre = cliente.iloc[0]['NOMBRE']
        st.success(f"Bienvenido/a, **{nombre}**")
        
        with st.form("registro_pago"):
            contrato = st.selectbox("Seleccione el contrato a reportar:", cliente['CONTRATO'].tolist())
            valor = st.number_input("Valor pagado (COP):", min_value=0, step=1000, value=0)
            fecha = st.date_input("Fecha de realización del pago")
            mes = st.selectbox("Mes correspondiente:", [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ], index=datetime.now().month-1)
            archivo = st.file_uploader("Adjuntar comprobante (JPG, PNG, PDF):", type=['jpg', 'png', 'pdf'])
            
            submit = st.form_submit_button("Enviar Reporte de Pago")
            
            if submit:
                if archivo is not None:
                    with st.spinner("Subiendo comprobante de pago de forma segura..."):
                        url_comprobante = subir_a_cloudinary(archivo)
                        
                        if url_comprobante:
                            st.success("¡Reporte enviado exitosamente!")
                            st.info(f"**Referencia de seguimiento:** {datetime.now().strftime('%Y%m%d%H%M%S')}")
                            st.caption("Hemos recibido su comprobante correctamente. El equipo técnico validará su información.")
                            st.caption(f"🔗 [Ver archivo en Cloudinary]({url_comprobante})")
                        else:
                            st.error("No se pudo procesar el archivo. Inténtelo de nuevo.")
                else:
                    st.warning("Por favor, adjunte el soporte de pago para completar la operación.")
    else:
        st.error("Cédula no encontrada en el sistema. Por favor, verifique el número ingresado.")

# --- FOOTER ---
st.markdown("---")
st.markdown('<p class="caption-footer">Señal Más | Innovación y Conectividad</p>', unsafe_allow_html=True)
