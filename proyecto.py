import streamlit as st
import pandas as pd
import base64
import plotly.graph_objects as go
st.set_page_config(page_title="UNIVERSIDAD TÉCNICA PARTICULAR DE LOJA", page_icon="🌐", layout="wide")

# --- Cargar imagen local como base64 para usar en HTML ---
def get_base64_image(path):
    with open(path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
    return f"data:image/png;base64,{encoded}"

logo_base64 = get_base64_image("img/logo.png")  # tu logo local

# --- CSS personalizado para navbar completo ---
st.markdown(f"""
    <style>
    /* Ocultar botones y menús predeterminados */
    .stDeployButton {{ display: none; }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    header {{ visibility: hidden; }}

    /* Quitar padding/margen superior de Streamlit */
    .main > div:first-child {{
        padding-top: 0rem;
        margin-top: 0rem;
    }}

    /* Navbar fijo arriba */
    .navbar {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 9999;
        width: 100%;
        display: flex;
        align-items: center;
        background-color: #f0f2f6;
        padding: 10px 30px;
        border-bottom: 1px solid #ccc;
        box-sizing: border-box;
        min-height: 60px;
    }}

    /* Logo a la izquierda */
    .navbar img {{
        height: 50px;
    }}

    /* Título centrado absolutamente */
    .navbar h1 {{
        font-size: 24px;
        margin: 0;
        color: #333;
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        pointer-events: none;
        white-space: nowrap;
    }}

    /* Padding para que contenido no quede oculto bajo navbar fijo */
    .appview-container .main {{
        padding-top: 70px;
    }}
    </style>

    <div class="navbar">
        <img src="{logo_base64}" alt="Logo">
        <h1>UNIVERSIDAD TÉCNICA PARTICULAR DE LOJA</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown(
    "<h1 style='text-align: center;'>📈 Análisis DInSAR - Escenario de Desplazamientos</h1>",
    unsafe_allow_html=True
)

# Upload file
uploaded_file = st.file_uploader("Suba el archivo para analizar", type=['xlsx'])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        with st.expander("🔍 Mostrar datos del archivo"):
            if st.checkbox("Ver tabla de datos"):
                st.dataframe(df)

        if 'FECHA' not in df.columns or 'rainfall' not in df.columns:
            st.error("El archivo debe contener las columnas 'FECHA' y 'rainfall'.")
        else:
            # Obtener columnas de desplazamiento
            displacement_cols = [col for col in df.columns if col not in ['FECHA', 'rainfall', 'Puntos']]

            # Convertir fecha
            try:
                df['date'] = pd.to_datetime(df['FECHA'], format='%b-%y')
            except:
                df['date'] = pd.to_datetime(df['FECHA'])

            # --------------------------
            # 1. FILTRAR POR RANGO DE FECHAS
            # --------------------------
            st.subheader("📅 Filtrar por Rango de Fechas")
            start_date = st.date_input("Fecha inicial", df['date'].min().date())
            end_date = st.date_input("Fecha final", df['date'].max().date())

            df_filtered = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
            st.markdown("---")
            st.markdown(f"""
                <div style='text-align: center; font-size:20px;'>
                <b>Rango seleccionado:</b> <span style='color:green'>{start_date}</span> - <span style='color:red'>{end_date}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("---")
            st.dataframe(df_filtered)

            # --------------------------
            # 2. GRÁFICA PRINCIPAL
            # --------------------------
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=df_filtered['date'],
                y=df_filtered['rainfall'],
                name='Precipitación (mm)',
                line=dict(color='blue', dash='dash'),
                yaxis='y2'
            ))

            for col in displacement_cols:
                fig.add_trace(go.Scatter(
                    x=df_filtered['date'],
                    y=df_filtered[col],
                    mode='markers',
                    name=f'Desplazamiento {col} (cm)',
                    marker=dict(size=6)
                ))

            fig.update_layout(
                width=1200,   # ancho en píxeles, prueba con valores menores para que sea más estrecha
                height=600,  # altura, opcional ajustar también
                title='Desplazamiento y Precipitación en el Tiempo',
                xaxis=dict(title='Fecha'),
                yaxis=dict(title='Desplazamiento (cm)'),
                yaxis2=dict(title='Precipitación (mm)', overlaying='y', side='right'),
                hovermode='x unified',
                legend=dict(
                    orientation='h',  # horizontal
                    y=-0.2,          # un poco abajo del gráfico
                    x=0.5,           # posición horizontal (centro)
                    xanchor='center',
                    yanchor='top'
                )
            )

            st.subheader('Visualización de Desplazamiento y Precipitación')
            st.plotly_chart(fig, use_container_width=False)

            # --------------------------
            # 3 y 4 combinados en dos columnas llamativas
            # --------------------------
            st.subheader("📊 Análisis de Desplazamiento")

            col1, col2 = st.columns(2)

            with col1:
                with st.container():
                    st.markdown('<p style="font-size:16px;"> 📈 Velocidad Media</p>', unsafe_allow_html=True)
                    for col in displacement_cols:
                        desplazamiento_total = df_filtered[col].iloc[-1] - df_filtered[col].iloc[0]
                        dias_totales = (df_filtered['date'].iloc[-1] - df_filtered['date'].iloc[0]).days
                        velocidad = desplazamiento_total / dias_totales if dias_totales > 0 else 0
                        st.success(f"**{col}**: {velocidad:.4f} cm/día")

            with col2:
                with st.container():
                    st.markdown('<p style="font-size:16px;">⚡ Mayor Tasa de Desplazamiento</p>', unsafe_allow_html=True)
                    for col in displacement_cols:
                        df_filtered[f'diff_{col}'] = df_filtered[col].diff()
                        idx_max = df_filtered[f'diff_{col}'].idxmax()
                        if pd.notnull(idx_max):
                            fecha_max = df_filtered.loc[idx_max, 'date']
                            tasa = df_filtered.loc[idx_max, f'diff_{col}']
                            st.info(f"**{col}**: {fecha_max.date()} con {tasa:.4f} cm/día")

            # --------------------------
            # 5. HISTOGRAMA MENSUAL DE PRECIPITACIONES
            # --------------------------
            st.subheader("Histograma de Precipitaciones Mensuales")
            df_filtered['month'] = df_filtered['date'].dt.to_period('M').dt.to_timestamp()
            lluvia_mensual = df_filtered.groupby('month')['rainfall'].sum()

            fig_hist = go.Figure()
            fig_hist.add_trace(go.Bar(x=lluvia_mensual.index, y=lluvia_mensual.values, name="Precipitación mensual"))
            fig_hist.update_layout(title="Precipitación Mensual", xaxis_title="Mes", yaxis_title="Precipitación (mm)")
            st.plotly_chart(fig_hist, use_container_width=True)

            # --------------------------
            # 6. TABLA RESUMEN ESTADÍSTICAS
            # --------------------------
            st.subheader("📊 Estadísticas Descriptivas")
            resumen = df_filtered[displacement_cols + ['rainfall']].describe()
            st.dataframe(resumen)

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {str(e)}")

else:
    st.info("Por favor suba un archivo Excel para comenzar.")