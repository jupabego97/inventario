import streamlit as st
import pandas as pd
import threading
import os
import requests
from datetime import datetime, date

# Configuración de la página
st.set_page_config(
    page_title="Inventario Scanner - Alegra",
    page_icon="📦",
    layout="centered"
)

# ========== ESTILOS CSS Y JAVASCRIPT ==========

st.markdown("""
<style>
/* Indicadores visuales de diferencia */
.diff-ok {
    background: linear-gradient(135deg, #00c853 0%, #69f0ae 100%);
    color: white;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    font-size: 24px;
    font-weight: bold;
    box-shadow: 0 4px 15px rgba(0, 200, 83, 0.4);
    animation: pulse-green 2s infinite;
}

.diff-warning {
    background: linear-gradient(135deg, #ff9800 0%, #ffcc02 100%);
    color: white;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    font-size: 24px;
    font-weight: bold;
    box-shadow: 0 4px 15px rgba(255, 152, 0, 0.4);
    animation: pulse-yellow 2s infinite;
}

.diff-danger {
    background: linear-gradient(135deg, #f44336 0%, #ff5252 100%);
    color: white;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    font-size: 24px;
    font-weight: bold;
    box-shadow: 0 4px 15px rgba(244, 67, 54, 0.4);
    animation: pulse-red 2s infinite;
}

@keyframes pulse-green {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.02); }
}

@keyframes pulse-yellow {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.02); }
}

@keyframes pulse-red {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.02); }
}

/* Historial de sesión */
.historial-item {
    background: #f8f9fa;
    border-left: 4px solid #007bff;
    padding: 10px 15px;
    margin: 5px 0;
    border-radius: 0 8px 8px 0;
    font-size: 14px;
}

.historial-item.success {
    border-left-color: #28a745;
}

.historial-item.warning {
    border-left-color: #ffc107;
}

/* Contador de progreso grande */
.progress-big {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px 25px;
    border-radius: 15px;
    text-align: center;
    margin: 10px 0;
}

.progress-big .number {
    font-size: 36px;
    font-weight: bold;
}

.progress-big .label {
    font-size: 14px;
    opacity: 0.9;
}

/* Modo rápido activo */
.modo-rapido-activo {
    background: linear-gradient(135deg, #00b4db 0%, #0083b0 100%);
    color: white;
    padding: 10px 20px;
    border-radius: 25px;
    text-align: center;
    font-weight: bold;
    margin: 10px 0;
}

/* Input numérico móvil */
input[type="number"] {
    font-size: 32px !important;
    text-align: center !important;
    padding: 15px !important;
    height: 70px !important;
}

/* Inputs de texto grandes (código de barras y nombre) */
.stTextInput input {
    font-size: 24px !important;
    padding: 15px 20px !important;
    height: 60px !important;
    border-radius: 10px !important;
}

/* Input de cantidad extra grande */
.big-number-input input[type="number"] {
    font-size: 48px !important;
    height: 90px !important;
    font-weight: bold !important;
}

/* Tarjeta de producto seleccionable */
.producto-card {
    background: white;
    border: 2px solid #e0e0e0;
    border-radius: 12px;
    padding: 15px 20px;
    margin: 8px 0;
    cursor: pointer;
    transition: all 0.2s ease;
}

.producto-card:hover {
    border-color: #667eea;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    transform: translateY(-2px);
}

.producto-card .nombre {
    font-size: 16px;
    font-weight: bold;
    color: #333;
    margin-bottom: 5px;
}

.producto-card .info {
    font-size: 13px;
    color: #666;
}

/* Atajos de teclado tooltip */
.keyboard-hint {
    background: #e9ecef;
    color: #495057;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-family: monospace;
}
</style>
""", unsafe_allow_html=True)

# JavaScript para auto-focus, sonidos y atajos de teclado
st.markdown("""
<script>
// Auto-focus en el campo de código de barras
document.addEventListener('DOMContentLoaded', function() {
    const barcodeInput = document.querySelector('input[data-testid="stTextInput"]');
    if (barcodeInput) {
        barcodeInput.focus();
    }
});

// Función para reproducir sonidos (usando Web Audio API)
function playSound(type) {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    if (type === 'success') {
        oscillator.frequency.setValueAtTime(880, audioContext.currentTime);
        oscillator.frequency.setValueAtTime(1100, audioContext.currentTime + 0.1);
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.3);
    } else if (type === 'error') {
        oscillator.frequency.setValueAtTime(300, audioContext.currentTime);
        oscillator.frequency.setValueAtTime(200, audioContext.currentTime + 0.2);
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.4);
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.4);
    } else if (type === 'warning') {
        oscillator.frequency.setValueAtTime(500, audioContext.currentTime);
        gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.2);
    }
}
</script>
""", unsafe_allow_html=True)


# ========== CONFIGURACIÓN ==========

ARCHIVO_INVENTARIO = "inventario.csv"
ARCHIVO_LOG = "log_ajustes.csv"
LOCK = threading.Lock()

# Columnas del CSV
COL_CODIGO = "Codigo"
COL_NOMBRE = "Nombre"
COL_STOCK = "Cantidad inicial en bodega: Principal"
COL_BARRAS = "Codigo de barras"
COL_CANTIDAD_ACTUAL = "cantidad_actual"

# API Alegra
ALEGRA_API_URL = "https://api.alegra.com/api/v1"
ALEGRA_API_KEY = os.getenv(
    "ALEGRA_API_KEY",
    "bmFub3Ryb25pY3NhbHNvbmRlbGF0ZWNub2xvZ2lhQGdtYWlsLmNvbTphMmM4OTA3YjE1M2VmYTc0ODE5ZA=="
)
WAREHOUSE_ID = 1

# ========== INICIALIZAR SESSION STATE ==========

if "historial_sesion" not in st.session_state:
    st.session_state.historial_sesion = []

if "modo_rapido" not in st.session_state:
    st.session_state.modo_rapido = False

if "ultimo_producto" not in st.session_state:
    st.session_state.ultimo_producto = None

if "buscar_por" not in st.session_state:
    st.session_state.buscar_por = "codigo_barras"

if "auto_submit" not in st.session_state:
    st.session_state.auto_submit = True

if "sonidos_activos" not in st.session_state:
    st.session_state.sonidos_activos = True

if "codigo_actual" not in st.session_state:
    st.session_state.codigo_actual = ""

if "producto_seleccionado" not in st.session_state:
    st.session_state.producto_seleccionado = None

if "mostrar_opciones_nombre" not in st.session_state:
    st.session_state.mostrar_opciones_nombre = False


# ========== FUNCIONES DE API ALEGRA ==========

def consultar_item_alegra(item_id):
    """Consulta un item en la API de Alegra."""
    try:
        url = f"{ALEGRA_API_URL}/items/{item_id}"
        headers = {
            "accept": "application/json",
            "authorization": f"Basic {ALEGRA_API_KEY}"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error al consultar Alegra: {e}")
        return None


def crear_ajuste_inventario(item_id, tipo, cantidad, costo):
    """Crea un ajuste de inventario en Alegra."""
    try:
        url = f"{ALEGRA_API_URL}/inventory-adjustments"
        headers = {
            "accept": "application/json",
            "authorization": f"Basic {ALEGRA_API_KEY}",
            "content-type": "application/json"
        }
        payload = {
            "date": date.today().isoformat(),
            "warehouse": {"id": str(WAREHOUSE_ID)},
            "items": [{
                "id": str(item_id),
                "type": tipo,
                "quantity": float(cantidad),
                "unitCost": float(costo) if costo else 0
            }]
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error al crear ajuste en Alegra: {e}")
        return None


def extraer_datos_item(item_data):
    """Extrae los datos relevantes de la respuesta de la API de Alegra."""
    if not item_data:
        return None
    
    nombre = item_data.get("name", "Sin nombre")
    inventory = item_data.get("inventory", {})
    cantidad_disponible = inventory.get("availableQuantity", 0)
    costo_unitario = inventory.get("unitCost", 0)
    
    price_list = item_data.get("price", [])
    precio = 0
    if price_list and len(price_list) > 0:
        precio = price_list[0].get("price", 0)
    
    return {
        "nombre": nombre,
        "cantidad_disponible": float(cantidad_disponible) if cantidad_disponible else 0,
        "costo_unitario": float(costo_unitario) if costo_unitario else 0,
        "precio": float(precio) if precio else 0
    }


# ========== FUNCIONES DE LOG ==========

def guardar_log_ajuste(codigo_barras, item_id, nombre, precio, cantidad_anterior, cantidad_nueva, diferencia, tipo_ajuste):
    """Guarda un registro en el log de ajustes."""
    log_entry = {
        "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "codigo_barras": codigo_barras,
        "id_alegra": item_id,
        "nombre": nombre,
        "precio": precio,
        "cantidad_anterior": cantidad_anterior,
        "cantidad_nueva": cantidad_nueva,
        "diferencia": diferencia,
        "tipo_ajuste": tipo_ajuste
    }
    
    with LOCK:
        if os.path.exists(ARCHIVO_LOG):
            df_log = pd.read_csv(ARCHIVO_LOG)
            df_log = pd.concat([df_log, pd.DataFrame([log_entry])], ignore_index=True)
        else:
            df_log = pd.DataFrame([log_entry])
        
        df_log.to_csv(ARCHIVO_LOG, index=False)


def cargar_log():
    """Carga el log de ajustes si existe."""
    if os.path.exists(ARCHIVO_LOG):
        try:
            return pd.read_csv(ARCHIVO_LOG)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


# ========== FUNCIONES DE HISTORIAL DE SESIÓN ==========

def agregar_al_historial(codigo_barras, nombre, cantidad_alegra, cantidad_contada, estado):
    """Agrega un producto al historial de la sesión actual."""
    entry = {
        "hora": datetime.now().strftime("%H:%M:%S"),
        "codigo_barras": codigo_barras,
        "nombre": nombre[:30] + "..." if len(nombre) > 30 else nombre,
        "cantidad_alegra": cantidad_alegra,
        "cantidad_contada": cantidad_contada,
        "estado": estado  # "ok", "ajustado", "error"
    }
    st.session_state.historial_sesion.insert(0, entry)
    # Mantener solo los últimos 50
    if len(st.session_state.historial_sesion) > 50:
        st.session_state.historial_sesion = st.session_state.historial_sesion[:50]


# ========== FUNCIONES DE DATOS LOCALES ==========

def cargar_datos():
    """Carga los datos del CSV si existe"""
    if os.path.exists(ARCHIVO_INVENTARIO):
        try:
            df = pd.read_csv(ARCHIVO_INVENTARIO, sep=";", dtype={COL_BARRAS: str, COL_CODIGO: str})
            df[COL_BARRAS] = df[COL_BARRAS].astype(str).str.strip()
            df[COL_CODIGO] = df[COL_CODIGO].astype(str).str.strip()
            if COL_CANTIDAD_ACTUAL not in df.columns:
                df[COL_CANTIDAD_ACTUAL] = ""
            return df
        except Exception as e:
            st.error(f"Error al cargar el archivo: {e}")
            return None
    return None


def guardar_datos(df):
    """Guarda los datos al CSV con bloqueo para concurrencia"""
    with LOCK:
        df.to_csv(ARCHIVO_INVENTARIO, sep=";", index=False)


def buscar_producto(df, termino_busqueda, tipo_busqueda="codigo_barras"):
    """Busca un producto por código de barras o por nombre"""
    termino = str(termino_busqueda).strip()
    
    if tipo_busqueda == "codigo_barras":
        resultado = df[df[COL_BARRAS] == termino]
        if not resultado.empty:
            return resultado.index[0], resultado.iloc[0]
    else:  # buscar por nombre - no retorna nada, usa buscar_productos_por_nombre
        pass
    
    return None, None


def buscar_productos_por_nombre(df, termino_busqueda, limite=10):
    """Busca productos que contengan el término en el nombre y retorna múltiples resultados."""
    termino = str(termino_busqueda).strip()
    if not termino or len(termino) < 2:
        return pd.DataFrame()
    
    # Buscar coincidencias parciales
    resultado = df[df[COL_NOMBRE].str.contains(termino, case=False, na=False)]
    return resultado.head(limite)


def procesar_archivo_subido(archivo):
    """Procesa el archivo subido y lo guarda"""
    try:
        if archivo.name.endswith('.csv'):
            contenido = archivo.getvalue().decode('utf-8')
            if ';' in contenido[:1000]:
                df = pd.read_csv(archivo, sep=";", dtype={COL_BARRAS: str, COL_CODIGO: str})
            else:
                df = pd.read_csv(archivo, dtype={COL_BARRAS: str, COL_CODIGO: str})
        else:
            df = pd.read_excel(archivo, dtype={COL_BARRAS: str, COL_CODIGO: str})
        
        columnas_requeridas = [COL_CODIGO, COL_BARRAS]
        columnas_faltantes = [c for c in columnas_requeridas if c not in df.columns]
        
        if columnas_faltantes:
            st.error(f"Faltan columnas requeridas: {columnas_faltantes}")
            return False
        
        df[COL_BARRAS] = df[COL_BARRAS].astype(str).str.strip()
        df[COL_CODIGO] = df[COL_CODIGO].astype(str).str.strip()
        
        if COL_CANTIDAD_ACTUAL not in df.columns:
            df[COL_CANTIDAD_ACTUAL] = ""
        
        guardar_datos(df)
        return True
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        return False


# ========== FUNCIONES DE UI ==========

def mostrar_indicador_diferencia(diferencia):
    """Muestra un indicador visual grande según la diferencia."""
    abs_diff = abs(diferencia)
    
    if diferencia == 0:
        st.markdown("""
        <div class="diff-ok">
            ✅ COINCIDE<br>
            <small>El conteo es igual al stock</small>
        </div>
        """, unsafe_allow_html=True)
    elif abs_diff <= 2:
        signo = "+" if diferencia > 0 else ""
        st.markdown(f"""
        <div class="diff-warning">
            ⚠️ DIFERENCIA: {signo}{diferencia:.0f}<br>
            <small>Pequeña diferencia detectada</small>
        </div>
        """, unsafe_allow_html=True)
    else:
        signo = "+" if diferencia > 0 else ""
        st.markdown(f"""
        <div class="diff-danger">
            🚨 DIFERENCIA: {signo}{diferencia:.0f}<br>
            <small>Diferencia significativa</small>
        </div>
        """, unsafe_allow_html=True)


def mostrar_historial_sesion():
    """Muestra el historial de productos escaneados en la sesión."""
    if not st.session_state.historial_sesion:
        st.info("No hay productos escaneados en esta sesión")
        return
    
    for item in st.session_state.historial_sesion[:10]:  # Mostrar últimos 10
        estado_color = {
            "ok": "success",
            "ajustado": "warning",
            "error": ""
        }.get(item["estado"], "")
        
        diferencia = item["cantidad_contada"] - item["cantidad_alegra"]
        diff_texto = f"({'+' if diferencia > 0 else ''}{diferencia:.0f})" if diferencia != 0 else "(=)"
        
        st.markdown(f"""
        <div class="historial-item {estado_color}">
            <strong>{item['hora']}</strong> - {item['nombre']}<br>
            <small>📊 Alegra: {item['cantidad_alegra']:.0f} → Contado: {item['cantidad_contada']:.0f} {diff_texto}</small>
        </div>
        """, unsafe_allow_html=True)


def limpiar_para_nuevo_escaneo():
    """Limpia el estado para un nuevo escaneo."""
    if "mostrar_confirmacion" in st.session_state:
        del st.session_state.mostrar_confirmacion
    if "datos_ajuste" in st.session_state:
        del st.session_state.datos_ajuste
    st.session_state.codigo_actual = ""
    st.session_state.producto_seleccionado = None


# ========== INTERFAZ PRINCIPAL ==========

st.title("📦 Inventario Scanner")
st.markdown("Escanea códigos de barras para actualizar inventario en **Alegra** en tiempo real")

# Sidebar para administración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Toggle de modo rápido
    st.session_state.modo_rapido = st.toggle(
        "⚡ Modo Conteo Rápido",
        value=st.session_state.modo_rapido,
        help="Auto-guarda al confirmar y limpia para el siguiente escaneo"
    )
    
    if st.session_state.modo_rapido:
        st.markdown('<div class="modo-rapido-activo">🚀 MODO RÁPIDO ACTIVO</div>', unsafe_allow_html=True)
    
    st.session_state.sonidos_activos = st.toggle(
        "🔊 Sonidos de confirmación",
        value=st.session_state.sonidos_activos,
        help="Reproduce sonidos al encontrar/no encontrar productos"
    )
    
    st.divider()
    
    # Subir archivo
    archivo_subido = st.file_uploader(
        "📁 Subir inventario",
        type=['csv', 'xlsx'],
        help="Sube el archivo CSV o Excel con el inventario"
    )
    
    if archivo_subido:
        if st.button("📤 Cargar archivo", type="primary"):
            with st.spinner("Procesando archivo..."):
                if procesar_archivo_subido(archivo_subido):
                    st.success("✅ Archivo cargado")
                    st.rerun()
    
    st.divider()
    
    # Contador de progreso grande
    df = cargar_datos()
    if df is not None:
        total_productos = len(df)
        productos_contados = df[COL_CANTIDAD_ACTUAL].notna() & (df[COL_CANTIDAD_ACTUAL] != "")
        contados = productos_contados.sum()
        
        st.markdown(f"""
        <div class="progress-big">
            <div class="number">{contados} / {total_productos}</div>
            <div class="label">Productos contados</div>
        </div>
        """, unsafe_allow_html=True)
        
        if total_productos > 0:
            progreso = contados / total_productos
            st.progress(progreso)
            st.caption(f"{progreso*100:.1f}% completado")
        
        st.divider()
        
        csv = df.to_csv(sep=";", index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Descargar inventario",
            data=csv,
            file_name=f"inventario_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    # Log de ajustes
    df_log = cargar_log()
    if not df_log.empty:
        st.divider()
        st.subheader("📋 Log de Ajustes")
        st.metric("Ajustes hoy", len(df_log))
        
        log_csv = df_log.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Descargar log",
            data=log_csv,
            file_name=f"log_ajustes_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    st.divider()
    
    # Historial de sesión en sidebar
    with st.expander("📜 Historial de sesión", expanded=False):
        mostrar_historial_sesion()
        if st.session_state.historial_sesion:
            if st.button("🗑️ Limpiar historial"):
                st.session_state.historial_sesion = []
                st.rerun()
    
    st.caption("🔗 Conectado a Alegra API")


# ========== CONTENIDO PRINCIPAL ==========

df = cargar_datos()

if df is None:
    st.warning("⚠️ No hay inventario cargado. Sube un archivo en la barra lateral.")
    st.stop()

# Función para mostrar y procesar un producto seleccionado
def mostrar_producto_seleccionado(idx, producto_local, df):
    """Muestra la interfaz de conteo para un producto seleccionado."""
    item_id = producto_local[COL_CODIGO]
    codigo_barras_producto = producto_local[COL_BARRAS]
    
    with st.spinner("🔄 Consultando Alegra..."):
        item_alegra = consultar_item_alegra(item_id)
    
    if item_alegra:
        datos = extraer_datos_item(item_alegra)
        
        if datos:
            # Sonido de éxito
            if st.session_state.sonidos_activos:
                st.markdown('<script>playSound("success")</script>', unsafe_allow_html=True)
            
            st.success("✅ Producto encontrado en Alegra")
            
            # Mostrar información del producto
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Nombre:**")
                st.info(datos["nombre"])
            
            with col2:
                st.markdown("**Stock Alegra:**")
                stock_color = "🟢" if datos['cantidad_disponible'] > 0 else "🔴"
                st.info(f"{stock_color} {datos['cantidad_disponible']:.0f} unidades")
            
            with col3:
                st.markdown("**Precio:**")
                st.info(f"${datos['precio']:,.0f}")
            
            # Mostrar si ya fue contado
            cantidad_previa = producto_local.get(COL_CANTIDAD_ACTUAL, "")
            if pd.notna(cantidad_previa) and cantidad_previa != "":
                st.warning(f"⚠️ Este producto ya fue contado: **{cantidad_previa}** unidades")
            
            # Input para cantidad contada - GRANDE
            st.markdown("---")
            
            # En modo rápido, mostrar indicador visual y auto-focus
            if st.session_state.modo_rapido:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #00b4db 0%, #0083b0 100%); 
                            color: white; padding: 10px 20px; border-radius: 10px; 
                            text-align: center; margin-bottom: 15px; font-weight: bold;">
                    ⚡ MODO RÁPIDO - Ingresa cantidad y presiona Enter para guardar
                </div>
                """, unsafe_allow_html=True)
                # Auto-focus usando componente HTML con autofocus
                st.components.v1.html("""
                <script>
                    setTimeout(function() {
                        // Buscar el input de número en el documento padre
                        const inputs = window.parent.document.querySelectorAll('input[type="number"]');
                        if (inputs.length > 0) {
                            inputs[0].focus();
                            inputs[0].select();
                        }
                    }, 300);
                </script>
                """, height=0)
            else:
                st.subheader("📝 Registrar conteo físico")
            
            # Si el stock en Alegra es negativo, iniciar en 0
            valor_inicial = max(0, int(datos["cantidad_disponible"]))
            
            # Input numérico GRANDE
            st.markdown("##### 👇 Ingresa la cantidad contada:")
            cantidad_contada = st.number_input(
                "Cantidad física contada:",
                min_value=0,
                step=1,
                value=valor_inicial,
                key="cantidad_contada",
                label_visibility="collapsed",
                help="Escribe la cantidad que contaste físicamente en tienda"
            )
            
            # Calcular diferencia
            diferencia = cantidad_contada - datos["cantidad_disponible"]
            
            # Mostrar indicador visual grande
            st.markdown("---")
            mostrar_indicador_diferencia(diferencia)
            
            if diferencia != 0:
                if diferencia > 0:
                    tipo_ajuste = "in"
                else:
                    tipo_ajuste = "out"
            else:
                tipo_ajuste = None
            
            st.markdown("---")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if diferencia != 0:
                    btn_label = "💾 Guardar y Sincronizar"
                else:
                    btn_label = "💾 Guardar conteo"
                
                if st.button(btn_label, type="primary", use_container_width=True, key="btn_guardar"):
                    if diferencia != 0:
                        st.session_state.mostrar_confirmacion = True
                        st.session_state.datos_ajuste = {
                            "codigo_barras": codigo_barras_producto,
                            "item_id": item_id,
                            "nombre": datos["nombre"],
                            "precio": datos["precio"],
                            "cantidad_anterior": datos["cantidad_disponible"],
                            "cantidad_contada": cantidad_contada,
                            "diferencia": diferencia,
                            "tipo_ajuste": tipo_ajuste,
                            "costo_unitario": datos["costo_unitario"],
                            "idx": idx
                        }
                        st.rerun()
                    else:
                        # Sin diferencia, solo guardar localmente
                        df_actualizado = cargar_datos()
                        if df_actualizado is not None:
                            df_actualizado.at[idx, COL_CANTIDAD_ACTUAL] = cantidad_contada
                            guardar_datos(df_actualizado)
                        
                        # Agregar al historial
                        agregar_al_historial(
                            codigo_barras_producto,
                            datos["nombre"],
                            datos["cantidad_disponible"],
                            cantidad_contada,
                            "ok"
                        )
                        
                        st.success("✅ Conteo guardado (sin cambios en Alegra)")
                        
                        if st.session_state.modo_rapido:
                            limpiar_para_nuevo_escaneo()
                            st.session_state.producto_seleccionado = None
                            st.rerun()
            
            with col_btn2:
                if st.button("🔄 Nuevo escaneo", use_container_width=True, key="btn_nuevo"):
                    limpiar_para_nuevo_escaneo()
                    st.session_state.producto_seleccionado = None
                    st.rerun()
        else:
            st.error("❌ Error al procesar datos del item")
    else:
        # Sonido de error
        if st.session_state.sonidos_activos:
            st.markdown('<script>playSound("error")</script>', unsafe_allow_html=True)
        st.error(f"❌ No se pudo consultar el item ID {item_id} en Alegra")


# Selector de tipo de búsqueda
st.subheader("🔍 Buscar producto")

col_busqueda1, col_busqueda2 = st.columns([3, 1])

with col_busqueda2:
    tipo_busqueda = st.radio(
        "Buscar por:",
        ["📷 Código de barras", "🔤 Nombre"],
        horizontal=False,
        label_visibility="collapsed"
    )
    st.session_state.buscar_por = "codigo_barras" if "Código" in tipo_busqueda else "nombre"

with col_busqueda1:
    if st.session_state.buscar_por == "codigo_barras":
        # Input GRANDE para código de barras
        st.markdown("##### 📷 Escanea o escribe el código:")
        codigo_input = st.text_input(
            "Código de barras:",
            placeholder="Escanea o escribe el código de barras...",
            key="input_codigo",
            label_visibility="collapsed",
            autocomplete="off"
        )
        nombre_input = None
    else:
        # Input GRANDE para búsqueda por nombre
        st.markdown("##### 🔤 Escribe el nombre del producto:")
        nombre_input = st.text_input(
            "Nombre del producto:",
            placeholder="Ej: cargador, cable, audifono...",
            key="input_nombre",
            label_visibility="collapsed"
        )
        codigo_input = None

# Atajos de teclado info
st.markdown("""
<small>
<span class="keyboard-hint">Enter</span> Buscar &nbsp;&nbsp;
<span class="keyboard-hint">Tab</span> Siguiente
</small>
""", unsafe_allow_html=True)

# ========== LÓGICA DE BÚSQUEDA ==========

# Si hay un producto ya seleccionado, mostrarlo
if st.session_state.producto_seleccionado is not None:
    idx = st.session_state.producto_seleccionado["idx"]
    producto_local = df.iloc[idx]
    mostrar_producto_seleccionado(idx, producto_local, df)

# Búsqueda por CÓDIGO DE BARRAS
elif st.session_state.buscar_por == "codigo_barras" and codigo_input:
    idx, producto_local = buscar_producto(df, codigo_input, "codigo_barras")
    
    if producto_local is not None:
        mostrar_producto_seleccionado(idx, producto_local, df)
    else:
        # Sonido de error
        if st.session_state.sonidos_activos:
            st.markdown('<script>playSound("error")</script>', unsafe_allow_html=True)
        st.error(f"❌ Producto no encontrado con código: **{codigo_input}**")
        st.info("Verifica que el código de barras esté en el archivo CSV cargado")

# Búsqueda por NOMBRE - Mostrar opciones seleccionables
elif st.session_state.buscar_por == "nombre" and nombre_input and len(nombre_input) >= 2:
    productos_encontrados = buscar_productos_por_nombre(df, nombre_input, limite=15)
    
    if not productos_encontrados.empty:
        st.success(f"✅ Se encontraron **{len(productos_encontrados)}** productos")
        st.markdown("### 👇 Selecciona un producto:")
        
        # Mostrar productos como botones seleccionables
        for i, (idx, row) in enumerate(productos_encontrados.iterrows()):
            nombre_producto = row[COL_NOMBRE]
            codigo_barras = row[COL_BARRAS]
            id_alegra = row[COL_CODIGO]
            
            # Verificar si ya fue contado
            cantidad_actual = row.get(COL_CANTIDAD_ACTUAL, "")
            ya_contado = pd.notna(cantidad_actual) and cantidad_actual != ""
            
            col_prod, col_btn = st.columns([4, 1])
            
            with col_prod:
                estado_icono = "✅" if ya_contado else "⏳"
                st.markdown(f"""
                <div class="producto-card">
                    <div class="nombre">{estado_icono} {nombre_producto}</div>
                    <div class="info">📷 {codigo_barras} &nbsp;|&nbsp; 🆔 {id_alegra}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_btn:
                if st.button("Seleccionar", key=f"btn_select_{i}_{idx}", use_container_width=True):
                    st.session_state.producto_seleccionado = {
                        "idx": idx,
                        "nombre": nombre_producto
                    }
                    st.rerun()
    else:
        # Sonido de error
        if st.session_state.sonidos_activos:
            st.markdown('<script>playSound("error")</script>', unsafe_allow_html=True)
        st.warning(f"⚠️ No se encontraron productos con: **{nombre_input}**")
        st.info("Intenta con otra palabra o parte del nombre")

elif st.session_state.buscar_por == "nombre" and nombre_input and len(nombre_input) < 2:
    st.info("✍️ Escribe al menos 2 caracteres para buscar...")


# ========== DIÁLOGO DE CONFIRMACIÓN ==========

if st.session_state.get("mostrar_confirmacion", False):
    datos = st.session_state.datos_ajuste
    
    st.markdown("---")
    st.markdown("### ⚠️ Confirmar ajuste de inventario")
    
    st.warning(f"""
    **¿Estás seguro de que el artículo "{datos['nombre']}" tiene {datos['cantidad_contada']:.0f} unidades en tienda?**
    
    - **Código de barras:** {datos['codigo_barras']}
    - **ID Alegra:** {datos['item_id']}
    - **Stock actual en Alegra:** {datos['cantidad_anterior']:.0f} unidades
    - **Cantidad contada:** {datos['cantidad_contada']:.0f} unidades
    - **Diferencia:** {'+' if datos['diferencia'] > 0 else ''}{datos['diferencia']:.0f} unidades ({'entrada' if datos['tipo_ajuste'] == 'in' else 'salida'})
    """)
    
    col_confirm1, col_confirm2 = st.columns(2)
    
    with col_confirm1:
        if st.button("✅ Sí, confirmar", type="primary", use_container_width=True, key="btn_confirmar"):
            with st.spinner("Enviando ajuste a Alegra..."):
                resultado = crear_ajuste_inventario(
                    item_id=datos["item_id"],
                    tipo=datos["tipo_ajuste"],
                    cantidad=abs(datos["diferencia"]),
                    costo=datos["costo_unitario"]
                )
            
            if resultado:
                # Sonido de éxito
                if st.session_state.sonidos_activos:
                    st.markdown('<script>playSound("success")</script>', unsafe_allow_html=True)
                
                # Guardar en CSV local
                df_actualizado = cargar_datos()
                if df_actualizado is not None:
                    df_actualizado.at[datos["idx"], COL_CANTIDAD_ACTUAL] = datos["cantidad_contada"]
                    guardar_datos(df_actualizado)
                
                # Guardar en log
                guardar_log_ajuste(
                    codigo_barras=datos["codigo_barras"],
                    item_id=datos["item_id"],
                    nombre=datos["nombre"],
                    precio=datos["precio"],
                    cantidad_anterior=datos["cantidad_anterior"],
                    cantidad_nueva=datos["cantidad_contada"],
                    diferencia=datos["diferencia"],
                    tipo_ajuste=datos["tipo_ajuste"]
                )
                
                # Agregar al historial
                agregar_al_historial(
                    datos["codigo_barras"],
                    datos["nombre"],
                    datos["cantidad_anterior"],
                    datos["cantidad_contada"],
                    "ajustado"
                )
                
                # Limpiar session state
                del st.session_state.mostrar_confirmacion
                del st.session_state.datos_ajuste
                
                st.success(f"✅ Inventario actualizado en Alegra!")
                st.success(f"Nueva cantidad: **{datos['cantidad_contada']:.0f}** unidades")
                
                if st.session_state.modo_rapido:
                    st.info("🚀 Modo rápido: Listo para siguiente escaneo")
                    limpiar_para_nuevo_escaneo()
                    st.rerun()
                else:
                    st.balloons()
            else:
                if st.session_state.sonidos_activos:
                    st.markdown('<script>playSound("error")</script>', unsafe_allow_html=True)
                st.error("❌ Error al actualizar Alegra. Intenta de nuevo.")
    
    with col_confirm2:
        if st.button("❌ Cancelar", use_container_width=True, key="btn_cancelar"):
            del st.session_state.mostrar_confirmacion
            del st.session_state.datos_ajuste
            st.rerun()


# ========== SECCIÓN DE PRODUCTOS ==========

st.divider()
with st.expander("📋 Ver todos los productos", expanded=False):
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        filtro_estado = st.selectbox(
            "Filtrar por estado:",
            ["Todos", "Contados", "Sin contar"]
        )
    
    with col_filtro2:
        buscar_nombre = st.text_input("Buscar por nombre:", placeholder="Escribe para filtrar...")
    
    df_filtrado = df.copy()
    
    if filtro_estado == "Contados":
        df_filtrado = df_filtrado[df_filtrado[COL_CANTIDAD_ACTUAL].notna() & (df_filtrado[COL_CANTIDAD_ACTUAL] != "")]
    elif filtro_estado == "Sin contar":
        df_filtrado = df_filtrado[df_filtrado[COL_CANTIDAD_ACTUAL].isna() | (df_filtrado[COL_CANTIDAD_ACTUAL] == "")]
    
    if buscar_nombre and COL_NOMBRE in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado[COL_NOMBRE].str.contains(buscar_nombre, case=False, na=False)]
    
    columnas_mostrar = [COL_CODIGO, COL_BARRAS]
    if COL_NOMBRE in df_filtrado.columns:
        columnas_mostrar.append(COL_NOMBRE)
    columnas_mostrar.append(COL_CANTIDAD_ACTUAL)
    
    st.dataframe(
        df_filtrado[columnas_mostrar],
        use_container_width=True,
        hide_index=True,
        column_config={
            COL_CODIGO: st.column_config.TextColumn("ID Alegra"),
            COL_BARRAS: st.column_config.TextColumn("Código de Barras"),
            COL_NOMBRE: st.column_config.TextColumn("Nombre"),
            COL_CANTIDAD_ACTUAL: st.column_config.NumberColumn("Conteo Físico")
        }
    )
    
    st.caption(f"Mostrando {len(df_filtrado)} de {len(df)} productos")


# ========== HISTORIAL DE AJUSTES ==========

with st.expander("📜 Ver historial de ajustes", expanded=False):
    df_log = cargar_log()
    
    if df_log.empty:
        st.info("No hay ajustes registrados todavía")
    else:
        df_log_ordenado = df_log.sort_values("fecha_hora", ascending=False)
        
        st.dataframe(
            df_log_ordenado,
            use_container_width=True,
            hide_index=True,
            column_config={
                "fecha_hora": st.column_config.TextColumn("Fecha/Hora"),
                "codigo_barras": st.column_config.TextColumn("Código Barras"),
                "id_alegra": st.column_config.TextColumn("ID Alegra"),
                "nombre": st.column_config.TextColumn("Nombre"),
                "precio": st.column_config.NumberColumn("Precio", format="$%.0f"),
                "cantidad_anterior": st.column_config.NumberColumn("Cant. Anterior"),
                "cantidad_nueva": st.column_config.NumberColumn("Cant. Nueva"),
                "diferencia": st.column_config.NumberColumn("Diferencia"),
                "tipo_ajuste": st.column_config.TextColumn("Tipo")
            }
        )
        
        st.caption(f"Total: {len(df_log)} ajustes registrados")


# ========== FOOTER CON ATAJOS ==========

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    <strong>Atajos de teclado:</strong><br>
    <span class="keyboard-hint">Enter</span> Buscar producto / Guardar conteo &nbsp;|&nbsp;
    <span class="keyboard-hint">Tab</span> Siguiente campo &nbsp;|&nbsp;
    <span class="keyboard-hint">Esc</span> Cancelar/Limpiar
</div>
""", unsafe_allow_html=True)
