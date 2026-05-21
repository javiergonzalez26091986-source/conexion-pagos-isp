import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Señal Más | Portal de Pagos", layout="centered")

# --- ESTILOS PERSONALIZADOS (Opcional: para darle un toque más limpio) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    </style>
    """, unsafe_allow_html=True)

st.title("💳 Señal Más | Reporte de Pagos")
st.subheader("Gestión automatizada de soporte")

# --- SIMULACIÓN DE CARGA DE DATOS ---
@st.cache_data(ttl=60)
def cargar_clientes():
    # En el futuro, aquí realizarás la conexión real a Google Sheets
    data = {
        'CODIGO': ['16892013', '12345678'],
        'NOMBRE': ['JANER RODRIGUEZ', 'CLIENTE PRUEBA'],
        'CONTRATO': ['CONT-001', 'CONT-002']
    }
    return pd.DataFrame(data)

df = cargar_clientes()

# --- INTERFAZ DE USUARIO ---
cedula_input = st.text_input("Ingrese su número de cédula para continuar:")

if cedula_input:
    # Filtro de cliente
    cliente = df[df['CODIGO'].astype(str) == str(cedula_input)]
    
    if not cliente.empty:
        nombre = cliente.iloc[0]['NOMBRE']
        st.success(f"Bienvenido/a, **{nombre}**")
        
        with st.form("registro_pago"):
            contrato = st.selectbox("Seleccione el contrato a reportar:", cliente['CONTRATO'].tolist())
            valor = st.number_input("Valor pagado (COP):", min_value=0, step=1000)
            fecha = st.date_input("Fecha de realización del pago")
            mes = st.selectbox("Mes correspondiente:", [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ])
            archivo = st.file_uploader("Adjuntar comprobante (JPG, PNG, PDF):", type=['jpg', 'png', 'pdf'])
            
            submit = st.form_submit_button("Enviar Reporte de Pago")
            
            if submit:
                if archivo is not None:
                    # PROCESAMIENTO PROFESIONAL
                    with st.spinner("Enviando reporte al área administrativa..."):
                        
                        # --- INTEGRACIÓN CON GOOGLE SHEETS ---
                        # Aquí incluirás el llamado a tu función de envío:
                        # respuesta = enviar_a_sheets(nombre, contrato, valor, fecha, mes, archivo)
                        
                        # --- MENSAJE DE CONFIRMACIÓN ---
                        st.success("¡Reporte enviado exitosamente!")
                        st.info(f"**Referencia de seguimiento:** {datetime.now().strftime('%Y%m%d%H%M%S')}")
                        st.caption("Hemos recibido su comprobante correctamente. El equipo técnico validará su información en el menor tiempo posible.")
                        
                        if st.button("Realizar nuevo reporte"):
                            st.rerun()
                else:
                    st.warning("Por favor, adjunte el soporte de pago para completar la operación.")
    else:
        st.error("Cédula no encontrada en el sistema. Por favor, verifique el número ingresado.")

# --- FOOTER ---
st.markdown("---")
st.caption("Señal Más | Innovación y Conectividad")
