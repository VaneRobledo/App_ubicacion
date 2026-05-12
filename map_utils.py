import folium


def create_base_map():
    return folium.Map(
        location=[-34.83799811205703, -58.38576850378097],
        zoom_start=13,
        tiles='CartoDB positron'
    )


def interpretar_feature(valor, tipo):
    if tipo == "competencia":
        if valor < 0.3:
            return "nivel de competencia bajo (zona poco desarrollada o con baja actividad comercial)"
        elif valor < 0.7:
            return "nivel de competencia adecuado (indica un mercado activo y validado)"
        else:
            return "nivel de competencia óptimo (zona comercial consolidada)"

    if tipo == "potenciales_clientes":
        if valor < 0.3:
            return "bajo flujo de potenciales clientes"
        elif valor < 0.7:
            return "flujo moderado de potenciales clientes"
        else:
            return "alto flujo de potenciales clientes"

    if tipo == "accesibilidad":
        if valor < 0.3:
            return "accesibilidad limitada"
        elif valor < 0.7:
            return "accesibilidad aceptable"
        else:
            return "excelente accesibilidad"

    if tipo == "sinergia":
        if valor < 0.3:
            return "baja presencia de negocios complementarios"
        elif valor < 0.7:
            return "buena presencia de negocios complementarios"
        else:
            return "ecosistema comercial muy favorable"

    return ""


def add_points(layer, puntos, color):
    for p in puntos:
        popup_text = f"""
            <b>{p.get('nombre', 'Sin nombre')}</b><br>
            Tipo: {p.get('tipo', 'N/A')}
        """
        folium.CircleMarker(
            location=[p['lat'], p['lon']],
            radius=5,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=folium.Popup(popup_text, max_width=250),
            tooltip=p.get('tipo', 'Punto')
        ).add_to(layer)
