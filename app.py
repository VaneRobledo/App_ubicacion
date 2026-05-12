import requests
import folium
import streamlit as st
import plotly.graph_objects as go
from streamlit_folium import st_folium
import os

from db_utils import search_business_types
from map_utils import add_points, create_base_map, interpretar_feature
from ui_utils import get_svg_icon, load_local_css, st_custom_header, st_custom_message

st.set_page_config(layout="wide", page_icon="📍", page_title="Evaluador de Ubicación Comercial")
load_local_css()

st_custom_header("Evaluador de Ubicación Comercial (Mapa interactivo)", icon="pin", color="#708238", level="h1")

# -----------------------
# Buscador de tipos de negocio
# -----------------------
st_custom_header("Buscar Tipo de Negocio", icon="search", color="#a67b5b", level="h3")

if "selected_business" not in st.session_state:
    st.session_state.selected_business = None

if "search_query" not in st.session_state:
    st.session_state.search_query = ""

search_query = st.text_input(
    "Buscar negocio:",
    value=st.session_state.search_query,
    placeholder="Escribe el nombre del negocio (ej: cafe, abogado, dentista...)",
    help="Busca entre más de 160 tipos de negocio disponibles"
)

if search_query != st.session_state.search_query:
    st.session_state.search_query = search_query
    st.rerun()

businesses = search_business_types(search_query)

if businesses:
    st.markdown(f"**Encontrados {len(businesses)} tipos de negocio:**")
    cols = st.columns(3)
    for i, business in enumerate(businesses[:9]):
        col_idx = i % 3
        with cols[col_idx]:
            if st.button(business["nombre"].title(), key=f"btn_{business['id']}", use_container_width=True):
                st.session_state.selected_business = business["nombre"]
                st.rerun()

    if len(businesses) > 9:
        st_custom_message(f"Y {len(businesses) - 9} negocios más... refine su búsqueda", "info")
else:
    st.warning("No se encontraron negocios que coincidan con la búsqueda.")

if st.session_state.selected_business:
    st_custom_message(f"Negocio seleccionado: <strong>{st.session_state.selected_business.title()}</strong>", "success")
    tipo_negocio = st.session_state.selected_business
else:
    tipo_negocio = None
    st_custom_message("Selecciona un tipo de negocio para continuar con el análisis", "info")

if not tipo_negocio:
    st.stop()

if "last_click" not in st.session_state:
    st.session_state.last_click = None

if "resultado" not in st.session_state:
    st.session_state.resultado = None

mapa = create_base_map()

if st.session_state.resultado:
    data = st.session_state.resultado
    geo = data.get("geo", {})

    competencia_layer = folium.FeatureGroup(name="🔴 Competencia")
    potenciales_clientes_layer = folium.FeatureGroup(name="🔵 potenciales_clientes")
    sinergia_layer = folium.FeatureGroup(name="🟢 Sinergia")
    transporte_layer = folium.FeatureGroup(name="🟡 Transporte")

    add_points(competencia_layer, geo.get("competencia", []), "red")
    add_points(potenciales_clientes_layer, geo.get("potenciales_clientes", []), "blue")
    add_points(sinergia_layer, geo.get("sinergia", []), "green")
    add_points(transporte_layer, geo.get("transporte", []), "orange")

    competencia_layer.add_to(mapa)
    potenciales_clientes_layer.add_to(mapa)
    sinergia_layer.add_to(mapa)
    transporte_layer.add_to(mapa)
    folium.LayerControl().add_to(mapa)

c1, c2 = st.columns([55, 45])
with c1:
    map_data = st_folium(mapa, width=900, height=600)

if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    new_point = (round(lat, 5), round(lon, 5))

    if st.session_state.last_click != new_point:
        st.session_state.last_click = new_point
        st_custom_message(f"Ubicación seleccionada: {lat:.5f}, {lon:.5f}", "success")

        URL_BACKEND = st.secrets.get("BACKEND_URL", "https://appubicacion-nube/analizar.streamlit.app")
        payload = {
            "lat": lat,
            "lon": lon,
            "tipo_negocio": tipo_negocio
        }

        with st.spinner("Consultando datos urbanos (puede tardar unos segundos)..."):
            try:
                response = requests.post(URL_BACKEND, json=payload, timeout=60)
                if response.status_code == 200:
                    st.session_state.resultado = response.json()
                else:
                    st.error("Error en API")
            except Exception as e:
                st.error(f"Error: {e}")

with c2:
    if st.session_state.resultado:
        data = st.session_state.resultado
        features = data["features"]
        prob = data["probabilidad"] * 100

        color = (
            "#2b814b" if prob >= 70
            else "#ca8a04" if prob >= 50
            else "#a01d1d"
        )

        st.markdown(f"""
        <div class="card">
            <div class="label">Probabilidad de buena ubicación</div>
            <div class="big-number" style="color:{color}">
                {prob:.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

        st_custom_header("Factores clave", icon="pin", color="#c39953", level="h3")

        categorias = [
            "Competencia",
            "Accesibilidad",
            "Clientes potenciales",
            "Sinergia"
        ]

        valores = [
            features.get("competencia", 0),
            features.get("accesibilidad", 0),
            features.get("potenciales_clientes", 0),
            features.get("sinergia", 0)
        ]

        categorias += [categorias[0]]
        valores += [valores[0]]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=valores,
            theta=categorias,
            fill='toself',
            name='Factores',
            line=dict(width=3),
            fillcolor='rgba(112, 130, 56, 0.3)',
            line_color='#708238'
        ))
        fig.update_layout(
            polar=dict(bgcolor='#fdfaf5',
                radialaxis=dict(
                    visible=True,
                    range=[0, 1],
                    gridcolor='#eaddca', showline=False
                ), angularaxis=dict(gridcolor='#eaddca')
            ),
            showlegend=False,
            height=420,
            margin=dict(l=40, r=40, t=40, b=40),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#4a4a4a',
        )
        st.plotly_chart(fig, use_container_width=True, width='stretch')

if st.session_state.resultado:
    data = st.session_state.resultado
    features = data["features"]
    st_custom_header("Interpretación", icon="insight", color="#c39953", level="h2")

    texto = f"""
    <div style="margin-top:20px;">
        <p>{get_svg_icon('pin', '#708238', 18)} <strong>Análisis de la ubicación</strong></p>
        <p>La zona presenta un <strong>{interpretar_feature(data['features']['potenciales_clientes'], 'potenciales_clientes')}</strong>, con una <strong>{interpretar_feature(features['accesibilidad'], 'accesibilidad')}</strong>.</p>
        <p>En cuanto al entorno comercial, se observa un <strong>{interpretar_feature(features['competencia'], 'competencia')}</strong>, 
        acompañado de <strong>{interpretar_feature(features['sinergia'], 'sinergia')}</strong>.</p>
        <p>Esto sugiere que la ubicación {'es favorable' if data['probabilidad'] > 0.6 else 'requiere análisis adicional' if data['probabilidad'] > 0.4 else 'presenta condiciones desfavorables'} para el tipo de negocio seleccionado.</p>
    </div>
    """
    st.markdown(texto, unsafe_allow_html=True)
