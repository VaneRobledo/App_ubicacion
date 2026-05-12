from pathlib import Path

from sqlalchemy import create_engine, text
import streamlit as st

DB_PATH = Path(__file__).resolve().parent / "mi_base_de_datos_expanded.db"
DB_URL = f"sqlite:///{DB_PATH}" if DB_PATH.exists() else "sqlite:///mi_base_de_datos_expanded.db"

@st.cache_data
def get_business_types():
    """Obtiene todos los tipos de negocio desde la base de datos."""
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            result = conn.execute(text(
                """
                SELECT id, nombre
                FROM business_types
                ORDER BY nombre
                """
            ))
            businesses = [{"id": row[0], "nombre": row[1]} for row in result.fetchall()]
        engine.dispose()
        return businesses
    except Exception as e:
        st.error(f"Error conectando a la base de datos: {e}")
        return []

@st.cache_data
def search_business_types(query):
    """Busca tipos de negocio que coincidan con la consulta."""
    if not query:
        return get_business_types()

    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            result = conn.execute(text(
                """
                SELECT id, nombre
                FROM business_types
                WHERE nombre LIKE :query
                ORDER BY nombre
                """
            ), {"query": f"%{query}%"})
            businesses = [{"id": row[0], "nombre": row[1]} for row in result.fetchall()]
        engine.dispose()
        return businesses
    except Exception as e:
        st.error(f"Error en búsqueda: {e}")
        return []

@st.cache_data
def get_business_details(business_name):
    """Obtiene detalles completos de un tipo de negocio."""
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            result = conn.execute(text(
                """
                SELECT id, nombre, mu, sigma, peso_competencia, peso_clientes, peso_accesibilidad, peso_sinergia
                FROM business_types
                WHERE nombre = :name
                """
            ), {"name": business_name})
            row = result.fetchone()
            if row:
                return {
                    "id": row[0],
                    "nombre": row[1],
                    "mu": row[2],
                    "sigma": row[3],
                    "peso_competencia": row[4],
                    "peso_clientes": row[5],
                    "peso_accesibilidad": row[6],
                    "peso_sinergia": row[7]
                }
        engine.dispose()
    except Exception as e:
        st.error(f"Error obteniendo detalles: {e}")
    return None
