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

# ========== CONFIGURACIÓN ==========

# Archivo de datos local (solo para mapear código de barras -> ID de Alegra)
ARCHIVO_INVENTARIO = "inventario.csv"
LOCK = threading.Lock()

# Columnas del CSV
COL_CODIGO = "Codigo"  # ID del item en Alegra
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
WAREHOUSE_ID = 1  # ID de bodega Principal en Alegra


# ========== FUNCIONES DE API ALEGRA ==========

def consultar_item_alegra(item_id):
    """
    Consulta un item en la API de Alegra.
    
    Args:
        item_id: ID del item en Alegra
        
    Returns:
        dict con los datos del item o None si hay error
    """
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
    """
    Crea un ajuste de inventario en Alegra.
    
    Args:
        item_id: ID del item en Alegra
        tipo: "in" para entrada, "out" para salida
        cantidad: Cantidad a ajustar (siempre positivo)
        costo: Costo unitario del item
        
    Returns:
        dict con la respuesta de Alegra o None si hay error
    """
    try:
        url = f"{ALEGRA_API_URL}/inventory-adjustments"
        headers = {
            "accept": "application/json",
            "authorization": f"Basic {ALEGRA_API_KEY}",
            "content-type": "application/json"
        }
        payload = {
            "date": date.today().isoformat(),
            "warehouse": {"id": str(WAREHOUSE_ID)},  # Debe ser string
            "items": [{
                "id": str(item_id),  # Debe ser string
                "type": tipo,
                "quantity": float(cantidad),
                "unitCost": float(costo) if costo else 0  # Campo correcto: unitCost
            }]
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error al crear ajuste en Alegra: {e}")
        return None


def extraer_datos_item(item_data):
    """
    Extrae los datos relevantes de la respuesta de la API de Alegra.
    
    Args:
        item_data: dict con la respuesta de GET /items/{id}
        
    Returns:
        dict con nombre, cantidad_disponible, costo_unitario, precio
    """
    if not item_data:
        return None
    
    # Extraer nombre
    nombre = item_data.get("name", "Sin nombre")
    
    # Extraer inventario
    inventory = item_data.get("inventory", {})
    cantidad_disponible = inventory.get("availableQuantity", 0)
    costo_unitario = inventory.get("unitCost", 0)
    
    # Extraer precio de lista
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


def buscar_producto(df, codigo_barras):
    """Busca un producto por código de barras y retorna el índice y datos"""
    codigo_barras = str(codigo_barras).strip()
    resultado = df[df[COL_BARRAS] == codigo_barras]
    if not resultado.empty:
        return resultado.index[0], resultado.iloc[0]
    return None, None


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
        
        # Verificar columnas necesarias (solo necesitamos Codigo y Codigo de barras para Alegra)
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


# ========== INTERFAZ ==========

st.title("📦 Inventario Scanner")
st.markdown("Escanea códigos de barras para actualizar inventario en **Alegra** en tiempo real")

# Sidebar para administración
with st.sidebar:
    st.header("⚙️ Administración")
    
    archivo_subido = st.file_uploader(
        "Subir archivo de inventario",
        type=['csv', 'xlsx'],
        help="Sube el archivo CSV o Excel con el inventario (debe tener columnas 'Codigo' y 'Codigo de barras')"
    )
    
    if archivo_subido:
        if st.button("📤 Cargar archivo", type="primary"):
            with st.spinner("Procesando archivo..."):
                if procesar_archivo_subido(archivo_subido):
                    st.success("✅ Archivo cargado correctamente")
                    st.rerun()
    
    st.divider()
    
    # Mostrar estado del inventario local
    df = cargar_datos()
    if df is not None:
        total_productos = len(df)
        productos_contados = df[COL_CANTIDAD_ACTUAL].notna() & (df[COL_CANTIDAD_ACTUAL] != "")
        contados = productos_contados.sum()
        
        st.metric("Total productos", total_productos)
        st.metric("Productos contados", f"{contados} / {total_productos}")
        
        if total_productos > 0:
            progreso = contados / total_productos
            st.progress(progreso)
        
        st.divider()
        
        csv = df.to_csv(sep=";", index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Descargar inventario",
            data=csv,
            file_name=f"inventario_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    st.divider()
    st.caption("🔗 Conectado a Alegra API")

# Contenido principal
df = cargar_datos()

if df is None:
    st.warning("⚠️ No hay inventario cargado. Sube un archivo en la barra lateral.")
    st.stop()

# Input para código de barras
st.subheader("🔍 Escanear producto")
codigo_input = st.text_input(
    "Código de barras:",
    placeholder="Escanea o escribe el código de barras",
    key="codigo_barras",
    label_visibility="collapsed"
)

# Buscar producto cuando se ingresa un código
if codigo_input:
    idx, producto_local = buscar_producto(df, codigo_input)
    
    if producto_local is not None:
        # Obtener ID de Alegra del CSV
        item_id = producto_local[COL_CODIGO]
        
        # Consultar datos en tiempo real de Alegra
        with st.spinner("Consultando Alegra..."):
            item_alegra = consultar_item_alegra(item_id)
        
        if item_alegra:
            datos = extraer_datos_item(item_alegra)
            
            if datos:
                st.success("✅ Producto encontrado en Alegra")
                
                # Mostrar información del producto desde Alegra
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**Nombre:**")
                    st.info(datos["nombre"])
                
                with col2:
                    st.markdown("**Stock Alegra:**")
                    st.info(f"{datos['cantidad_disponible']:.0f} unidades")
                
                with col3:
                    st.markdown("**Precio:**")
                    st.info(f"${datos['precio']:,.0f}")
                
                # Mostrar si ya fue contado localmente
                cantidad_previa = producto_local.get(COL_CANTIDAD_ACTUAL, "")
                if pd.notna(cantidad_previa) and cantidad_previa != "":
                    st.warning(f"⚠️ Este producto ya fue contado hoy: **{cantidad_previa}** unidades")
                
                # Input para cantidad contada
                st.markdown("---")
                st.subheader("📝 Registrar conteo físico")
                
                cantidad_contada = st.number_input(
                    "Cantidad física contada:",
                    min_value=0,
                    step=1,
                    value=int(datos["cantidad_disponible"]),  # Precargar con valor actual
                    key="cantidad_contada"
                )
                
                # Calcular diferencia
                diferencia = cantidad_contada - datos["cantidad_disponible"]
                
                if diferencia != 0:
                    if diferencia > 0:
                        st.info(f"📈 Se agregará **+{diferencia:.0f}** unidades al inventario")
                        tipo_ajuste = "in"
                    else:
                        st.info(f"📉 Se quitarán **{abs(diferencia):.0f}** unidades del inventario")
                        tipo_ajuste = "out"
                else:
                    st.success("✓ El conteo coincide con el stock en Alegra")
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button("💾 Guardar y Sincronizar", type="primary", use_container_width=True):
                        if diferencia != 0:
                            # Crear ajuste en Alegra
                            with st.spinner("Actualizando Alegra..."):
                                resultado = crear_ajuste_inventario(
                                    item_id=item_id,
                                    tipo=tipo_ajuste,
                                    cantidad=abs(diferencia),
                                    costo=datos["costo_unitario"]
                                )
                            
                            if resultado:
                                # Guardar en CSV local también
                                df_actualizado = cargar_datos()
                                if df_actualizado is not None:
                                    df_actualizado.at[idx, COL_CANTIDAD_ACTUAL] = cantidad_contada
                                    guardar_datos(df_actualizado)
                                
                                st.success(f"✅ Inventario actualizado en Alegra!")
                                st.success(f"Nueva cantidad: **{cantidad_contada}** unidades")
                                st.balloons()
                            else:
                                st.error("❌ Error al actualizar Alegra. Intenta de nuevo.")
                        else:
                            # Solo guardar localmente si no hay diferencia
                            df_actualizado = cargar_datos()
                            if df_actualizado is not None:
                                df_actualizado.at[idx, COL_CANTIDAD_ACTUAL] = cantidad_contada
                                guardar_datos(df_actualizado)
                            st.success("✅ Conteo guardado (sin cambios en Alegra)")
                
                with col_btn2:
                    if st.button("🔄 Nuevo escaneo", use_container_width=True):
                        st.rerun()
            else:
                st.error("❌ Error al procesar datos del item")
        else:
            st.error(f"❌ No se pudo consultar el item ID {item_id} en Alegra")
    else:
        st.error(f"❌ Producto no encontrado con código: **{codigo_input}**")
        st.info("Verifica que el código de barras esté en el archivo CSV cargado")

# Sección para ver productos
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
    
    # Mostrar tabla
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
