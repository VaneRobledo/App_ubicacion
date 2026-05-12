import requests
import math
import time
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

OVERPASS_URL = "https://overpass.kumi.systems/api/interpreter"

# Configuración de base de datos expandida
DATABASE_URL = "sqlite:///mi_base_de_datos_expanded.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Definir modelos localmente para evitar dependencias
Base = declarative_base()

class OSMEntity(Base):
    __tablename__ = "osm_entities"
    id = Column(Integer, primary_key=True, index=True)
    osm_key = Column(String, nullable=False)
    osm_value = Column(String, nullable=True)
    nombre = Column(String, nullable=False)
    categoria = Column(String, nullable=False)
    relations = relationship("BusinessRelation", back_populates="entity")

class BusinessType(Base):
    __tablename__ = "business_types"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    mu = Column(Float, nullable=False)
    sigma = Column(Float, nullable=False)
    peso_competencia = Column(Float, nullable=False)
    peso_clientes = Column(Float, nullable=False)
    peso_accesibilidad = Column(Float, nullable=False)
    peso_sinergia = Column(Float, nullable=False)
    relations = relationship("BusinessRelation", back_populates="business_type")

class BusinessRelation(Base):
    __tablename__ = "business_relations"
    id = Column(Integer, primary_key=True, index=True)
    business_type_id = Column(Integer, ForeignKey("business_types.id"), nullable=False)
    osm_entity_id = Column(Integer, ForeignKey("osm_entities.id"), nullable=False)
    relation_type = Column(String, nullable=False)
    weight = Column(Float, nullable=False, default=1.0)
    business_type = relationship("BusinessType", back_populates="relations")
    entity = relationship("OSMEntity", back_populates="relations")

TRANSPORT_TAGS = [("highway", "bus_stop"), ("railway", "station"), ("public_transport", None)]

TRANSPORT_TAGS = [("highway", "bus_stop"), ("railway", "station"), ("public_transport", None)]


def get_db():
    """Obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def obtener_negocio_db(tipo_negocio):
    """Obtiene definición completa de negocio desde base de datos"""
    db = next(get_db())

    try:
        # Buscar el tipo de negocio
        negocio = db.query(BusinessType).filter(BusinessType.nombre == tipo_negocio).first()

        if not negocio:
            return None

        # Obtener todas las relaciones del negocio
        relaciones = db.query(BusinessRelation).filter(
            BusinessRelation.business_type_id == negocio.id
        ).all()

        # Organizar relaciones por tipo
        competencia = []
        sinergia = []
        clientes = []

        for rel in relaciones:
            entity = db.query(OSMEntity).filter(OSMEntity.id == rel.osm_entity_id).first()
            if entity:
                entity_data = (entity.osm_key, entity.osm_value)

                if rel.relation_type == 'competencia':
                    competencia.append(entity_data)
                elif rel.relation_type == 'sinergia':
                    sinergia.append(entity_data)
                elif rel.relation_type == 'cliente':
                    clientes.append((entity.osm_key, entity.osm_value, rel.weight))

        return {
            "id": negocio.id,
            "nombre": negocio.nombre,
            "mu": negocio.mu,
            "sigma": negocio.sigma,
            "weights": {
                "competencia": negocio.peso_competencia,
                "potenciales_clientes": negocio.peso_clientes,
                "accesibilidad": negocio.peso_accesibilidad,
                "sinergia": negocio.peso_sinergia,
            },
            "tags": [],  # Se puede agregar lógica específica si es necesario
            "competencia": competencia,
            "sinergia": sinergia,
            "clientes": clientes
        }

    finally:
        db.close()

# =============== API ===============

def overpass_query(query, retries=2):
    """Ejecuta una consulta a Overpass API con reintentos."""
    headers = {"User-Agent": "MiAppGeoespacial/1.0"}
    for i in range(retries):
        try:
            response = requests.post(OVERPASS_URL, data=query, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json().get("elements", [])
        except Exception as e:
            if i == retries - 1:
                print(f"⚠️ Overpass error: {e}")
                return []
            time.sleep(1)


def build_query(lat, lon, tipo_negocio, radius=500):
    """
    Construye query Overpass optimizada para el tipo de negocio.
    Solo incluye tags relevantes para ese negocio + transporte.
    """
    negocio = obtener_negocio_db(tipo_negocio)
    if not negocio:
        return None
    
    filtros = set()
    filtros.update(negocio.get("tags", []))
    filtros.update(negocio.get("competencia", []))
    filtros.update(negocio.get("sinergia", []))
    filtros.update((tag, value) for tag, value, _ in negocio.get("clientes", []))
    filtros.update(TRANSPORT_TAGS)
    
    nodos = []
    for tag, value in sorted(filtros):
        if value is None:
            nodos.append(f'  nwr["{tag}"](around:{radius},{lat},{lon});')
        else:
            nodos.append(f'  nwr["{tag}"="{value}"](around:{radius},{lat},{lon});')
    
    return "[out:json];\n(\n" + "\n".join(nodos) + "\n);\nout center;"


# =============== DISTANCIA Y SCORING ===============
def haversine(lat1, lon1, lat2, lon2):
    """Calcula distancia en metros entre dos puntos."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def peso_distancia(dist):
    """Modelo de fricción por distancia."""
    return 1 / (1 + dist / 100)


def score_competencia(comp, mu, sigma):
    """Curva gaussiana para evaluar competencia."""
    return math.exp(-((comp - mu) ** 2) / (2 * sigma ** 2))


def sigmoid(x):
    """Función sigmoide para normalizar el score final."""
    return 1 / (1 + math.exp(-x))


def matches_filters(tags, filtros):
    """Verifica si los tags coinciden con alguno de los filtros."""
    for tag, value in filtros:
        if value is None and tag in tags:
            return True
        if tags.get(tag) == value:
            return True
    return False


def get_tags_negocio(tipo_negocio):
    """Retorna los tags para identificar un negocio."""
    negocio = obtener_negocio_db(tipo_negocio)
    return negocio.get("tags", []) if negocio else []


# =============== ANÁLISIS PRINCIPAL ===============

def analizar_ubicacion(lat, lon, tipo_negocio):
    """Analiza una ubicación para un tipo de negocio específico."""
    
    negocio = obtener_negocio_db(tipo_negocio)
    if not negocio:
        raise ValueError(f"Tipo de negocio '{tipo_negocio}' no soportado")
    
    # Construir y ejecutar query optimizada para este negocio
    query = build_query(lat, lon, tipo_negocio)
    if not query:
        raise ValueError(f"No se pudo construir query para '{tipo_negocio}'")
    
    elementos = overpass_query(query)
    
    # Acumuladores
    competencia = 0.0
    transporte = 0.0
    potenciales_clientes = 0.0
    sinergia = 0.0
    
    geo = {
        "competencia": [],
        "potenciales_clientes": [],
        "sinergia": [],
        "transporte": [],
    }
    
    # Procesar cada elemento OSM
    for el in elementos:
        tags = el.get("tags", {})
        lat2 = el.get("lat") or el.get("center", {}).get("lat")
        lon2 = el.get("lon") or el.get("center", {}).get("lon")
        
        if lat2 is None or lon2 is None:
            continue
        
        dist = haversine(lat, lon, lat2, lon2)
        peso = peso_distancia(dist)
        
        punto = {
            "lat": lat2,
            "lon": lon2,
            "tipo": tags.get("amenity") or tags.get("shop") or tags.get("office") or tags.get("leisure"),
            "nombre": tags.get("name", "Sin nombre"),
        }
        
        # Flags para evitar doble conteo dentro de la misma categoría
        sumo_a_clientes = False
        
        # 1. Transporte (Independiente)
        if matches_filters(tags, TRANSPORT_TAGS):
            transporte += peso
            geo["transporte"].append(punto)
        
        # 2. Clientes Potenciales (Independiente del transporte)
        for tag, value, weight in negocio.get("clientes", []):
            if (value is None and tag in tags) or (tags.get(tag) == value):
                if not sumo_a_clientes: # Solo suma una vez aunque coincida con varios tags de cliente
                    potenciales_clientes += peso * weight
                    geo["potenciales_clientes"].append(punto)
                    sumo_a_clientes = True
        
        # 3. Competencia (Independiente)
        if matches_filters(tags, negocio.get("competencia", [])):
            competencia += peso
            geo["competencia"].append(punto)
            
        # 4. Sinergia (Independiente)
        if matches_filters(tags, negocio.get("sinergia", [])):
            sinergia += peso
            geo["sinergia"].append(punto)

        # debug
        # Agrega esto temporalmente en tu bucle de elementos
        if not sumo_a_clientes and not matches_filters(tags, negocio.get("competencia", [])):
            print(f"DEBUG: Elemento no clasificado - Tags: {tags}")
    
    # Normalización de features
    features = {
        "competencia": competencia,
        "accesibilidad": min(transporte / 6, 1), # Ajustar según densidad real
        "potenciales_clientes": min(potenciales_clientes / 5, 1), 
        "sinergia": min(sinergia / 4, 1),
    }
    
    # Score de competencia no lineal
    features["competencia"] = score_competencia(
        features["competencia"],
        negocio["mu"],
        negocio["sigma"],
    )
    
    # Score final
    raw_score = sum(features[key] * negocio["weights"][key] for key in negocio["weights"])
    probabilidad = sigmoid(2 * raw_score)
    
    return {
        "probabilidad": round(probabilidad, 3),
        "features": features,
        "raw": {
            "competencia_raw": competencia,
            "transporte": transporte,
            "potenciales_clientes": potenciales_clientes,
            "sinergia": sinergia,
        },
        "geo": geo,
    }

# if __name__ == "__main__":
#     query = build_query(-34.60, -58.38)

#     print("Consultando Overpass...")
#     elements = overpass_query(query)

#     print("OK")
#     print("Cantidad:", len(elements))
