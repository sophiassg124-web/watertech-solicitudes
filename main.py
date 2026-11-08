import csv
import streamlit as st
from datetime import date, datetime
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.parse
import base64

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Watertech | Solicitud de medidores",
    page_icon="💧",
    layout="wide"
)

ASSET_DIR = Path(__file__).resolve().parent

# Función para convertir imágenes a base64 y usarlas en CSS si es necesario
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""

fondo_path = ASSET_DIR / "fondo.png"
fondo_b64 = get_base64_image(fondo_path)

# --- ESTILOS CSS PERSONALIZADOS ---
fondo_css = f"background-image: url('data:image/png;base64,{fondo_b64}'); background-size: cover;" if fondo_b64 else "background-color: #F4F7FA;"

st.markdown(f"""
    <style>
    /* Fondo general de la aplicación y textos legibles */
    .stApp {{
        {fondo_css}
    }}
    
    /* Textos generales oscuros y claros para máxima visibilidad */
    p, span, label, .stMarkdown, div {{
        color: #2C3E50;
        font-family: 'Segoe UI', sans-serif;
    }}

    /* FORZAR QUE LAS ETIQUETAS DE LOS CAMPOS ESTÉN EN NEGRITA */
    label, div[data-baseweb="checkbox"] span, .stTextInput label, .stSelectbox label, .stFileUploader label {{
        font-weight: bold !important;
        color: #1E2235 !important;
    }}

    /* Títulos principales */
    h1, h2, h3, h4 {{
        color: #1E2235 !important;
        font-family: 'Segoe UI', sans-serif;
    }}

    /* Banner superior corporativo */
    .header-banner {{
        background-color: #FFFFFF;
        padding: 15px 25px;
        border-bottom: 3px solid #007ACC;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 25px;
        border-radius: 5px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }}

    /* Forzar casillas de texto claras, limpias y blancas */
    input, textarea {{
        background-color: #FFFFFF !important;
        color: #2C3E50 !important;
        border: 1px solid #DCE4EC !important;
        border-radius: 4px !important;
    }}

    /* ESTILO BOTÓN UPLOAD: Azul oscuro, texto blanco, negrita y texto auxiliar visible */
    div[data-testid="stFileUploader"] section {{
        background-color: #FFFFFF !important;
        border: 1px dashed #007ACC !important;
    }}
    div[data-testid="stFileUploader"] button {{
        background-color: #005A9E !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border: none !important;
    }}
    div[data-testid="stFileUploader"] button p, 
    div[data-testid="stFileUploader"] button span {{
        color: #FFFFFF !important;
        font-weight: bold !important;
    }}
    div[data-testid="stFileUploader"] small, 
    div[data-testid="stFileUploader"] span[class*="small"] {{
        color: #2C3E50 !important;
        font-weight: 600 !important;
    }}

    /* CORREGIR MENÚS DESPLEGABLES (SELECTBOX) A FONDO BLANCO Y TEXTO OSCURO */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-baseweb="menu"], div[role="listbox"] {{
        background-color: #FFFFFF !important;
    }}
    div[data-baseweb="menu"] div, ul[data-baseweb="menu"] li, div[role="option"] {{
        color: #2C3E50 !important;
        background-color: #FFFFFF !important;
    }}
    div[data-baseweb="menu"] div:hover, ul[data-baseweb="menu"] li:hover, div[role="option"]:hover {{
        background-color: #EAEEF3 !important;
        color: #007ACC !important;
    }}

    /* Estilo general del botón de navegación */
    .stButton>button {{
        background-color: #007ACC !important;
        border-radius: 5px;
        padding: 0.6rem 1.8rem;
        border: none;
    }}
    
    /* FORZAR QUE EL TEXTO DEL BOTÓN DE NAVEGACIÓN SEA BLANCO Y EN NEGRITA */
    .stButton>button p, .stButton>button span {{
        color: #FFFFFF !important;
        font-size: 18px !important;
        font-weight: bold !important;
    }}

    .stButton>button:hover {{
        background-color: #005A9E !important;
    }}
    
    .stButton>button:hover p, .stButton>button:hover span {{
        color: #FFFFFF !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN DE DATOS Y ESTADOS ---
DATA_DIR = Path.home() / "Documents" / "WatertechSolicitudes"
CSV_PATH = DATA_DIR / "solicitudes_watertech.csv"

EMAIL_REMITENTE = "tu_correo@gmail.com"  
EMAIL_PASSWORD = "tu_contraseña_de_aplicacion" 
EMAIL_DESTINO = "Sandra.gaitan@wtmeters.co"

NORMS = {
    "Bogotá D.C.": "Resolución SIC 69940 de 2025: confirmar aplicabilidad al proyecto. Norma local adicional: por verificar con Watertech.",
    "Medellín": "Resolución SIC 69940 de 2025: confirmar aplicabilidad al proyecto. Norma local adicional: por verificar con Watertech.",
    "Cali": "Resolución SIC 69940 de 2025: confirmar aplicabilidad al proyecto. Norma local adicional: por verificar con Watertech.",
    "Barranquilla": "Resolución SIC 69940 de 2025: confirmar aplicabilidad al proyecto. Norma local adicional: por verificar con Watertech.",
    "Bucaramanga": "Resolución SIC 69940 de 2025: confirmar aplicabilidad al proyecto. Norma local adicional: por verificar con Watertech.",
    "Otra ciudad": "Referencia normativa por verificar con Watertech."
}

DIAMETERS = ['½"', '¾"', '1"', '1½"', '2"', '3"', '4"']
HEADERS = [
    "Fecha de solicitud", "Nombre completo", "Empresa", "Cargo", "Ciudad de contacto",
    "Teléfono", "Correo electrónico", "NIT", "RUT adjunto", "Tipo de cliente", "Estado del proyecto",
    "Requiere asesoría técnica", "Ciudad del proyecto", "Referencia normativa", 
    "Archivo masivo adjunto", "Detalle de medidores", "Comentarios adicionales", "Fecha prevista de compra/entrega"
]

if 'step' not in st.session_state:
    st.session_state.step = 0

# --- ENCABEZADO CON LOGOTIPO OFICIAL ---
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.markdown("<div style='padding-top: 15px;'><span style='color: #007ACC; font-weight: bold; font-size: 14px;'>🛡️ Representantes oficiales ARAD Group | Soporte Técnico Especializado</span></div>", unsafe_allow_html=True)
with header_col2:
    logo_path = ASSET_DIR / "watertech.png"
    if logo_path.exists():
        st.image(str(logo_path), width=180)

st.markdown("<hr style='margin: 5px 0 20px 0;'>", unsafe_allow_html=True)

step_titles = [
    "MEDIDORES DE AGUA", 
    "INFORMACIÓN NORMATIVA", 
    "PASO 1 DE 3: DATOS Y RUT", 
    "PASO 2 DE 3: ESPECIFICACIONES", 
    "PASO 3 DE 3: PLANIFICACIÓN", 
    "REVISIÓN FINAL"
]

st.markdown(f"<h2 style='color: #1E2235; margin-bottom: 15px;'>{step_titles[st.session_state.step]}</h2>", unsafe_allow_html=True)

# --- PASO 0: BIENVENIDA ---
if st.session_state.step == 0:
    st.markdown("### Realiza tu solicitud.")
    st.write("Inicia tu cotización para que el equipo de Watertech conozca tu proyecto y pueda ayudarte a planificar los medidores que necesitas.")
    
    st.markdown("---")
    st.markdown("#### Bienvenido a Watertech")
    st.markdown(
        "✔ Tecnología de vanguardia avalada internacionalmente.<br>"
        "✔ Acompañamiento técnico para proyectos de acueductos, constructoras, industrias, etc.<br>"
        "✔ Inventarios permanentes.", unsafe_allow_html=True
    )
    st.write("Completa los pasos del formulario. Podrás adjuntar archivos con tu requerimiento específico, elegir diámetros, tipos, cantidades y solicitar asesoría especializada.")

# --- PASO 1: NORMATIVA ---
elif st.session_state.step == 1:
    st.markdown("### RESOLUCIÓN 69940")
    st.write("Conoce la normativa técnica metrológica obligatoria y vigente en Colombia.")
    
    st.markdown("""
    Esta norma corresponde al nuevo reglamento técnico, que exige que todo medidor de agua residencial (mecánico, electrónico o ultrasónico) cumpla con estrictos estándares internacionales de precisión para garantizar cobros justos al usuario.
    
    <div style="background-color: #FDEDEC; border-left: 4px solid #E74C3C; padding: 12px; margin: 15px 0; color: #922B21; border-radius: 4px;">
    <b>¡Vender o instalar medidores sin esta certificación ahora es un riesgo crítico que genera altas multas, decomisos y el rechazo de redes de acueducto en todo el país!</b>
    </div>
    
    Antes de realizar cualquier inversión, consulte y verifique la legalidad metrológica de sus proveedores. En Watertech Lassa S.A.S. respaldamos su compra con transparencia absoluta, garantizando que cada uno de sus proyectos fluya con total seguridad jurídica y sin contratiempos ante las autoridades.
    
    <div style="display: inline-block; background-color: rgba(255, 255, 255, 0.85); border: 1.5px solid #007ACC; padding: 8px 14px; border-radius: 5px; margin-top: 10px; margin-bottom: 10px;">
        <a href="https://sedeelectronica.sic.gov.co/sites/default/files/normativa/Resoluci%C3%B3n%20No.%2069940%20del%2012%20de%20septiembre%20de%202025.pdf" target="_blank" style="color: #005A9E; font-size: 15px; font-weight: bold; text-decoration: none;">
            📄 Ver PDF oficial de la Resolución 69940
        </a>
    </div>
    """, unsafe_allow_html=True)

# --- PASO 2: DATOS Y RUT ---
elif st.session_state.step == 2:
    st.markdown("### Cuéntanos sobre tu proyecto")
    st.write("Por favor, ingresa los datos de contacto, tipo de cliente, adjunta tu RUT y el estado actual de tu proyecto.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.nombre = st.text_input("Nombre completo *", value=st.session_state.get('nombre', ''))
        st.session_state.cargo = st.text_input("Cargo *", value=st.session_state.get('cargo', ''))
        st.session_state.telefono = st.text_input("Teléfono *", value=st.session_state.get('telefono', ''))
        st.session_state.nit = st.text_input("NIT de la empresa *", value=st.session_state.get('nit', ''))
    with col2:
        st.session_state.empresa = st.text_input("Empresa *", value=st.session_state.get('empresa', ''))
        st.session_state.ciudad_contacto = st.text_input("Ciudad de contacto *", value=st.session_state.get('ciudad_contacto', ''))
        st.session_state.correo = st.text_input("Correo electrónico *", value=st.session_state.get('correo', ''))
        
        rut_file = st.file_uploader("Adjuntar RUT de la empresa (PDF o Imagen)", type=["pdf", "jpg", "png"])
        st.session_state.rut_name = rut_file.name if rut_file else "Ningún archivo seleccionado"

    st.markdown("---")
    col3, col4 = st.columns(2)
    with col3:
        st.session_state.client_type = st.selectbox("Tipo de cliente", ["Acueducto", "Constructora", "Industria", "Cliente ocasional"])
        st.session_state.project_status = st.selectbox("Estado del proyecto", ["Diseño / Arquitectura", "Licitación en curso", "Obra gris / Instalación", "Ejecución final"])
    with col4:
        st.session_state.advisory = st.checkbox("Requiere visita o asesoría técnica especializada")

# --- PASO 3: ESPECIFICACIONES Y DIÁMETROS (CON TODOS LOS MODELOS ACTUALIZADOS) ---
elif st.session_state.step == 3:
    st.markdown("### Especificaciones de los medidores y Fichas Técnicas")
    st.write("Selecciona diámetros y cantidades, adjunta archivos con tu requerimiento específico en Excel (opcional) y descarga las fichas técnicas.")
    
    # Barra superior con los modelos actualizados (Ultrasónicos y Mecánicos)
    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 1, 2, 1])
    with f_col1:
        cat_ultrasound = st.selectbox(
            "Fichas Técnicas: Ultrasónicos...", 
            ["Octave (Ultrasónico)", "Sonata (Ultrasónico)", "Contazara (Ultrasónico)"], 
            key="cat_ultra"
        )
    with f_col2:
        if cat_ultrasound == "Octave (Ultrasónico)":
            st.link_button("Ver PDF", "https://watertech.com.co/wp-content/uploads/2024/09/CS-A-11-CATALOGO-OCTAVE_V2.pdf")
        elif cat_ultrasound == "Sonata (Ultrasónico)":
            st.link_button("Ver PDF", "https://watertech.com.co/wp-content/uploads/2024/09/CS-A-10-CATALOGO-SONATA_V2.pdf")
        else:
            st.link_button("Ver PDF", "https://watertech.com.co/")
            
    with f_col3:
        cat_mech = st.selectbox(
            "Mecánicos...", 
            ["Sirius R315C (Mecánico/Destacado)", "Sirius R200 (Mecánico)", "Pegasus (Mecánico)", "Omega (Mecánico)", "Ara (Mecánico)", "Venus (Mecánico)"], 
            key="cat_mech"
        )
    with f_col4:
        if cat_mech.startswith("Sirius R315C"):
            st.link_button("Ver PDF", "https://watertech.com.co/wp-content/uploads/2024/09/CS-A-09-CATALOGO-SIRIUS-S_V2.pdf")
        elif cat_mech.startswith("Venus"):
            st.link_button("Ver PDF", "https://watertech.com.co/wp-content/uploads/2026/05/CS-A-06-CATALOGO-VENUS_V2_unlocked-1.pdf")
        else:
            st.link_button("Ver PDF", "https://watertech.com.co/")

    excel_file = st.file_uploader("📁 Adjuntar archivo de requerimientos en Excel (Opcional)", type=["xlsx", "xls"])
    st.session_state.excel_name = excel_file.name if excel_file else "Ningún archivo seleccionado"

    st.session_state.city_project = st.selectbox("Ciudad del proyecto", list(NORMS.keys()))
    st.info(f"**Referencia normativa:** {NORMS[st.session_state.city_project]}")

    # Estructura de dos columnas: Tabla a la izquierda, Panel Sirius a la derecha
    col_table, col_sirius = st.columns([2, 1])

    with col_table:
        st.markdown("<h4 style='color: #007ACC; margin-top: 15px;'>⚙️ SELECCIONA DIÁMETROS Y CANTIDADES</h4>", unsafe_allow_html=True)
        
        st.session_state.meter_selections = []
        for diam in DIAMETERS:
            d_col1, d_col2, d_col3 = st.columns([1, 2, 2])
            with d_col1:
                st.markdown(f"**{diam}**")
            with d_col2:
                m_type = st.selectbox(f"Tipo {diam}", ["No seleccionar", "Mecánico", "Ultrasónico"], key=f"type_{diam}")
            with d_col3:
                qty = st.number_input(f"Cantidad {diam}", min_value=0, max_value=100000, value=0, step=1, key=f"qty_{diam}")
            
            if qty > 0 and m_type != "No seleccionar":
                st.session_state.meter_selections.append(f"{diam}: {m_type} x {qty}")

    with col_sirius:
        st.markdown("""
            <div style="border: 1px solid #007ACC; padding: 15px; border-radius: 8px; background-color: #FAFAFA; margin-top: 40px;">
                <span style="color: #27AE60; font-weight: bold;">⭐ Destacado</span><br>
                <b style="font-size: 18px; color: #1E2235;">Sirius R315C</b>
        """, unsafe_allow_html=True)
        
        sirius_path = ASSET_DIR / "sirius.png"
        if sirius_path.exists():
            st.image(str(sirius_path), width=200)
        
        st.markdown("""
            <p style="font-size: 13px; color: #4A607A;">Máxima precisión metrológica.</p>
            <a href="https://watertech.com.co/wp-content/uploads/2024/09/CS-A-09-CATALOGO-SIRIUS-S_V2.pdf" target="_blank" style="color: #007ACC; font-weight: bold;">Ficha Técnica PDF</a>
            </div>
        """, unsafe_allow_html=True)

    st.session_state.observations = st.text_area("Comentarios adicionales para la solicitud", value=st.session_state.get('observations', ''))

# --- PASO 4: PLANIFICACIÓN ---
elif st.session_state.step == 4:
    st.markdown("### ¡Planifiquemos tu compra!")
    st.write("Para garantizar una entrega oportuna, cuéntanos: ¿para qué fecha tienes prevista la compra o necesitas recibir el producto?")
    
    st.write("Contamos con inventarios permanentes y te acompañamos en la planificación de tu pedido, teniendo en cuenta la disponibilidad, las fechas de calibración requeridas y las etapas logísticas necesarias para garantizar una entrega adecuada.")
    
    st.session_state.delivery_date = st.text_input("Fecha prevista de compra o entrega (DD/MM/AAAA)", value=st.session_state.get('delivery_date', date.today().strftime("%d/%m/%Y")))

# --- PASO 5: REVISIÓN Y ENVÍO ---
elif st.session_state.step == 5:
    st.markdown("### Revisa y confirma")
    st.write("Verifica los datos antes de enviar tu solicitud.")
    
    summary_data = {
        "Fecha de solicitud": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Nombre completo": st.session_state.get('nombre', ''),
        "Empresa": st.session_state.get('empresa', ''),
        "Cargo": st.session_state.get('cargo', ''),
        "Ciudad de contacto": st.session_state.get('ciudad_contacto', ''),
        "Teléfono": st.session_state.get('telefono', ''),
        "Correo electrónico": st.session_state.get('correo', ''),
        "NIT": st.session_state.get('nit', ''),
        "RUT adjunto": st.session_state.get('rut_name', 'Ninguno'),
        "Tipo de cliente": st.session_state.get('client_type', ''),
        "Estado del proyecto": st.session_state.get('project_status', ''),
        "Requiere asesoría técnica": "Sí" if st.session_state.get('advisory', False) else "No",
        "Ciudad del proyecto": st.session_state.get('city_project', ''),
        "Referencia normativa": NORMS.get(st.session_state.get('city_project', ''), ''),
        "Archivo masivo adjunto": st.session_state.get('excel_name', 'Ninguno'),
        "Detalle de medidores": " | ".join(st.session_state.get('meter_selections', [])) if st.session_state.get('meter_selections', []) else "Ver archivo Excel adjunto",
        "Comentarios adicionales": st.session_state.get('observations', ''),
        "Fecha prevista de compra/entrega": st.session_state.get('delivery_date', '')
    }

    for k, v in summary_data.items():
        if k != "Fecha de solicitud":
            st.markdown(f"**{k}:** {v if v else '—'}")

    st.markdown("---")
    if st.button("Confirmar solicitud ✓", type="primary"):
        if not summary_data["Nombre completo"] or not summary_data["Correo electrónico"] or not summary_data["NIT"] or not summary_data["Empresa"] or not summary_data["Cargo"] or not summary_data["Ciudad de contacto"] or not summary_data["Teléfono"]:
            st.markdown("""
                <div style="background-color: #FDEDEC; border-left: 4px solid #E74C3C; padding: 12px; margin: 15px 0; color: #C0392B; border-radius: 4px; font-weight: bold;">
                    Por favor completa todos los campos obligatorios de contacto antes de confirmar.
                </div>
            """, unsafe_allow_html=True)
        else:
            try:
                DATA_DIR.mkdir(parents=True, exist_ok=True)
                exists = CSV_PATH.exists()
                with CSV_PATH.open("a", newline="", encoding="utf-8-sig") as file:
                    writer = csv.DictWriter(file, fieldnames=HEADERS, delimiter=";")
                    if not exists:
                        writer.writeheader()
                    writer.writerow(summary_data)
                
                # Envío de correo
                try:
                    msg = MIMEMultipart()
                    msg['From'] = EMAIL_REMITENTE
                    msg['To'] = EMAIL_DESTINO
                    msg['Subject'] = f"Nueva Solicitud Web - {summary_data['Empresa']} ({summary_data['Ciudad del proyecto']})"
                    cuerpo_correo = f"NUEVA SOLICITUD WEB - WATERTECH\n\n" + "\n".join([f"- {k}: {v}" for k, v in summary_data.items()])
                    msg.attach(MIMEText(cuerpo_correo, 'plain', 'utf-8'))
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(EMAIL_REMITENTE, EMAIL_PASSWORD)
                    server.sendmail(EMAIL_REMITENTE, EMAIL_DESTINO, msg.as_string())
                    server.quit()
                except Exception as mail_err:
                    print(f"Aviso correo: {mail_err}")

                st.success(f"¡Solicitud recibida correctamente!\n\nLos datos se guardaron en:\n{CSV_PATH}")
                
                wa_msg = f"*NUEVA SOLICITUD DE MEDIDORES - WATERTECH*\n\n👤 *Cliente:* {summary_data['Nombre completo']}\n🏢 *Empresa:* {summary_data['Empresa']}\n📍 *Ciudad:* {summary_data['Ciudad del proyecto']}\n📦 *Medidores:* {summary_data['Detalle de medidores']}"
                wa_url = f"https://api.whatsapp.com/send?phone=573173691029&text={urllib.parse.quote(wa_msg)}"
                st.markdown(f"👉 [Hacer clic aquí para notificar por WhatsApp]({wa_url})", unsafe_allow_html=True)
                st.balloons()
            except Exception as e:
                st.error(f"No se pudo guardar: {e}")

# --- BOTONES DE NAVEGACIÓN INFERIORES ---
col_back, col_next = st.columns([1, 1])

with col_back:
    if st.session_state.step > 0:
        if st.button("← Anterior"):
            st.session_state.step -= 1
            st.rerun()

with col_next:
    if st.session_state.step < len(step_titles) - 1:
        if st.button("Siguiente →"):
            # Validación Paso 2 (Datos obligatorios)
            if st.session_state.step == 2:
                if not st.session_state.get('nombre') or not st.session_state.get('correo') or not st.session_state.get('nit') or not st.session_state.get('empresa') or not st.session_state.get('cargo') or not st.session_state.get('ciudad_contacto') or not st.session_state.get('telefono'):
                    st.markdown("""
                        <div style="background-color: #FDEDEC; border-left: 4px solid #E74C3C; padding: 12px; margin: 15px 0; color: #C0392B; border-radius: 4px; font-weight: bold;">
                            Por favor completa todos los campos obligatorios antes de continuar.
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.session_state.step += 1
                    st.rerun()
            
            # Validación Paso 3 (Especificaciones y medidores obligatorios)
            elif st.session_state.step == 3:
                selections = st.session_state.get('meter_selections', [])
                has_excel = bool(st.session_state.get('excel_name') and st.session_state.get('excel_name') != "Ningún archivo seleccionado")
                
                if not selections and not has_excel:
                    st.markdown("""
                        <div style="background-color: #FDEDEC; border-left: 4px solid #E74C3C; padding: 12px; margin: 15px 0; color: #C0392B; border-radius: 4px; font-weight: bold;">
                            Por favor selecciona al menos un medidor con su respectiva cantidad o adjunta un archivo en Excel antes de continuar.
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.session_state.step += 1
                    st.rerun()
            else:
                st.session_state.step += 1
                st.rerun()