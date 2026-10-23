
import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.request
import json
import time

# Configuración de la página web de Streamlit
st.set_page_config(page_title="Slot Telemetry Control", layout="wide")
st.title("🏎️ Slot Control & Telemetry")

# --- 1. CONEXIÓN SEGURA CON SUPABASE ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    SUPABASE_URL = "https://supabase.co"
    SUPABASE_KEY = "sb_publishable_8CCHsKMSd6VwkGa4x25eDQ_px3Ju8or"

# Aseguramos que la URL base no termine en barra para no duplicar
if SUPABASE_URL.endswith('/'):
    SUPABASE_URL = SUPABASE_URL[:-1]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
    "Cache-Control": "no-cache"
}

def leer_tabla_supabase(tabla_nombre):
    url = f"{SUPABASE_URL}/rest/v1/{tabla_nombre}?select=*"
    try:
        req = urllib.request.Request(url, headers=HEADERS, method="GET")
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                datos = json.loads(response.read().decode())
                if len(datos) > 0:
                    return pd.DataFrame(datos)
    except Exception:
        pass
    return pd.DataFrame()

def enviar_datos_supabase(tabla_nombre, payload):
    url = f"{SUPABASE_URL}/rest/v1/{tabla_nombre}"
    try:
        data_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data_bytes, headers=HEADERS, method="POST")
        with urllib.request.urlopen(req) as response:
            if response.status == 201 or response.status == 200:
                return True, "Guardado con éxito"
            return False, f"Error del servidor: Código {response.status}"
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode()
        if e.code == 307 or e.code == 308 or "Redirecting" in error_msg:
            try:
                url_correcta = f"{SUPABASE_URL}/rest/v1/{tabla_nombre}/"
                req_alt = urllib.request.Request(url_correcta, data=data_bytes, headers=HEADERS, method="POST")
                with urllib.request.urlopen(req_alt) as resp_alt:
                    if resp_alt.status == 201 or resp_alt.status == 200:
                        return True, "Guardado con éxito (Ruta corregida)"
            except Exception as inner_e:
                return False, f"Fallo en redirección: {str(inner_e)}"
        return False, f"Detalle Base de Datos (Código {e.code}): {error_msg}"
    except Exception as e:
        return False, f"Error de conexión: {str(e)}"

# Descarga previa de datos de la nube
df_coches_raw = leer_tabla_supabase("coches")
df_pilotos_raw = leer_tabla_supabase("pilotos")
df_piezas_raw = leer_tabla_supabase("piezas_recambios")
df_carreras_raw = leer_tabla_supabase("carreras")
df_mantenimiento_raw = leer_tabla_supabase("mantenimiento")

lista_coches = [f"{row['id_coche']} - {row['modelo']} ({row['marca']})" for _, row in df_coches_raw.iterrows()] if not df_coches_raw.empty else []
lista_pilotos = [f"{row['id_piloto']} - {row['piloto']}" for _, row in df_pilotos_raw.iterrows()] if not df_pilotos_raw.empty else []

pestana_coches, pestana_pilotos, pestana_piezas, pestana_carreras, pestana_maint = st.tabs([
    "🏎️ Panel de Coches", "👤 Pilotos", "🔧 Piezas", "🏁 Carreras", "🛠️ Mantenimiento"
])

st.sidebar.header("🛠️ Panel de Control (Boxes)")
opcion_formulario = st.sidebar.radio(
    "¿Qué deseas registrar?", 
    ["Añadir Coche 🚗", "Añadir Piloto 👤", "Añadir Carrera 🏁"]
)

if opcion_formulario == "Añadir Coche 🚗":
    st.sidebar.subheader("Nuevo Coche de Slot")
    modelo = st.sidebar.text_input("Modelo del coche")
    marca = st.sidebar.selectbox("Marca", ["Scaleauto", "Slot.it", "NSR", "Black Arrow", "Carrera", "Scalextric", "SRC", "Otro"])
    categoria = st.sidebar.selectbox("Categoría", ["GT3", "LMP", "Clásicos", "Rally", "Fórmula 1", "Grupo C"])
    precio_compra = st.sidebar.number_input("Precio de compra (€)", min_value=0.0, step=0.5)
    
    if st.sidebar.button("Guardar Coche en la Nube"):
        if modelo.strip() != "":
            payload = {
                "modelo": modelo, 
                "marca": marca, 
                "categoria": categoria, 
                "precio_compra": precio_compra
            }
            status, msg = enviar_datos_supabase("coches", payload)
            if status:
                st.sidebar.success(msg)
                time.sleep(0.5)  
                st.rerun()
            else:
                st.sidebar.error(msg)

elif opcion_formulario == "Añadir Piloto 👤":
    st.sidebar.subheader("Nuevo Piloto")
    nombre_piloto = st.sidebar.text_input("Nombre del piloto")
    club_piloto = st.sidebar.text_input("Club / Escudería")
    
    if st.sidebar.button("Guardar Piloto en la Nube"):
        if nombre_piloto.strip() != "":
            payload = {
                "piloto": nombre_piloto, 
                "club": club_piloto
            }
            status, msg = enviar_datos_supabase("pilotos", payload)
            if status:
                st.sidebar.success(msg)
                time.sleep(0.5)  
                st.rerun()
            else:
                st.sidebar.error(msg)

elif opcion_formulario == "Añadir Carrera 🏁":
    st.sidebar.subheader("Registro de Sesión / Carrera")
    if not lista_coches or not lista_pilotos:
        st.sidebar.warning("⚠️ Necesitas registrar al menos un coche y un piloto antes de añadir una carrera.")
    else:
        coche_sel = st.sidebar.selectbox("Coche que corrió", lista_coches)
        piloto_sel = st.sidebar.selectbox("Piloto", lista_pilotos)
        circuito = st.sidebar.selectbox("Circuito", ["Bsz", "Amore", "Delta", "Otro"])
        vueltas = st.sidebar.number_input("Vueltas completadas", min_value=0, step=1)
        vuelta_rapida = st.sidebar.number_input("Tiempo Vuelta Rápida (s)", min_value=0.0, format="%.3f")
        
        if st.sidebar.button("Guardar Telemetría"):
            id_coche = int(coche_sel.split(" - ")[0])
            id_piloto = int(piloto_sel.split(" - ")[0])
            payload = {
                "id_coche": id_coche, 
                "vueltas": vueltas, 
                "vuelta_rapida": vuelta_rapida, 
                "id_piloto": id_piloto, 
                "circuito": circuito
            }
            status, msg = enviar_datos_supabase("carreras", payload)
            if status:
                st.sidebar.success(msg)
                time.sleep(0.5)  
                st.rerun()
            else:
                st.sidebar.error(msg)

with pestana_coches:
    st.header("🗂️ Mi Garaje de Slot")
    if not df_coches_raw.empty:
        st.dataframe(df_coches_raw, use_container_width=True)
    else:
        st.info("No hay vehículos guardados en el garaje todavía.")

with pestana_pilotos:
    st.header("👤 Plantilla de Pilotos")
    if not df_pilotos_raw.empty:
        st.dataframe(df_pilotos_raw, use_container_width=True)
    else:
        st.info("Aún no has registrado ningún piloto.")

with pestana_piezas:
    st.header("🔧 Gestión de Componentes e Inventario")
    if not df_piezas_raw.empty:
        st.dataframe(df_piezas_raw, use_container_width=True)
    else:
        st.info("El inventario de piezas está vacío.")

with pestana_carreras:
    st.header("🏁 Cuadro de Telemetría de Carreras")
    if not df_carreras_raw.empty:
        st.dataframe(df_carreras_raw, use_container_width=True)
    else:
        st.info("No se han registrado sesiones ni telemetrías de carreras.")

with pestana_maint:
    st.header("🛠️ Historial del Taller mecánico")
    if not df_mantenimiento_raw.empty:
        st.dataframe(df_mantenimiento_raw, use_container_width=True)
    else:
        st.info("Mecánica al día. Ningún vehículo ha requerido entrar a boxes todavía.")
