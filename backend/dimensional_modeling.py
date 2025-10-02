"""
Dimensional Modeling Engine
Implements algorithms to automatically identify and create star schema models
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from sql_analyzer import SQLAnalyzer, TableInfo, ColumnInfo, DimensionalRole, ColumnType
from ai_dimension_classifier import AIDimensionClassifier

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class DimensionTable:
    """Represents a dimension table in the star schema"""
    name: str
    source_table: str
    surrogate_key: str
    natural_key: str
    attributes: List[str]
    scd_type: int = 1  # Slowly Changing Dimension type
    description: str = ""


@dataclass
class FactTable:
    """Represents a fact table in the star schema"""
    name: str
    source_table: str
    measures: List[str]
    dimension_keys: List[str]
    grain: str = ""  # Business grain description
    description: str = ""


@dataclass
class StarSchema:
    """Represents a complete star schema model"""
    name: str
    fact_table: FactTable
    dimension_tables: List[DimensionTable]
    relationships: List[Dict[str, str]]
    metadata: Dict[str, Any] = field(default_factory=dict)


class DimensionalModelingEngine:
    """Engine for creating dimensional models from relational data"""
    
    def __init__(self, dialect: str = "postgresql"):
        self.sql_analyzer = SQLAnalyzer()
        self.ai_classifier = AIDimensionClassifier()
        self.star_schemas: List[StarSchema] = []
        self.dialect = dialect

        # Common dimension patterns (fallback when AI is not available)
        self.time_dimension_patterns = [
            r'.*data.*', r'.*date.*', r'.*time.*', r'.*hora.*',
            r'.*created.*', r'.*updated.*', r'.*modified.*'
        ]

        self.customer_dimension_patterns = [
            r'.*cliente.*', r'.*customer.*', r'.*person.*', r'.*pessoa.*',
            r'.*user.*', r'.*usuario.*'
        ]

        self.product_dimension_patterns = [
            r'.*produto.*', r'.*product.*', r'.*item.*', r'.*servico.*',
            r'.*service.*', r'.*material.*'
        ]

        self.location_dimension_patterns = [
            r'.*local.*', r'.*location.*', r'.*endereco.*', r'.*address.*',
            r'.*cidade.*', r'.*city.*', r'.*estado.*', r'.*state.*'
        ]

    def create_dimensional_model(self, sql_content: str, model_name: str = "DataWarehouse") -> Dict[str, Any]:
        """Create a dimensional model from SQL content"""
        logger.info(f"🏗️ [DIM MODEL] Starting dimensional model creation for: {model_name}")
        logger.info(f"🏗️ [DIM MODEL] SQL content length: {len(sql_content)} characters")

        try:
            # Analyze SQL structure
            logger.info("🔍 [DIM MODEL] Analyzing SQL structure...")
            analysis = self.sql_analyzer.parse_sql(sql_content)
            logger.info(f"🔍 [DIM MODEL] SQL analysis completed, keys: {list(analysis.keys())}")

            if "error" in analysis:
                logger.error(f"❌ [DIM MODEL] SQL analysis error: {analysis['error']}")
                return {"error": analysis["error"]}

            # Log analysis details
            tables = analysis.get("tables", [])
            logger.info(f"🔍 [DIM MODEL] Found {len(tables)} tables in analysis")
            for i, table in enumerate(tables):
                logger.info(f"🔍 [DIM MODEL] Table {i+1}: {table.get('name', 'unknown')} with {len(table.get('columns', []))} columns")

            # Generate star schema
            logger.info("⭐ [DIM MODEL] Generating star schema...")
            star_schema = self._generate_star_schema(analysis, model_name)

            if not star_schema:
                logger.error("❌ [DIM MODEL] Could not generate a valid star schema")
                return {"error": "Could not generate a valid star schema from the provided SQL"}

            logger.info(f"✅ [DIM MODEL] Star schema generated successfully")
            logger.info(f"⭐ [DIM MODEL] Fact table: {star_schema.fact_table.name}")
            logger.info(f"⭐ [DIM MODEL] Dimension tables: {len(star_schema.dimension_tables)}")

            # Add star schema to the list for later use
            self.star_schemas.append(star_schema)
            logger.info(f"⭐ [DIM MODEL] Star schema added to engine list. Total schemas: {len(self.star_schemas)}")

            # Generate DDL for the star schema
            logger.info("📝 [DIM MODEL] Generating DDL statements...")
            ddl_statements = self._generate_star_schema_ddl(star_schema)
            logger.info(f"📝 [DIM MODEL] Generated {len(ddl_statements)} DDL statements")

            result = {
                "success": True,
                "star_schema": self._star_schema_to_dict(star_schema),
                "ddl_statements": ddl_statements,
                "original_analysis": analysis,
                "recommendations": self._generate_modeling_recommendations(star_schema, analysis)
            }

            logger.info("✅ [DIM MODEL] Dimensional model creation completed successfully")
            return result

        except Exception as e:
            logger.error(f"❌ [DIM MODEL] Error creating dimensional model: {str(e)}")
            import traceback
            logger.error(f"🔍 [DIM MODEL] Full error traceback:")
            logger.error(traceback.format_exc())
            return {"error": f"Error creating dimensional model: {str(e)}"}

    def _generate_star_schema(self, analysis: Dict[str, Any], model_name: str) -> Optional[StarSchema]:
        """Generate star schema from analysis results"""
        tables = analysis.get("tables", [])
        dimensional_analysis = analysis.get("dimensional_analysis", {})

        if not tables:
            return None

        # If single table, denormalize into star schema
        if len(tables) == 1:
            return self._denormalize_single_table(tables[0], model_name)
        
        # Multiple tables - identify fact and dimension candidates
        fact_candidates = dimensional_analysis.get("fact_candidates", [])
        dimension_candidates = dimensional_analysis.get("dimension_candidates", [])
        
        if not fact_candidates:
            # Try to create fact table from the table with most measures
            fact_table = self._identify_best_fact_candidate(tables)
            if not fact_table:
                return self._denormalize_single_table(tables[0], model_name)
        else:
            fact_table = self._create_fact_table(fact_candidates[0])
        
        # Create dimension tables
        dimension_tables = []
        for dim_candidate in dimension_candidates:
            dim_table = self._create_dimension_table(dim_candidate)
            if dim_table:
                dimension_tables.append(dim_table)
        
        # Add time dimension if not present
        if not any(self._is_time_dimension(dim) for dim in dimension_tables):
            time_dim = self._create_time_dimension()
            dimension_tables.append(time_dim)
        
        # Create relationships
        relationships = self._create_relationships(fact_table, dimension_tables)
        
        return StarSchema(
            name=model_name,
            fact_table=fact_table,
            dimension_tables=dimension_tables,
            relationships=relationships,
            metadata={
                "created_at": datetime.now().isoformat(),
                "source_tables": len(tables),
                "modeling_approach": "multi_table" if len(tables) > 1 else "single_table"
            }
        )

    def _denormalize_single_table(self, table_data: Dict[str, Any], model_name: str) -> StarSchema:
        """Create star schema by denormalizing a single table using AI classification"""
        table_name = table_data["name"]
        columns = table_data["columns"]

        logger.info(f"🔄 [DENORMALIZE] Starting denormalization for table: {table_name}")
        logger.info(f"🔄 [DENORMALIZE] Table has {len(columns)} columns")

        # Log column details
        for i, col in enumerate(columns):
            logger.info(f"🔄 [DENORMALIZE] Column {i+1}: {col.get('name', 'unknown')} ({col.get('data_type', 'unknown')})")

        # Use AI to classify dimensions
        logger.info("🤖 [DENORMALIZE] Calling AI classifier...")
        ai_classifications = self.ai_classifier.classify_table_dimensions(table_name, columns)
        logger.info(f"🤖 [DENORMALIZE] AI classifier returned {len(ai_classifications)} classifications")

        # Process AI classifications
        measures = []
        dimension_attributes = {}
        time_columns = []

        logger.info("🔄 [DENORMALIZE] Processing AI classifications...")
        for i, classification in enumerate(ai_classifications):
            col_name = classification.column_name
            dim_role = classification.dimensional_role
            dim_type = classification.dimension_type
            confidence = classification.confidence

            logger.info(f"🔄 [DENORMALIZE] Classification {i+1}: {col_name} -> {dim_type}/{dim_role} (confidence: {confidence})")

            if dim_role == "fact_measure":
                measures.append(col_name)
                logger.info(f"📊 [DENORMALIZE] Added measure: {col_name}")
            elif dim_role == "time_dimension":
                time_columns.append(col_name)
                logger.info(f"⏰ [DENORMALIZE] Added time column: {col_name}")
            elif dim_role in ["dimension_attribute", "dimension_key"]:
                if dim_type not in dimension_attributes:
                    dimension_attributes[dim_type] = []
                dimension_attributes[dim_type].append(col_name)
                logger.info(f"🏷️ [DENORMALIZE] Added dimension attribute: {col_name} to {dim_type}")

        logger.info(f"📊 [DENORMALIZE] Summary - Measures: {len(measures)}, Time columns: {len(time_columns)}, Dimension types: {len(dimension_attributes)}")
        logger.info(f"📊 [DENORMALIZE] Measures: {measures}")
        logger.info(f"📊 [DENORMALIZE] Dimension attributes: {dimension_attributes}")

        # If no explicit measures found, create implicit measures for event counting
        if not measures:
            measures = ["visit_count"]  # Implicit measure for counting visits/events

        # Create fact table
        fact_table = FactTable(
            name=f"fact_{table_name}",
            source_table=table_name,
            measures=measures,
            dimension_keys=[],
            grain=f"One row per {table_name} record",
            description=f"Fact table derived from {table_name}"
        )
        
        # Create dimension tables
        dimension_tables = []
        
        # Create specific dimension tables
        for dim_type, attributes in dimension_attributes.items():
            if attributes:
                dim_table = DimensionTable(
                    name=f"dim_{dim_type}",
                    source_table=table_name,
                    surrogate_key=f"{dim_type}_sk",
                    natural_key=attributes[0],  # Use first attribute as natural key
                    attributes=attributes,
                    description=f"{dim_type.title()} dimension"
                )
                dimension_tables.append(dim_table)
                fact_table.dimension_keys.append(f"{dim_type}_sk")
        
        # Add time dimension
        time_dim = self._create_time_dimension()
        dimension_tables.append(time_dim)
        fact_table.dimension_keys.append("date_sk")
        
        # Create relationships
        relationships = self._create_relationships(fact_table, dimension_tables)

        return StarSchema(
            name=model_name,
            fact_table=fact_table,
            dimension_tables=dimension_tables,
            relationships=relationships,
            metadata={
                "created_at": datetime.now().isoformat(),
                "source_tables": 1,
                "modeling_approach": "denormalization"
            }
        )

    def _classify_dimension_type(self, column_name: str) -> str:
        """Classify dimension type based on column name"""
        column_lower = column_name.lower()

        # Enhanced patterns for access control data
        if any(word in column_lower for word in ['nome', 'name', 'cpf', 'email', 'telefone', 'phone', 'pessoa', 'person']):
            return "person"
        elif any(word in column_lower for word in ['tipo', 'type', 'categoria', 'category', 'visita', 'visit']):
            return "visit_type"
        elif any(word in column_lower for word in ['bloco', 'block', 'apartamento', 'apartment', 'local', 'location']):
            return "location"
        elif any(word in column_lower for word in ['veiculo', 'vehicle', 'placa', 'plate', 'carro', 'car']):
            return "vehicle"
        elif any(word in column_lower for word in ['motivo', 'reason', 'observacao', 'observation', 'comment']):
            return "activity"
        elif any(re.search(pattern, column_lower) for pattern in self.customer_dimension_patterns):
            return "customer"
        elif any(re.search(pattern, column_lower) for pattern in self.product_dimension_patterns):
            return "product"
        elif any(re.search(pattern, column_lower) for pattern in self.location_dimension_patterns):
            return "location"
        elif any(re.search(pattern, column_lower) for pattern in self.time_dimension_patterns):
            return "time"
        else:
            # Generic dimension based on column name
            return column_name.replace("_", "").replace(" ", "").lower()

    def _identify_best_fact_candidate(self, tables: List[Dict[str, Any]]) -> Optional[FactTable]:
        """Identify the best fact table candidate from multiple tables"""
        best_table = None
        max_measures = 0
        
        for table in tables:
            measures = [col for col in table["columns"] if col["dimensional_role"] == "fact_measure"]
            if len(measures) > max_measures:
                max_measures = len(measures)
                best_table = table
        
        if best_table:
            return self._create_fact_table({
                "table_name": best_table["name"],
                "measures": [col["name"] for col in best_table["columns"] if col["dimensional_role"] == "fact_measure"],
                "dimension_keys": [col["name"] for col in best_table["columns"] if col["dimensional_role"] == "dimension_key"]
            })
        
        return None

    def _create_fact_table(self, fact_candidate: Dict[str, Any]) -> FactTable:
        """Create fact table from candidate"""
        return FactTable(
            name=f"fact_{fact_candidate['table_name']}",
            source_table=fact_candidate["table_name"],
            measures=fact_candidate["measures"],
            dimension_keys=fact_candidate["dimension_keys"],
            grain=f"One row per {fact_candidate['table_name']} transaction",
            description=f"Fact table for {fact_candidate['table_name']} business process"
        )

    def _create_dimension_table(self, dim_candidate: Dict[str, Any]) -> Optional[DimensionTable]:
        """Create dimension table from candidate"""
        if not dim_candidate.get("attributes"):
            return None
        
        return DimensionTable(
            name=f"dim_{dim_candidate['table_name']}",
            source_table=dim_candidate["table_name"],
            surrogate_key=f"{dim_candidate['table_name']}_sk",
            natural_key=dim_candidate.get("key_column", dim_candidate["attributes"][0]),
            attributes=dim_candidate["attributes"],
            description=f"Dimension table for {dim_candidate['table_name']}"
        )

    def _create_time_dimension(self) -> DimensionTable:
        """Create standard time dimension"""
        return DimensionTable(
            name="dim_date",
            source_table="generated",
            surrogate_key="date_sk",
            natural_key="date_key",
            attributes=[
                "date_key", "full_date", "day_of_week", "day_name",
                "day_of_month", "day_of_year", "week_of_year",
                "month_number", "month_name", "quarter", "year",
                "is_weekend", "is_holiday"
            ],
            description="Standard date dimension table"
        )

    def _is_time_dimension(self, dimension: DimensionTable) -> bool:
        """Check if dimension is a time dimension"""
        return "date" in dimension.name.lower() or "time" in dimension.name.lower()

    def _create_relationships(self, fact_table: FactTable, dimension_tables: List[DimensionTable]) -> List[Dict[str, str]]:
        """Create relationships between fact and dimension tables"""
        relationships = []
        
        for dim_table in dimension_tables:
            relationships.append({
                "from_table": fact_table.name,
                "from_column": dim_table.surrogate_key,
                "to_table": dim_table.name,
                "to_column": dim_table.surrogate_key,
                "relationship_type": "many_to_one"
            })
        
        return relationships

    def _generate_star_schema_ddl(self, star_schema: StarSchema) -> List[str]:
        """Generate DDL statements for the star schema"""
        ddl_statements = []
        
        # Generate dimension table DDLs
        for dim_table in star_schema.dimension_tables:
            ddl = self._generate_dimension_ddl(dim_table)
            ddl_statements.append(ddl)
        
        # Generate fact table DDL
        fact_ddl = self._generate_fact_ddl(star_schema.fact_table, star_schema.dimension_tables)
        ddl_statements.append(fact_ddl)
        
        return ddl_statements

    def _generate_dimension_ddl(self, dim_table: DimensionTable) -> str:
        """Generate DDL for dimension table"""
        ddl = f"-- {dim_table.description}\n"
        ddl += f"CREATE TABLE {dim_table.name} (\n"
        ddl += f"    {dim_table.surrogate_key} BIGSERIAL PRIMARY KEY,\n"
        
        for attr in dim_table.attributes:
            if attr == dim_table.natural_key:
                ddl += f"    {attr} VARCHAR(50) NOT NULL,\n"
            else:
                ddl += f"    {attr} VARCHAR(255),\n"
        
        # Add SCD columns for Type 2
        if dim_table.scd_type == 2:
            ddl += "    effective_date DATE NOT NULL,\n"
            ddl += "    expiry_date DATE,\n"
            ddl += "    is_current BOOLEAN DEFAULT TRUE,\n"
        
        ddl += "    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,\n"
        ddl += "    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP\n"
        ddl += ");\n\n"
        
        # Add indexes
        ddl += f"CREATE INDEX idx_{dim_table.name}_{dim_table.natural_key} ON {dim_table.name}({dim_table.natural_key});\n\n"
        
        return ddl

    def _generate_fact_ddl(self, fact_table: FactTable, dimension_tables: List[DimensionTable]) -> str:
        """Generate DDL for fact table"""
        ddl = f"-- {fact_table.description}\n"
        ddl += f"CREATE TABLE {fact_table.name} (\n"
        
        # Add dimension foreign keys
        for dim_table in dimension_tables:
            ddl += f"    {dim_table.surrogate_key} BIGINT NOT NULL,\n"

        # Add measures
        for measure in fact_table.measures:
            ddl += f"    {measure} NUMERIC(18,2),\n"

        ddl += "    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,\n"
        ddl += "    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,\n"
        
        # Add composite primary key
        pk_columns = [dim.surrogate_key for dim in dimension_tables]
        ddl += f"    PRIMARY KEY ({', '.join(pk_columns)})\n"
        ddl += ");\n\n"
        
        # Add foreign key constraints
        for dim_table in dimension_tables:
            ddl += f"ALTER TABLE {fact_table.name} ADD CONSTRAINT fk_{fact_table.name}_{dim_table.name} "
            ddl += f"FOREIGN KEY ({dim_table.surrogate_key}) REFERENCES {dim_table.name}({dim_table.surrogate_key});\n"
        
        ddl += "\n"
        return ddl

    def _generate_modeling_recommendations(self, star_schema: StarSchema, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for the dimensional model"""
        recommendations = []
        
        # Check for missing dimensions
        if len(star_schema.dimension_tables) < 3:
            recommendations.append("Consider adding more dimension tables for better analytical capabilities")
        
        # Check for fact table measures
        if len(star_schema.fact_table.measures) < 2:
            recommendations.append("Consider adding more measures to the fact table for richer analytics")
        
        # Check for time dimension
        if not any(self._is_time_dimension(dim) for dim in star_schema.dimension_tables):
            recommendations.append("Consider adding a time dimension for temporal analysis")
        
        # Check for SCD implementation
        recommendations.append("Consider implementing Slowly Changing Dimensions (SCD) for historical tracking")
        
        return recommendations

    def _star_schema_to_dict(self, star_schema: StarSchema) -> Dict[str, Any]:
        """Convert StarSchema to dictionary for JSON serialization"""
        return {
            "name": star_schema.name,
            "fact_table": {
                "name": star_schema.fact_table.name,
                "source_table": star_schema.fact_table.source_table,
                "measures": star_schema.fact_table.measures,
                "dimension_keys": star_schema.fact_table.dimension_keys,
                "grain": star_schema.fact_table.grain,
                "description": star_schema.fact_table.description
            },
            "dimension_tables": [
                {
                    "name": dim.name,
                    "source_table": dim.source_table,
                    "surrogate_key": dim.surrogate_key,
                    "natural_key": dim.natural_key,
                    "attributes": dim.attributes,
                    "scd_type": dim.scd_type,
                    "description": dim.description
                }
                for dim in star_schema.dimension_tables
            ],
            "relationships": star_schema.relationships,
            "metadata": star_schema.metadata
        }
