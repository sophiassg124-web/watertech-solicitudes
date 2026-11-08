from datetime import date, datetime
import csv
import sqlite3
from pathlib import Path
import urllib.parse
import base64

# Importar librerías para Google Sheets
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Watertech | Solicitud de medidores",
    page_icon="💧",
    layout="wide"
)

ASSET_DIR = Path(__file__).resolve().parent

# Función para convertir imágenes a base64
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""

fondo_path = ASSET_DIR / "fondo.png"
fondo_b64 = get_base64_image(fondo_path)

sirius_img_path = ASSET_DIR / "sirius.png"
sirius_b64 = get_base64_image(sirius_img_path)

# --- CONFIGURACIÓN DE BASE DE DATOS Y CSV ---
DATA_DIR = Path.home() / "Documents" / "WatertechSolicitudes"
CSV_PATH = DATA_DIR / "solicitudes_watertech.csv"
DB_PATH = DATA_DIR / "watertech.db"

def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS solicitudes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_solicitud TEXT,
            nombre_completo TEXT,
            empresa TEXT,
            cargo TEXT,
            ciudad_contacto TEXT,
            telefono TEXT,
            correo_electronico TEXT,
            nit TEXT,
            rut_adjunto TEXT,
            tipo_cliente TEXT,
            estado_proyecto TEXT,
            requiere_asesoria TEXT,
            ciudad_proyecto TEXT,
            referencia_normativa TEXT,
            archivo_masivo TEXT,
            detalle_medidores TEXT,
            comentarios TEXT,
            fecha_prevista TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- FUNCIÓN PARA GUARDAR EN GOOGLE SHEETS (USANDO credentials.json LOCAL) ---
def guardar_en_google_sheets(summary_dict):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds_path = ASSET_DIR / "credentials.json"
    
    if creds_path.exists():
        creds = Credentials.from_service_account_file(str(creds_path), scopes=scope)
        client = gspread.authorize(creds)
        
        sheet = client.open("SolicitudesWatertech").sheet1
        
        col_A = sheet.col_values(1)
        
        if not col_A:
            sheet.update('A1', [HEADERS])
            next_row = 2
        else:
            next_row = len(col_A) + 1
            
        fila = [
            summary_dict["Fecha de solicitud"], 
            summary_dict["Nombre completo"], 
            summary_dict["Empresa"],
            summary_dict["Cargo"], 
            summary_dict["Ciudad de contacto"], 
            summary_dict["Teléfono"],
            summary_dict["Correo electrónico"], 
            summary_dict["NIT"], 
            summary_dict["RUT adjunto"],
            summary_dict["Tipo de cliente"], 
            summary_dict["Estado del proyecto"], 
            summary_dict["Requiere asesoría técnica"],
            summary_dict["Ciudad del proyecto"], 
            summary_dict["Referencia normativa"], 
            summary_dict["Archivo masivo adjunto"],
            summary_dict["Detalle de medidores"], 
            summary_dict["Comentarios adicionales"], 
            summary_dict["Fecha prevista de compra/entrega"]
        ]
        
        sheet.update(values=[fila], range_name=f'A{next_row}', value_input_option='USER_ENTERED')
    else:
        raise Exception(f"No se encontró el archivo credentials.json en: {creds_path}")

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

# --- ESTILOS CSS PERSONALIZADOS ---
fondo_css = f"background-image: url('data:image/png;base64,{fondo_b64}'); background-size: cover;" if fondo_b64 else "background-color: #F4F7FA;"

st.markdown(f"""
    <style>
    .stApp {{ {fondo_css} }}
    p, span, label, .stMarkdown, div {{ color: #2C3E50; font-family: 'Segoe UI', sans-serif; }}
    label, div[data-baseweb="checkbox"] span, .stTextInput label, .stSelectbox label, .stFileUploader label, div[data-testid="stTextArea"] label, div[data-testid="stDateInput"] label {{
        font-weight: 800 !important; color: #1E2235 !important;
    }}
    h1, h2, h3, h4 {{ color: #1E2235 !important; font-family: 'Segoe UI', sans-serif; }}
    .diameter-label {{ font-size: 20px !important; font-weight: 800 !important; color: #005A9E !important; padding-top: 25px; display: block; letter-spacing: 0.5px; }}
    div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] {{ margin-bottom: -15px !important; }}
    .hd-image {{ image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges; image-rendering: high-quality; width: 100%; max-width: 360px; height: auto; display: block; margin: 0 auto; }}
    .summary-card {{ background-color: #FFFFFF; border: 1px solid #DCE4EC; padding: 20px 25px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 20px; }}
    .summary-title {{ color: #007ACC; font-size: 17px; font-weight: bold; border-bottom: 2px solid #EAEEF3; padding-bottom: 8px; margin-bottom: 12px; }}
    .summary-row {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #F4F7FA; }}
    .summary-label {{ font-weight: 600; color: #596B82; width: 40%; }}
    .summary-value {{ color: #1E2235; font-weight: 500; width: 60%; text-align: right; }}
    div[data-testid="stSuccess"] {{ display: none !important; }}
    .water-divider {{ display: flex; align-items: center; justify-content: center; margin: 30px auto 20px auto; max-width: 600px; }}
    .water-line {{ flex: 1; height: 2px; background: linear-gradient(to right, transparent, #007ACC, transparent); }}
    .water-icon {{ margin: 0 15px; font-size: 20px; color: #007ACC; background: #FFFFFF; border: 2px solid #007ACC; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(0, 122, 204, 0.2); }}
    .success-box {{ background-color: #FFFFFF; border: 1px solid #DCE4EC; border-left: 5px solid #007ACC; color: #1E2235; padding: 24px 30px; border-radius: 10px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.06); margin: 15px auto 25px auto; max-width: 750px; }}
    .success-title {{ font-size: 22px; font-weight: bold; color: #1E2235 !important; }}
    .whatsapp-container {{ display: flex; justify-content: center; margin-top: 20px; margin-bottom: 20px; }}
    .whatsapp-btn {{ background-color: #25D366; color: white !important; text-align: center; padding: 14px 28px; border-radius: 8px; font-size: 17px; font-weight: bold; text-decoration: none; box-shadow: 0 4px 12px rgba(37, 211, 102, 0.35); transition: background-color 0.3s ease, transform 0.2s ease; display: inline-block; }}
    .whatsapp-btn:hover {{ background-color: #1EBE57; color: white !important; text-decoration: none; transform: translateY(-2px); }}
    div[data-baseweb="calendar"] {{ background-color: #FFFFFF !important; color: #2C3E50 !important; }}
    div[data-baseweb="calendar"] div, div[data-baseweb="calendar"] button, div[data-baseweb="calendar"] span {{ color: #2C3E50 !important; }}
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-baseweb="menu"], div[role="listbox"] {{ background-color: #FFFFFF !important; }}
    input, textarea {{ background-color: #FFFFFF !important; color: #2C3E50 !important; border: 1px solid #DCE4EC !important; border-radius: 4px !important; }}
    div[data-testid="stLinkButton"] > a {{ background-color: #007ACC !important; color: #FFFFFF !important; font-weight: bold !important; border-radius: 5px !important; border: none !important; }}
    div[data-testid="stLinkButton"] > a:hover {{ background-color: #005A9E !important; color: #FFFFFF !important; }}
    div[data-testid="stFileUploader"] section {{ background-color: #FFFFFF !important; border: 1px dashed #007ACC !important; }}
    div[data-testid="stFileUploader"] button {{ background-color: #005A9E !important; color: #FFFFFF !important; font-weight: bold !important; border: none !important; }}
    div[data-testid="stFileUploader"] button p, div[data-testid="stFileUploader"] button span {{ color: #FFFFFF !important; font-weight: bold !important; }}
    div[data-testid="stFileUploader"] small, div[data-testid="stFileUploader"] span[class*="small"] {{ color: #2C3E50 !important; font-weight: 600 !important; }}
    .stButton>button {{ background-color: #007ACC !important; border-radius: 5px; padding: 0.6rem 1.8rem; border: none; }}
    .stButton>button p, .stButton>button span {{ color: #FFFFFF !important; font-size: 18px !important; font-weight: bold !important; }}
    .stButton>button:hover {{ background-color: #005A9E !important; }}
    </style>
""", unsafe_allow_html=True)

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

# --- PASO 3: ESPECIFICACIONES Y DIÁMETROS ---
elif st.session_state.step == 3:
    st.markdown("### Especificaciones de los medidores y Fichas Técnicas")
    st.write("Selecciona diámetros y cantidades, adjunta archivos con tu requerimiento específico en Excel (opcional) y descarga las fichas técnicas.")
    
    pdf_links = {
        "Octave (Ultrasónico)": "https://watertech.com.co/wp-content/uploads/2024/09/CS-A-11-CATALOGO-OCTAVE_V2.pdf",
        "Sonata (Ultrasónico)": "https://watertech.com.co/wp-content/uploads/2024/09/CS-A-10-CATALOGO-SONATA_V2.pdf",
        "Contazara (Ultrasónico)": "https://watertech.com.co/wp-content/uploads/2024/09/CS-A-11-CATALOGO-OCTAVE_V2.pdf",
        "SIRIUS-S R315 (Mecánico/Destacado)": "https://watertech.com.co/wp-content/uploads/2024/09/CS-A-09-CATALOGO-SIRIUS-S_V2.pdf",
        "Sirius R200 (Mecánico)": "https://watertech.com.co/wp-content/uploads/2024/10/CATALOGO-MED-SIRIUS-R200.pdf",
        "Pegasus (Mecánico)": "https://watertech.com.co/wp-content/uploads/2024/09/CS-A-07-CATALOGO-PEGASUS_V2.pdf",
        "Omega-S (Mecánico)": "https://watertech.com.co/wp-content/uploads/2024/10/CS-A-14-CATALOGO-OMEGA-S_V2.pdf",
        "Ara (Mecánico)": "https://watertech.com.co/wp-content/uploads/2024/09/CS-A-04-CATALOGO-ARA_V2.pdf",
        "Venus (Mecánico)": "https://watertech.com.co/wp-content/uploads/2026/05/CS-A-06-CATALOGO-VENUS_V2_unlocked-1.pdf"
    }

    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 1, 2, 1])
    with f_col1:
        cat_ultrasound = st.selectbox(
            "Fichas Técnicas: Ultrasónicos...", 
            ["Octave (Ultrasónico)", "Sonata (Ultrasónico)", "Contazara (Ultrasónico)"], 
            key="cat_ultra"
        )
    with f_col2:
        st.link_button("Ver PDF", pdf_links[cat_ultrasound])
            
    with f_col3:
        cat_mech = st.selectbox(
            "Mecánicos...", 
            ["SIRIUS-S R315 (Mecánico/Destacado)", "Sirius R200 (Mecánico)", "Pegasus (Mecánico)", "Omega-S (Mecánico)", "Ara (Mecánico)", "Venus (Mecánico)"], 
            key="cat_mech"
        )
    with f_col4:
        st.link_button("Ver PDF", pdf_links[cat_mech])

    excel_file = st.file_uploader("📁 Adjuntar archivo de requerimientos en Excel (Opcional)", type=["xlsx", "xls"])
    st.session_state.excel_name = excel_file.name if excel_file else "Ningún archivo seleccionado"

    st.session_state.city_project = st.selectbox("Ciudad del proyecto", list(NORMS.keys()))
    
    st.markdown(f"""
        <div style="background-color: #EAEEF3; border-left: 4px solid #007ACC; padding: 10px 15px; border-radius: 4px; margin: 10px 0;">
            <b>Referencia normativa:</b> {NORMS[st.session_state.city_project]}
        </div>
    """, unsafe_allow_html=True)

    col_table, col_sirius = st.columns([2, 1])

    with col_table:
        st.markdown("<h4 style='color: #007ACC; margin-top: 15px;'>⚙️ SELECCIONA DIÁMETROS Y CANTIDADES</h4>", unsafe_allow_html=True)
        
        st.session_state.meter_selections = []
        for diam in DIAMETERS:
            d_col1, d_col2, d_col3 = st.columns([0.6, 2.2, 2.2])
            with d_col1:
                st.markdown(f"<span class='diameter-label'>{diam}</span>", unsafe_allow_html=True)
            with d_col2:
                m_type = st.selectbox(f"Tipo {diam}", ["No seleccionar", "Mecánico", "Ultrasónico"], key=f"type_{diam}")
            with d_col3:
                qty = st.number_input(f"Cantidad {diam}", min_value=0, max_value=100000, value=0, step=1, key=f"qty_{diam}")
            
            if qty > 0 and m_type != "No seleccionar":
                st.session_state.meter_selections.append(f"{diam}: {m_type} x {qty}")

    with col_sirius:
        st.markdown("""
            <div style="border: 1px solid #DCE4EC; padding: 12px 15px; border-radius: 10px; background-color: #FFFFFF; margin-top: 15px; box-shadow: 0 3px 10px rgba(0,0,0,0.05); text-align: center;">
                <span style="color: #F1C40F; font-weight: bold; font-size: 14px;">⭐</span> 
                <span style="color: #27AE60; font-weight: bold; font-size: 14px;">SIRIUS-S R315 (Destacado)</span>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        
        if sirius_b64:
            st.markdown(f"""
                <div style="text-align: center; margin-bottom: 12px;">
                    <img src="data:image/png;base64,{sirius_b64}" class="hd-image">
                </div>
            """, unsafe_allow_html=True)
        else:
            if sirius_img_path.exists():
                st.image(str(sirius_img_path), width=340)

        st.link_button("📄 Ficha Técnica PDF", "https://watertech.com.co/wp-content/uploads/2024/09/CS-A-09-CATALOGO-SIRIUS-S_V2.pdf", use_container_width=True)

    st.session_state.observations = st.text_area("**Comentarios adicionales para la solicitud**", value=st.session_state.get('observations', ''))

# --- PASO 4: PLANIFICACIÓN ---
elif st.session_state.step == 4:
    st.markdown("### ¡Planifiquemos tu compra!")
    st.write("Para garantizar una entrega oportuna, cuéntanos: ¿para qué fecha tienes prevista la compra o necesitas recibir el producto?")
    
    st.write("Contamos con inventarios permanentes y te acompañamos en la planificación de tu pedido, teniendo en cuenta la disponibilidad, las fechas de calibración requeridas y las etapas logísticas necesarias para garantizar una entrega adecuada.")
    
    selected_date = st.date_input("Fecha prevista de compra o entrega", value=st.session_state.get('delivery_date_obj', date.today()))
    st.session_state.delivery_date_obj = selected_date
    st.session_state.delivery_date = selected_date.strftime("%d/%m/%Y")

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

    st.markdown(f"""
        <div class="summary-card">
            <div class="summary-title">👤 Datos de Contacto y Empresa</div>
            <div class="summary-row"><span class="summary-label">Nombre completo</span><span class="summary-value">{summary_data['Nombre completo'] or '—'}</span></div>
            <div class="summary-row"><span class="summary-label">Empresa</span><span class="summary-value">{summary_data['Empresa'] or '—'}</span></div>
            <div class="summary-row"><span class="summary-label">Cargo</span><span class="summary-value">{summary_data['Cargo'] or '—'}</span></div>
            <div class="summary-row"><span class="summary-label">Ciudad de contacto</span><span class="summary-value">{summary_data['Ciudad de contacto'] or '—'}</span></div>
            <div class="summary-row"><span class="summary-label">Teléfono</span><span class="summary-value">{summary_data['Teléfono'] or '—'}</span></div>
            <div class="summary-row"><span class="summary-label">Correo electrónico</span><span class="summary-value">{summary_data['Correo electrónico'] or '—'}</span></div>
            <div class="summary-row"><span class="summary-label">NIT</span><span class="summary-value">{summary_data['NIT'] or '—'}</span></div>
            <div class="summary-row" style="border-bottom: none;"><span class="summary-label">RUT adjunto</span><span class="summary-value">{summary_data['RUT adjunto']}</span></div>
        </div>

        <div class="summary-card">
            <div class="summary-title">🏗️ Especificaciones del Proyecto</div>
            <div class="summary-row"><span class="summary-label">Tipo de cliente</span><span class="summary-value">{summary_data['Tipo de cliente']}</span></div>
            <div class="summary-row"><span class="summary-label">Estado del proyecto</span><span class="summary-value">{summary_data['Estado del proyecto']}</span></div>
            <div class="summary-row"><span class="summary-label">Asesoría técnica</span><span class="summary-value">{summary_data['Requiere asesoría técnica']}</span></div>
            <div class="summary-row"><span class="summary-label">Ciudad del proyecto</span><span class="summary-value">{summary_data['Ciudad del proyecto']}</span></div>
            <div class="summary-row"><span class="summary-label">Referencia normativa</span><span class="summary-value" style="font-size: 13px;">{summary_data['Referencia normativa']}</span></div>
            <div class="summary-row"><span class="summary-label">Archivo masivo (Excel)</span><span class="summary-value">{summary_data['Archivo masivo adjunto']}</span></div>
            <div class="summary-row"><span class="summary-label">Detalle de medidores</span><span class="summary-value" style="font-weight: bold; color: #007ACC;">{summary_data['Detalle de medidores']}</span></div>
            <div class="summary-row"><span class="summary-label">Comentarios adicionales</span><span class="summary-value">{summary_data['Comentarios adicionales'] or 'Ninguno'}</span></div>
            <div class="summary-row" style="border-bottom: none;"><span class="summary-label">Fecha prevista de entrega</span><span class="summary-value" style="font-weight: bold; color: #27AE60;">{summary_data['Fecha prevista de compra/entrega']}</span></div>
        </div>
    """, unsafe_allow_html=True)

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
                
                # 1. Guardar en Google Sheets (Tiempo real)
                try:
                    guardar_en_google_sheets(summary_data)
                except Exception as gs_err:
                    print(f"Aviso Google Sheets: {gs_err}")

                # 2. Guardar en Base de Datos SQLite Local
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO solicitudes (
                        fecha_solicitud, nombre_completo, empresa, cargo, ciudad_contacto,
                        telefono, correo_electronico, nit, rut_adjunto, tipo_cliente,
                        estado_proyecto, requiere_asesoria, ciudad_proyecto, referencia_normativa,
                        archivo_masivo, detalle_medidores, comentarios, fecha_prevista
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    summary_data["Fecha de solicitud"], summary_data["Nombre completo"], summary_data["Empresa"],
                    summary_data["Cargo"], summary_data["Ciudad de contacto"], summary_data["Teléfono"],
                    summary_data["Correo electrónico"], summary_data["NIT"], summary_data["RUT adjunto"],
                    summary_data["Tipo de cliente"], summary_data["Estado del proyecto"], summary_data["Requiere asesoría técnica"],
                    summary_data["Ciudad del proyecto"], summary_data["Referencia normativa"], summary_data["Archivo masivo adjunto"],
                    summary_data["Detalle de medidores"], summary_data["Comentarios adicionales"], summary_data["Fecha prevista de compra/entrega"]
                ))
                conn.commit()
                conn.close()

                # 3. Guardar respaldo CSV
                exists = CSV_PATH.exists()
                with CSV_PATH.open("a", newline="", encoding="utf-8-sig") as file:
                    writer = csv.DictWriter(file, fieldnames=HEADERS, delimiter=";")
                    if not exists:
                        writer.writeheader()
                    writer.writerow(summary_data)

                # Elemento divisorio elegante con diseño acuático
                st.markdown("""
                    <div class="water-divider">
                        <div class="water-line"></div>
                        <div class="water-icon">💧</div>
                        <div class="water-line"></div>
                    </div>
                """, unsafe_allow_html=True)

                # Tarjeta blanca limpia con el mensaje de éxito
                st.markdown(f"""
                    <div class="success-box">
                        <div class="success-title">¡Solicitud recibida correctamente!</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Mensaje de WhatsApp corporativo sin emojis
                wa_msg = (
                    f"NUEVA SOLICITUD DE MEDIDORES - WATERTECH\n\n"
                    f"Cliente: {summary_data['Nombre completo']}\n"
                    f"Empresa: {summary_data['Empresa']}\n"
                    f"Ciudad: {summary_data['Ciudad del proyecto']}\n"
                    f"RUT Adjunto: {summary_data['RUT adjunto']}\n"
                    f"Medidores: {summary_data['Detalle de medidores']}\n"
                    f"Excel Masivo: {summary_data['Archivo masivo adjunto']}\n"
                    f"Fecha Prevista: {summary_data['Fecha prevista de compra/entrega']}"
                )
                
                wa_url = f"https://api.whatsapp.com/send?phone=573173691029&text={urllib.parse.quote(wa_msg)}"
                
                st.markdown(f"""
                    <div class="whatsapp-container">
                        <a href="{wa_url}" target="_blank" class="whatsapp-btn">
                            Notificar solicitud por WhatsApp ahora
                        </a>
                    </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"No se pudo guardar la solicitud: {e}")

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
            else:
                st.session_state.step += 1
                st.rerun()