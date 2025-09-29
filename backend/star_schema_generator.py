"""
Star Schema Generator
Advanced DDL generation for optimized data warehouse schemas
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from dimensional_modeling import StarSchema, FactTable, DimensionTable


class DatabaseDialect(Enum):
    """Supported database dialects for DDL generation"""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLSERVER = "sqlserver"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"
    REDSHIFT = "redshift"


@dataclass
class IndexDefinition:
    """Definition for database indexes"""
    name: str
    table_name: str
    columns: List[str]
    index_type: str = "BTREE"  # BTREE, HASH, BITMAP
    is_unique: bool = False
    is_clustered: bool = False


@dataclass
class PartitionDefinition:
    """Definition for table partitioning"""
    partition_type: str  # RANGE, LIST, HASH
    partition_column: str
    partition_values: List[str] = None


class StarSchemaGenerator:
    """Generates optimized DDL for star schema implementations"""
    
    def __init__(self, dialect: DatabaseDialect = DatabaseDialect.MYSQL):
        self.dialect = dialect
        self.type_mappings = self._get_type_mappings()
        
    def _get_type_mappings(self) -> Dict[str, Dict[str, str]]:
        """Get data type mappings for different database dialects"""
        return {
            DatabaseDialect.MYSQL.value: {
                "surrogate_key": "BIGINT AUTO_INCREMENT",
                "natural_key": "VARCHAR(100)",
                "string": "VARCHAR(255)",
                "text": "TEXT",
                "integer": "INT",
                "bigint": "BIGINT",
                "decimal": "DECIMAL(18,2)",
                "date": "DATE",
                "datetime": "DATETIME",
                "timestamp": "TIMESTAMP",
                "boolean": "BOOLEAN"
            },
            DatabaseDialect.POSTGRESQL.value: {
                "surrogate_key": "BIGSERIAL",
                "natural_key": "VARCHAR(100)",
                "string": "VARCHAR(255)",
                "text": "TEXT",
                "integer": "INTEGER",
                "bigint": "BIGINT",
                "decimal": "NUMERIC(18,2)",
                "date": "DATE",
                "datetime": "TIMESTAMP",
                "timestamp": "TIMESTAMP WITH TIME ZONE",
                "boolean": "BOOLEAN"
            },
            DatabaseDialect.SQLSERVER.value: {
                "surrogate_key": "BIGINT IDENTITY(1,1)",
                "natural_key": "NVARCHAR(100)",
                "string": "NVARCHAR(255)",
                "text": "NVARCHAR(MAX)",
                "integer": "INT",
                "bigint": "BIGINT",
                "decimal": "DECIMAL(18,2)",
                "date": "DATE",
                "datetime": "DATETIME2",
                "timestamp": "DATETIME2",
                "boolean": "BIT"
            },
            DatabaseDialect.SNOWFLAKE.value: {
                "surrogate_key": "NUMBER AUTOINCREMENT",
                "natural_key": "VARCHAR(100)",
                "string": "VARCHAR(255)",
                "text": "VARCHAR(16777216)",
                "integer": "NUMBER(10,0)",
                "bigint": "NUMBER(19,0)",
                "decimal": "NUMBER(18,2)",
                "date": "DATE",
                "datetime": "TIMESTAMP_NTZ",
                "timestamp": "TIMESTAMP_TZ",
                "boolean": "BOOLEAN"
            }
        }
    
    def generate_complete_schema(self, star_schema: StarSchema, 
                               include_indexes: bool = True,
                               include_partitioning: bool = False,
                               include_constraints: bool = True) -> Dict[str, Any]:
        """Generate complete DDL for star schema"""
        
        result = {
            "schema_name": star_schema.name,
            "dialect": self.dialect.value,
            "ddl_statements": [],
            "indexes": [],
            "constraints": [],
            "partitions": [],
            "metadata": {
                "generated_at": "2024-01-01T00:00:00Z",
                "tables_count": len(star_schema.dimension_tables) + 1,
                "estimated_size": self._estimate_schema_size(star_schema)
            }
        }
        
        # Generate dimension tables
        for dim_table in star_schema.dimension_tables:
            dim_ddl = self._generate_dimension_table_ddl(dim_table)
            result["ddl_statements"].append(dim_ddl)
            
            if include_indexes:
                indexes = self._generate_dimension_indexes(dim_table)
                result["indexes"].extend(indexes)
        
        # Generate fact table
        fact_ddl = self._generate_fact_table_ddl(star_schema.fact_table, star_schema.dimension_tables)
        result["ddl_statements"].append(fact_ddl)
        
        if include_indexes:
            fact_indexes = self._generate_fact_indexes(star_schema.fact_table, star_schema.dimension_tables)
            result["indexes"].extend(fact_indexes)
        
        # Generate constraints
        if include_constraints:
            constraints = self._generate_foreign_key_constraints(star_schema)
            result["constraints"].extend(constraints)
        
        # Generate partitioning
        if include_partitioning:
            partitions = self._generate_partitioning_strategy(star_schema)
            result["partitions"].extend(partitions)
        
        # Generate views and procedures
        views = self._generate_analytical_views(star_schema)
        result["ddl_statements"].extend(views)
        
        return result
    
    def _generate_dimension_table_ddl(self, dim_table: DimensionTable) -> str:
        """Generate DDL for dimension table"""
        type_map = self.type_mappings[self.dialect.value]
        
        ddl = f"-- {dim_table.description}\n"
        ddl += f"CREATE TABLE {dim_table.name} (\n"
        
        # Surrogate key
        ddl += f"    {dim_table.surrogate_key} {type_map['surrogate_key']} PRIMARY KEY,\n"
        
        # Natural key
        ddl += f"    {dim_table.natural_key} {type_map['natural_key']} NOT NULL,\n"
        
        # Attributes
        for attr in dim_table.attributes:
            if attr not in [dim_table.surrogate_key, dim_table.natural_key]:
                data_type = self._infer_attribute_type(attr)
                ddl += f"    {attr} {type_map.get(data_type, type_map['string'])},\n"
        
        # SCD Type 2 columns
        if dim_table.scd_type == 2:
            ddl += f"    effective_date {type_map['date']} NOT NULL,\n"
            ddl += f"    expiry_date {type_map['date']},\n"
            ddl += f"    is_current {type_map['boolean']} DEFAULT TRUE,\n"
            ddl += f"    version_number {type_map['integer']} DEFAULT 1,\n"
        
        # Audit columns
        ddl += f"    created_at {type_map['timestamp']} DEFAULT CURRENT_TIMESTAMP,\n"
        ddl += f"    updated_at {type_map['timestamp']} DEFAULT CURRENT_TIMESTAMP,\n"
        ddl += f"    created_by {type_map['string']} DEFAULT 'ETL_PROCESS',\n"
        ddl += f"    updated_by {type_map['string']} DEFAULT 'ETL_PROCESS'\n"
        
        ddl += ");\n\n"
        
        # Add comments
        ddl += f"COMMENT ON TABLE {dim_table.name} IS '{dim_table.description}';\n"
        ddl += f"COMMENT ON COLUMN {dim_table.name}.{dim_table.surrogate_key} IS 'Surrogate key for {dim_table.name}';\n"
        ddl += f"COMMENT ON COLUMN {dim_table.name}.{dim_table.natural_key} IS 'Natural business key';\n\n"
        
        return ddl
    
    def _generate_fact_table_ddl(self, fact_table: FactTable, dimension_tables: List[DimensionTable]) -> str:
        """Generate DDL for fact table"""
        type_map = self.type_mappings[self.dialect.value]
        
        ddl = f"-- {fact_table.description}\n"
        ddl += f"-- Grain: {fact_table.grain}\n"
        ddl += f"CREATE TABLE {fact_table.name} (\n"
        
        # Dimension foreign keys
        for dim_table in dimension_tables:
            ddl += f"    {dim_table.surrogate_key} {type_map['bigint']} NOT NULL,\n"
        
        # Measures
        for measure in fact_table.measures:
            measure_type = self._infer_measure_type(measure)
            ddl += f"    {measure} {type_map.get(measure_type, type_map['decimal'])},\n"
        
        # Degenerate dimensions (if any)
        ddl += f"    transaction_id {type_map['string']},\n"
        ddl += f"    source_system {type_map['string']} DEFAULT 'MAIN_SYSTEM',\n"
        
        # Audit columns
        ddl += f"    created_at {type_map['timestamp']} DEFAULT CURRENT_TIMESTAMP,\n"
        ddl += f"    updated_at {type_map['timestamp']} DEFAULT CURRENT_TIMESTAMP,\n"
        ddl += f"    etl_batch_id {type_map['bigint']},\n"
        ddl += f"    data_quality_score {type_map['decimal']}\n"
        
        ddl += ");\n\n"
        
        # Add table comment
        ddl += f"COMMENT ON TABLE {fact_table.name} IS '{fact_table.description}';\n\n"
        
        return ddl
    
    def _generate_dimension_indexes(self, dim_table: DimensionTable) -> List[str]:
        """Generate indexes for dimension table"""
        indexes = []
        type_map = self.type_mappings[self.dialect.value]
        
        # Natural key index
        indexes.append(f"CREATE UNIQUE INDEX idx_{dim_table.name}_{dim_table.natural_key} ON {dim_table.name}({dim_table.natural_key});")
        
        # SCD Type 2 indexes
        if dim_table.scd_type == 2:
            indexes.append(f"CREATE INDEX idx_{dim_table.name}_current ON {dim_table.name}(is_current, {dim_table.natural_key});")
            indexes.append(f"CREATE INDEX idx_{dim_table.name}_effective ON {dim_table.name}(effective_date, expiry_date);")
        
        # Attribute indexes for commonly queried fields
        searchable_attributes = [attr for attr in dim_table.attributes 
                               if any(keyword in attr.lower() for keyword in ['name', 'code', 'type', 'status'])]
        
        for attr in searchable_attributes[:3]:  # Limit to 3 most important
            indexes.append(f"CREATE INDEX idx_{dim_table.name}_{attr} ON {dim_table.name}({attr});")
        
        return indexes
    
    def _generate_fact_indexes(self, fact_table: FactTable, dimension_tables: List[DimensionTable]) -> List[str]:
        """Generate indexes for fact table"""
        indexes = []
        
        # Composite index on all dimension keys
        dim_keys = [dim.surrogate_key for dim in dimension_tables]
        indexes.append(f"CREATE INDEX idx_{fact_table.name}_dims ON {fact_table.name}({', '.join(dim_keys)});")
        
        # Individual dimension key indexes
        for dim_table in dimension_tables:
            indexes.append(f"CREATE INDEX idx_{fact_table.name}_{dim_table.surrogate_key} ON {fact_table.name}({dim_table.surrogate_key});")
        
        # Date dimension index (if exists)
        date_keys = [dim.surrogate_key for dim in dimension_tables if 'date' in dim.name.lower()]
        if date_keys:
            indexes.append(f"CREATE INDEX idx_{fact_table.name}_date ON {fact_table.name}({date_keys[0]});")
        
        # ETL batch index
        indexes.append(f"CREATE INDEX idx_{fact_table.name}_etl_batch ON {fact_table.name}(etl_batch_id);")
        
        return indexes
    
    def _generate_foreign_key_constraints(self, star_schema: StarSchema) -> List[str]:
        """Generate foreign key constraints"""
        constraints = []
        
        for dim_table in star_schema.dimension_tables:
            constraint_name = f"fk_{star_schema.fact_table.name}_{dim_table.name}"
            constraint = (f"ALTER TABLE {star_schema.fact_table.name} "
                         f"ADD CONSTRAINT {constraint_name} "
                         f"FOREIGN KEY ({dim_table.surrogate_key}) "
                         f"REFERENCES {dim_table.name}({dim_table.surrogate_key});")
            constraints.append(constraint)
        
        return constraints
    
    def _generate_partitioning_strategy(self, star_schema: StarSchema) -> List[str]:
        """Generate partitioning strategy for large tables"""
        partitions = []
        
        # Partition fact table by date if date dimension exists
        date_dims = [dim for dim in star_schema.dimension_tables if 'date' in dim.name.lower()]
        
        if date_dims and self.dialect in [DatabaseDialect.POSTGRESQL, DatabaseDialect.MYSQL]:
            date_key = date_dims[0].surrogate_key
            partition_ddl = f"""
-- Partition fact table by date for better performance
ALTER TABLE {star_schema.fact_table.name} 
PARTITION BY RANGE ({date_key}) (
    PARTITION p_2023 VALUES LESS THAN (20240101),
    PARTITION p_2024 VALUES LESS THAN (20250101),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);"""
            partitions.append(partition_ddl)
        
        return partitions
    
    def _generate_analytical_views(self, star_schema: StarSchema) -> List[str]:
        """Generate analytical views for common queries"""
        views = []
        
        # Generate a summary view
        dim_joins = []
        dim_selects = []
        
        for dim_table in star_schema.dimension_tables:
            alias = dim_table.name.replace('dim_', '')
            dim_joins.append(f"LEFT JOIN {dim_table.name} {alias} ON f.{dim_table.surrogate_key} = {alias}.{dim_table.surrogate_key}")
            
            # Add key attributes to select
            key_attrs = [attr for attr in dim_table.attributes[:3]]  # First 3 attributes
            for attr in key_attrs:
                dim_selects.append(f"{alias}.{attr}")
        
        measures_select = ', '.join([f"SUM(f.{measure}) as total_{measure}" for measure in star_schema.fact_table.measures])
        
        view_ddl = f"""
-- Analytical summary view
CREATE VIEW vw_{star_schema.fact_table.name}_summary AS
SELECT 
    {', '.join(dim_selects)},
    {measures_select},
    COUNT(*) as record_count
FROM {star_schema.fact_table.name} f
{chr(10).join(dim_joins)}
GROUP BY {', '.join(dim_selects)};
"""
        views.append(view_ddl)
        
        return views
    
    def _infer_attribute_type(self, attribute_name: str) -> str:
        """Infer data type for dimension attribute"""
        attr_lower = attribute_name.lower()
        
        if any(keyword in attr_lower for keyword in ['date', 'time', 'created', 'updated']):
            return 'datetime'
        elif any(keyword in attr_lower for keyword in ['id', 'key', 'number']):
            return 'bigint'
        elif any(keyword in attr_lower for keyword in ['amount', 'price', 'cost', 'value']):
            return 'decimal'
        elif any(keyword in attr_lower for keyword in ['flag', 'is_', 'has_']):
            return 'boolean'
        elif any(keyword in attr_lower for keyword in ['description', 'comment', 'note']):
            return 'text'
        else:
            return 'string'
    
    def _infer_measure_type(self, measure_name: str) -> str:
        """Infer data type for fact measure"""
        measure_lower = measure_name.lower()
        
        if any(keyword in measure_lower for keyword in ['count', 'quantity', 'qty']):
            return 'bigint'
        else:
            return 'decimal'
    
    def _estimate_schema_size(self, star_schema: StarSchema) -> Dict[str, str]:
        """Estimate schema size and complexity"""
        return {
            "complexity": "medium",
            "estimated_fact_rows": "1M-10M",
            "estimated_total_size": "1-10 GB",
            "maintenance_level": "low"
        }
    
    def generate_etl_templates(self, star_schema: StarSchema) -> Dict[str, str]:
        """Generate ETL template scripts"""
        templates = {}
        
        # Dimension load template
        for dim_table in star_schema.dimension_tables:
            if dim_table.source_table != "generated":
                templates[f"load_{dim_table.name}"] = self._generate_dimension_etl(dim_table)
        
        # Fact load template
        templates[f"load_{star_schema.fact_table.name}"] = self._generate_fact_etl(star_schema)
        
        return templates
    
    def _generate_dimension_etl(self, dim_table: DimensionTable) -> str:
        """Generate ETL template for dimension table"""
        if dim_table.scd_type == 1:
            return f"""
-- SCD Type 1 ETL for {dim_table.name}
MERGE {dim_table.name} AS target
USING (SELECT * FROM staging.{dim_table.source_table}) AS source
ON target.{dim_table.natural_key} = source.{dim_table.natural_key}
WHEN MATCHED THEN
    UPDATE SET {', '.join([f'{attr} = source.{attr}' for attr in dim_table.attributes if attr != dim_table.natural_key])},
               updated_at = CURRENT_TIMESTAMP
WHEN NOT MATCHED THEN
    INSERT ({', '.join(dim_table.attributes)}, created_at, updated_at)
    VALUES ({', '.join([f'source.{attr}' for attr in dim_table.attributes])}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
"""
        else:
            return f"""
-- SCD Type 2 ETL for {dim_table.name}
-- Implementation requires more complex logic for historical tracking
-- This is a simplified template
INSERT INTO {dim_table.name} ({', '.join(dim_table.attributes)}, effective_date, is_current, created_at)
SELECT {', '.join(dim_table.attributes)}, CURRENT_DATE, TRUE, CURRENT_TIMESTAMP
FROM staging.{dim_table.source_table}
WHERE NOT EXISTS (
    SELECT 1 FROM {dim_table.name} 
    WHERE {dim_table.natural_key} = staging.{dim_table.source_table}.{dim_table.natural_key}
    AND is_current = TRUE
);
"""
    
    def _generate_fact_etl(self, star_schema: StarSchema) -> str:
        """Generate ETL template for fact table"""
        dim_lookups = []
        for dim_table in star_schema.dimension_tables:
            if dim_table.source_table != "generated":
                dim_lookups.append(f"JOIN {dim_table.name} {dim_table.name.replace('dim_', '')} ON source.{dim_table.natural_key} = {dim_table.name.replace('dim_', '')}.{dim_table.natural_key}")
        
        return f"""
-- Fact table ETL for {star_schema.fact_table.name}
INSERT INTO {star_schema.fact_table.name} (
    {', '.join([dim.surrogate_key for dim in star_schema.dimension_tables])},
    {', '.join(star_schema.fact_table.measures)},
    created_at, etl_batch_id
)
SELECT 
    {', '.join([f"{dim.name.replace('dim_', '')}.{dim.surrogate_key}" for dim in star_schema.dimension_tables])},
    {', '.join([f"source.{measure}" for measure in star_schema.fact_table.measures])},
    CURRENT_TIMESTAMP,
    @batch_id
FROM staging.{star_schema.fact_table.source_table} source
{chr(10).join(dim_lookups)};
"""
