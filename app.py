import streamlit as st
import pandas as pd
import threading
import os
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Inventario Scanner",
    page_icon="📦",
    layout="centered"
)

# Archivo de datos
ARCHIVO_INVENTARIO = "inventario.csv"
LOCK = threading.Lock()

# Columnas importantes del CSV original (separador ;)
COL_CODIGO = "Codigo"
COL_NOMBRE = "Nombre"
COL_STOCK = "Cantidad inicial en bodega: Principal"
COL_BARRAS = "Codigo de barras"
COL_CANTIDAD_ACTUAL = "cantidad_actual"


def cargar_datos():
    """Carga los datos del CSV si existe"""
    if os.path.exists(ARCHIVO_INVENTARIO):
        try:
            df = pd.read_csv(ARCHIVO_INVENTARIO, sep=";", dtype={COL_BARRAS: str})
            # Asegurar que la columna de código de barras sea string
            df[COL_BARRAS] = df[COL_BARRAS].astype(str).str.strip()
            # Crear columna cantidad_actual si no existe
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
    """Busca un producto por código de barras"""
    codigo_barras = str(codigo_barras).strip()
    resultado = df[df[COL_BARRAS] == codigo_barras]
    if not resultado.empty:
        return resultado.index[0], resultado.iloc[0]
    return None, None


def procesar_archivo_subido(archivo):
    """Procesa el archivo subido y lo guarda"""
    try:
        if archivo.name.endswith('.csv'):
            # Intentar detectar el separador
            contenido = archivo.getvalue().decode('utf-8')
            if ';' in contenido[:1000]:
                df = pd.read_csv(archivo, sep=";", dtype={COL_BARRAS: str})
            else:
                df = pd.read_csv(archivo, dtype={COL_BARRAS: str})
        else:
            df = pd.read_excel(archivo, dtype={COL_BARRAS: str})
        
        # Verificar columnas necesarias
        columnas_requeridas = [COL_CODIGO, COL_NOMBRE, COL_STOCK, COL_BARRAS]
        columnas_faltantes = [c for c in columnas_requeridas if c not in df.columns]
        
        if columnas_faltantes:
            st.error(f"Faltan columnas requeridas: {columnas_faltantes}")
            return False
        
        # Limpiar código de barras
        df[COL_BARRAS] = df[COL_BARRAS].astype(str).str.strip()
        
        # Agregar columna cantidad_actual si no existe
        if COL_CANTIDAD_ACTUAL not in df.columns:
            df[COL_CANTIDAD_ACTUAL] = ""
        
        # Guardar
        guardar_datos(df)
        return True
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        return False


# ========== INTERFAZ ==========

st.title("📦 Inventario Scanner")
st.markdown("Escanea códigos de barras para registrar el conteo físico del inventario")

# Sidebar para administración
with st.sidebar:
    st.header("⚙️ Administración")
    
    archivo_subido = st.file_uploader(
        "Subir archivo de inventario",
        type=['csv', 'xlsx'],
        help="Sube el archivo CSV o Excel con el inventario"
    )
    
    if archivo_subido:
        if st.button("📤 Cargar archivo", type="primary"):
            with st.spinner("Procesando archivo..."):
                if procesar_archivo_subido(archivo_subido):
                    st.success("✅ Archivo cargado correctamente")
                    st.rerun()
    
    st.divider()
    
    # Mostrar estado del inventario
    df = cargar_datos()
    if df is not None:
        total_productos = len(df)
        productos_contados = df[COL_CANTIDAD_ACTUAL].notna() & (df[COL_CANTIDAD_ACTUAL] != "")
        contados = productos_contados.sum()
        
        st.metric("Total productos", total_productos)
        st.metric("Productos contados", f"{contados} / {total_productos}")
        
        # Progreso
        if total_productos > 0:
            progreso = contados / total_productos
            st.progress(progreso)
        
        st.divider()
        
        # Descargar archivo actualizado
        csv = df.to_csv(sep=";", index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Descargar inventario",
            data=csv,
            file_name=f"inventario_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

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
    idx, producto = buscar_producto(df, codigo_input)
    
    if producto is not None:
        st.success("✅ Producto encontrado")
        
        # Mostrar información del producto
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Nombre:**")
            st.info(producto[COL_NOMBRE])
        
        with col2:
            st.markdown("**Stock en sistema:**")
            st.info(f"{producto[COL_STOCK]} unidades")
        
        # Mostrar cantidad actual si ya fue contado
        cantidad_previa = producto.get(COL_CANTIDAD_ACTUAL, "")
        if pd.notna(cantidad_previa) and cantidad_previa != "":
            st.warning(f"⚠️ Este producto ya fue contado: **{cantidad_previa}** unidades")
        
        # Input para cantidad contada
        st.markdown("---")
        st.subheader("📝 Registrar conteo")
        
        cantidad = st.number_input(
            "Cantidad física contada:",
            min_value=0,
            step=1,
            key="cantidad_contada"
        )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("💾 Guardar conteo", type="primary", use_container_width=True):
                # Recargar datos para evitar conflictos
                df_actualizado = cargar_datos()
                if df_actualizado is not None:
                    df_actualizado.at[idx, COL_CANTIDAD_ACTUAL] = cantidad
                    guardar_datos(df_actualizado)
                    st.success(f"✅ Conteo guardado: **{cantidad}** unidades")
                    st.balloons()
                    # Limpiar el input
                    st.rerun()
        
        with col_btn2:
            if st.button("🔄 Nuevo escaneo", use_container_width=True):
                st.rerun()
    else:
        st.error(f"❌ Producto no encontrado con código: **{codigo_input}**")
        st.info("Verifica que el código de barras sea correcto")

# Sección para ver productos
st.divider()
with st.expander("📋 Ver todos los productos", expanded=False):
    # Filtros
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        filtro_estado = st.selectbox(
            "Filtrar por estado:",
            ["Todos", "Contados", "Sin contar"]
        )
    
    with col_filtro2:
        buscar_nombre = st.text_input("Buscar por nombre:", placeholder="Escribe para filtrar...")
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if filtro_estado == "Contados":
        df_filtrado = df_filtrado[df_filtrado[COL_CANTIDAD_ACTUAL].notna() & (df_filtrado[COL_CANTIDAD_ACTUAL] != "")]
    elif filtro_estado == "Sin contar":
        df_filtrado = df_filtrado[df_filtrado[COL_CANTIDAD_ACTUAL].isna() | (df_filtrado[COL_CANTIDAD_ACTUAL] == "")]
    
    if buscar_nombre:
        df_filtrado = df_filtrado[df_filtrado[COL_NOMBRE].str.contains(buscar_nombre, case=False, na=False)]
    
    # Mostrar tabla con columnas relevantes
    columnas_mostrar = [COL_BARRAS, COL_NOMBRE, COL_STOCK, COL_CANTIDAD_ACTUAL]
    st.dataframe(
        df_filtrado[columnas_mostrar],
        use_container_width=True,
        hide_index=True,
        column_config={
            COL_BARRAS: st.column_config.TextColumn("Código de Barras"),
            COL_NOMBRE: st.column_config.TextColumn("Nombre"),
            COL_STOCK: st.column_config.NumberColumn("Stock Sistema"),
            COL_CANTIDAD_ACTUAL: st.column_config.NumberColumn("Conteo Físico")
        }
    )
    
    st.caption(f"Mostrando {len(df_filtrado)} de {len(df)} productos")
