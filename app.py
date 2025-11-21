import streamlit as st
import pandas as pd
import io
import re

# --- CONFIGURACIÓN DE PÁGINA Y ESTILOS ---
st.set_page_config(page_title="Data Cleaner Pro", page_icon="💎", layout="wide")

# Hemos simplificado el CSS para que se adapte automáticamente al modo claro/oscuro del usuario
st.markdown("""
    <style>
    /* Damos un poco de énfasis a los títulos */
    h1 {color: #2c3e50;}
    /* En modo oscuro, ajustamos el color del título para que se lea bien */
    @media (prefers-color-scheme: dark) {
        h1 {color: #ecf0f1;}
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER Y PROPUESTA DE VALOR ---
st.title("💎 Data Cleaner Pro")
st.markdown("""
**Tu navaja suiza para datos:** Sube tu archivo, elimina duplicados, corrige formatos, 
convierte monedas a números y exporta un Excel impecable en segundos.
""")
st.markdown("---")

# --- SIDEBAR: CARGA DE DATOS ---
st.sidebar.header("📂 1. Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Arrastra tu archivo Excel o CSV aquí", type=["csv", "xlsx"])

# --- TUTORIAL (Se muestra solo si NO hay archivo) ---
if uploaded_file is None:
    st.info("👋 **Bienvenido.** Para empezar, arrastra un archivo en el menú de la izquierda.")
    
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.markdown("#### 1️⃣ Limpia")
        st.caption("Elimina duplicados, espacios extra y rellena huecos automáticamente.")
    with col_t2:
        st.markdown("#### 2️⃣ Transforma")
        st.caption("Convierte monedas de texto a números (ej: '$500' -> 500) y arregla mayúsculas.")
    with col_t3:
        st.markdown("#### 3️⃣ Exporta")
        st.caption("Descarga tu trabajo en Excel o CSV listo para presentar.")
    
    st.markdown("---")
    
    # Ejemplo visual COMPLETO (Antes y Después)
    st.markdown("##### 💡 El resultado que obtendrás:")
    
    # Datos de ejemplo
    ejemplo_sucio = pd.DataFrame({
        'Cliente': ['  juan perez  ', 'MARIA GOMEZ', 'juan perez'],
        'Venta': ['$ 1,200.00', '1500 USD', '$ 1,200.00']
    })
    
    ejemplo_limpio = pd.DataFrame({
        'Cliente': ['Juan Perez', 'Maria Gomez'],
        'Venta': [1200.00, 1500.00]
    })
    
    # Mostrar lado a lado
    c_ex1, c_ex2 = st.columns(2)
    with c_ex1:
        st.markdown("**Antes (Datos Sucios):**")
        st.table(ejemplo_sucio)
    with c_ex2:
        st.markdown("**Después (Limpios y sin duplicados):**")
        st.table(ejemplo_limpio)
        
    st.caption("👆 Eliminación automática de duplicados, formato de nombre correcto y conversión de moneda a número.")

# --- LÓGICA PRINCIPAL (Se muestra si HAY archivo) ---
else:
    # Inicializamos
    df = None
    
    def convert_df_to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='DataCleanerPro')
        return output.getvalue()

    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        st.sidebar.success("✅ Archivo cargado")
        
        # Creamos copia de trabajo
        df_clean = df.copy()

        # --- SECCIÓN 2: LIMPIEZA BÁSICA ---
        st.sidebar.header("🛠️ 2. Herramientas de Limpieza")
        
        with st.sidebar.expander("🧹 Limpieza General", expanded=True):
            if st.checkbox("Eliminar duplicados", value=False):
                df_clean = df_clean.drop_duplicates()
            
            if st.checkbox("Rellenar vacíos con 'Sin Dato'", value=False):
                df_clean = df_clean.fillna("Sin Dato")
            
            if st.checkbox("Eliminar espacios extra (Trim)", value=True, help="Convierte '  Juan   Perez ' en 'Juan Perez'"):
                cols_obj = df_clean.select_dtypes(include=['object']).columns
                for col in cols_obj:
                    df_clean[col] = df_clean[col].astype(str).apply(lambda x: " ".join(x.split()))

        # --- SECCIÓN 3: CONVERSIÓN DE MONEDA ---
        with st.sidebar.expander("💲 Conversión de Moneda a Número"):
            st.write("Selecciona columnas con precios en texto (ej: '$ 1,000') para volverlos números.")
            cols_moneda = st.multiselect("Columnas a convertir:", df_clean.columns)
            
            for col in cols_moneda:
                try:
                    # Usamos regex para dejar solo números y puntos/comas
                    # Esta expresión busca cualquier cosa que NO sea dígito, punto o coma y lo borra
                    df_clean[col] = df_clean[col].astype(str).str.replace(r'[^\d.,-]', '', regex=True)
                    # Intentamos convertir a numérico
                    df_clean[col] = pd.to_numeric(df_clean[col])
                    st.success(f"Columna '{col}' convertida a números.")
                except:
                    st.warning(f"No se pudo convertir la columna '{col}' automáticamente. Revisa el formato.")

        # --- SECCIÓN 4: FORMATO DE TEXTO ---
        with st.sidebar.expander("🔤 Formato de Texto"):
            cols_texto = list(df_clean.select_dtypes(include=['object']).columns)
            
            # UPPER
            cols_upper = st.multiselect("A MAYÚSCULAS:", cols_texto)
            for col in cols_upper:
                df_clean[col] = df_clean[col].astype(str).str.upper()
            
            # LOWER
            rest_1 = [c for c in cols_texto if c not in cols_upper]
            cols_lower = st.multiselect("A minúsculas:", rest_1)
            for col in cols_lower:
                df_clean[col] = df_clean[col].astype(str).str.lower()
            
            # TITLE
            rest_2 = [c for c in rest_1 if c not in cols_lower]
            cols_title = st.multiselect("A Tipo Título:", rest_2)
            for col in cols_title:
                df_clean[col] = df_clean[col].astype(str).str.title()

        # --- SECCIÓN 5: RENOMBRAR COLUMNAS ---
        with st.sidebar.expander("🏷️ Renombrar Columnas"):
            st.write("Cambia los nombres de las columnas para el archivo final.")
            nombres_nuevos = {}
            for col in df_clean.columns:
                nuevo_nombre = st.text_input(f"Renombrar '{col}' a:", value=col, key=f"rename_{col}")
                nombres_nuevos[col] = nuevo_nombre
            
            df_clean = df_clean.rename(columns=nombres_nuevos)

        # --- FILTROS ---
        st.sidebar.markdown("---")
        if st.sidebar.checkbox("🎯 Filtrar datos antes de descargar"):
            col_filtro = st.sidebar.selectbox("Columna a filtrar:", df_clean.columns)
            valores = df_clean[col_filtro].unique()
            seleccion = st.sidebar.multiselect(f"Valores de '{col_filtro}':", valores)
            if seleccion:
                df_clean = df_clean[df_clean[col_filtro].isin(seleccion)]

        # --- PANTALLA PRINCIPAL (Métricas y Resultados) ---
        
        # Dashboard de métricas (Ahora se adaptan al modo oscuro/claro)
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Filas Originales", len(df))
        c2.metric("Filas Actuales (Limpias)", len(df_clean))
        c3.metric("Columnas", len(df_clean.columns))

        st.markdown("---")

        tab1, tab2 = st.tabs(["📋 Vista Previa y Descarga", "📊 Análisis Gráfico"])

        with tab1:
            st.dataframe(df_clean, use_container_width=True)
            
            st.markdown("### 📥 Descargar Archivo Listo")
            d1, d2 = st.columns(2)
            with d1:
                csv = df_clean.to_csv(index=False).encode('utf-8')
                st.download_button("Descargar CSV", data=csv, file_name="DataCleaner_Pro.csv", mime="text/csv", use_container_width=True)
            with d2:
                excel_data = convert_df_to_excel(df_clean)
                st.download_button("Descargar Excel (.xlsx)", data=excel_data, file_name="DataCleaner_Pro.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

        with tab2:
            # Detectamos columnas numéricas para gráficos
            num_cols = df_clean.select_dtypes(include=['float64', 'int64']).columns
            cat_cols = df_clean.select_dtypes(include=['object']).columns
            
            if len(num_cols) > 0 and len(cat_cols) > 0:
                st.subheader("Generador de Gráficos")
                c_graph1, c_graph2 = st.columns(2)
                eje_x = c_graph1.selectbox("Eje X (Categoría):", cat_cols)
                eje_y = c_graph2.selectbox("Eje Y (Valor):", num_cols)
                
                st.bar_chart(df_clean.set_index(eje_x)[eje_y])
                
                st.markdown("---")
                st.write("##### Estadísticas Descriptivas")
                st.dataframe(df_clean.describe(), use_container_width=True)
            else:
                st.info("⚠️ Para ver gráficos, asegúrate de tener columnas numéricas. Si tienes precios con símbolos ($/€), usa la opción 'Conversión de Moneda' en el menú lateral.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")