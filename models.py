# database/models.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey
)

from sqlalchemy.orm import relationship
from db.database import Base


# =====================================================
# TABLA: osm_entities
# =====================================================

class OSMEntity(Base):
    __tablename__ = "osm_entities"

    id = Column(Integer, primary_key=True, index=True)

    osm_key = Column(String, nullable=False)
    osm_value = Column(String, nullable=True)

    nombre = Column(String, nullable=False)
    categoria = Column(String, nullable=False)

    # relaciones
    relations = relationship(
        "BusinessRelation",
        back_populates="entity"
    )


# =====================================================
# TABLA: business_types
# =====================================================

class BusinessType(Base):
    __tablename__ = "business_types"

    id = Column(Integer, primary_key=True, index=True)

    nombre = Column(String, unique=True, nullable=False)

    # parámetros del modelo
    mu = Column(Float, nullable=False)
    sigma = Column(Float, nullable=False)

    # pesos del score
    peso_competencia = Column(Float, nullable=False)
    peso_clientes = Column(Float, nullable=False)
    peso_accesibilidad = Column(Float, nullable=False)
    peso_sinergia = Column(Float, nullable=False)

    # relaciones
    relations = relationship(
        "BusinessRelation",
        back_populates="business_type"
    )


# =====================================================
# TABLA: business_relations
# =====================================================

class BusinessRelation(Base):
    __tablename__ = "business_relations"

    id = Column(Integer, primary_key=True, index=True)

    # negocio al que pertenece
    business_type_id = Column(
        Integer,
        ForeignKey("business_types.id"),
        nullable=False
    )

    # entidad OSM relacionada
    osm_entity_id = Column(
        Integer,
        ForeignKey("osm_entities.id"),
        nullable=False
    )

    # competencia / sinergia / cliente
    relation_type = Column(String, nullable=False)

    # peso específico
    weight = Column(Float, nullable=False, default=1.0)

    # relaciones ORM
    business_type = relationship(
        "BusinessType",
        back_populates="relations"
    )

    entity = relationship(
        "OSMEntity",
        back_populates="relations"
    )