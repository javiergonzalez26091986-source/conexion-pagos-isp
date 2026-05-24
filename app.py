import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image

# --- CARGAR IMÁGENES DESDE EL REPOSITORIO ---
# Usamos los nombres exactos que tienes en tu GitHub
try:
    logo_completo = Image.open('logoSenalMas.jpeg')
    isotipo = Image.open('logoSenalMas.ico')
except Exception:
    # Salvaguarda por si ejecutas en un entorno sin las imágenes aún
    logo_completo = None
    isotipo = "💳"

# --- CONFIGURACIÓN DE PÁGINA ---
# El isotipo (.ico) se asigna a la pestaña del navegador de forma nativa
st.set_page_config(
    page_title="Señal Más | Portal de Pagos", 
    page_icon=isotipo, 
    layout="centered"
)

# --- ESTILOS PERSONALIZADOS (Ajuste de color corporativo e integración del logo) ---
st.markdown("""
    <style>
        /* Fondo de la página ajustado al azul oscuro exacto del logo de Señal Más */
        .main { 
            background-color: #00233c; 
        }
        
        /* Contenedor del contenido principal */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* Contenedor CSS para centrar y armonizar el logo */
        .logo-container {
            display: flex;
            justify-content: center;
            margin-bottom: 1.5rem;
        }

        /* Título en color blanco para resaltar sobre el fondo oscuro */
        h1 {
            color: #ffffff;
            text-align: center;
            font-size: 2.2rem;
            margin-top: 0;
            font-weight: 700;
        }

        /* Subtítulo en un tono claro suavizado */
        h3 {
            color: #b0c4de;
            text-align: center;
            font-size: 1.1rem;
            font-weight: 400;
            margin-bottom: 2.5rem;
        }

        /* Estilo para los textos informativos fijos en pantalla */
        .stMarkdown p {
            color: #ffffff;
        }

        /* Caja de entrada de texto (Cédula) adaptada */
        .stTextInput > div > div > input {
            background-color: #ffffff;
            color: #00233c;
            border-radius: 8px;
            border: 2px solid #00a896;
        }

        /* Estilo elegante para el formulario blanco interno */
        .stForm {
            border: none;
            border-radius: 12px;
            background-color: #ffffff;
            padding: 2rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        /* Asegurar que las etiquetas del formulario sean legibles sobre el fondo blanco */
        .stForm label {
            color: #00233c !important;
            font-weight: 600;
        }

        /* Botón de envío estilizado con el color corporativo */
        .stButton>button {
            background-color: #00233c;
            color: white;
            border-radius: 8px;
            font-weight: 600;
            border: none;
            padding: 0.6rem 2rem;
            width: 100%;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            background-color: #00a896;
            color: white;
            box-shadow: 0 4px 10px rgba(0,168,150,0.4);
        }

        /* Separador decorativo del Footer */
        .stMarkdown hr {
            border: 0;
            height: 1px;
            background: linear-gradient(to right, transparent, #b0c4de, transparent);
            margin-top: 3rem;
        }
        
        /* Texto del Footer centrado */
        .caption-footer {
            color: #b0c4de;
            text-align: center;
            font-size: 0.9rem;
            margin-top: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

# --- ENCABEZADO CON LOGO ---
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
    # Filtro de cliente
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
                    with st.spinner("Enviando reporte al área administrativa..."):
                        # --- INTEGRACIÓN FUTURA CON GOOGLE SHEETS / CLOUDINARY ---
                        # Aquí procesarás la lógica en la siguiente fase.
                        
                        st.success("¡Reporte enviado exitosamente!")
                        st.info(f"**Referencia de seguimiento:** {datetime.now().strftime('%Y%m%d%H%M%S')}")
                        st.caption("Hemos recibido su comprobante correctamente. El equipo técnico validará su información en el menor tiempo posible.")
                else:
                    st.warning("Por favor, adjunte el soporte de pago para completar la operación.")
    else:
        st.error("Cédula no encontrada en el sistema. Por favor, verifique el número ingresado.")

# --- FOOTER ---
st.markdown("---")
st.markdown('<p class="caption-footer">Señal Más | Innovación y Conectividad</p>', unsafe_allow_html=True)
