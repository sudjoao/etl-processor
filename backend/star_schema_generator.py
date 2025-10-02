"""
Star Schema Generator
Advanced DDL generation for PostgreSQL data warehouse schemas
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from dimensional_modeling import StarSchema, FactTable, DimensionTable


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
    """Generates optimized DDL for PostgreSQL star schema implementations"""

    def __init__(self):
        self.type_mappings = self._get_type_mappings()

    def _quote_identifier(self, identifier: str) -> str:
        """Return identifier without quotes (PostgreSQL standard identifiers)"""
        return identifier

    def _get_type_mappings(self) -> Dict[str, str]:
        """Get PostgreSQL data type mappings"""
        return {
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
            "boolean": "BOOLEAN",
            "tinyint": "SMALLINT",
            "mediumtext": "TEXT",
            "longtext": "TEXT",
            "double": "DOUBLE PRECISION",
            "float": "REAL",
            "json": "JSONB",
            "uuid": "UUID"
        }
    
    def generate_complete_schema(self, star_schema: StarSchema,
                               include_indexes: bool = True,
                               include_partitioning: bool = False,
                               include_constraints: bool = True,
                               include_sample_data: bool = False,
                               sample_records: int = 10,
                               original_sql: str = None) -> Dict[str, Any]:
        """Generate complete DDL and DML for star schema"""

        result = {
            "schema_name": star_schema.name,
            "dialect": "postgresql",
            "ddl_statements": [],
            "dml_statements": {},
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

        # Generate DML statements
        if include_sample_data or original_sql:
            sample_dml = self.generate_sample_dml(star_schema, sample_records, original_sql)
            result["dml_statements"] = sample_dml

        return result
    
    def _generate_dimension_table_ddl(self, dim_table: DimensionTable) -> str:
        """Generate DDL for dimension table"""
        type_map = self.type_mappings
        
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
        type_map = self.type_mappings
        
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
        
        if date_dims:  # PostgreSQL supports partitioning
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

    def generate_sample_dml(self, star_schema: StarSchema, num_records: int = 10, original_sql: str = None) -> Dict[str, str]:
        """Generate DML statements for the star schema using real data when available"""
        dml_statements = {}

        # Extract real data from original SQL if provided
        real_data = {}
        if original_sql:
            real_data = self._extract_real_data_from_sql(original_sql)

        # Only generate DML if we have real data
        if real_data:
            # Generate dimension table DML with real data
            for dim_table in star_schema.dimension_tables:
                dml_statements[f"insert_{dim_table.name}"] = self._generate_dimension_real_data(
                    dim_table, real_data
                )

            # Generate fact table DML with real data
            dml_statements[f"insert_{star_schema.fact_table.name}"] = self._generate_fact_real_data(
                star_schema.fact_table, star_schema.dimension_tables, real_data
            )
        else:
            # Fallback to sample data if no real data available
            for dim_table in star_schema.dimension_tables:
                dml_statements[f"insert_{dim_table.name}"] = self._generate_dimension_sample_data(
                    dim_table, num_records, real_data
                )

            dml_statements[f"insert_{star_schema.fact_table.name}"] = self._generate_fact_sample_data(
                star_schema.fact_table, star_schema.dimension_tables, num_records, real_data
            )

        return dml_statements

    def _generate_dimension_real_data(self, dim_table: DimensionTable, real_data: Dict[str, Dict[str, List[str]]]) -> str:
        """Generate INSERT statements for dimension table using only real data"""
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"🔧 [REAL DML] Generating real data DML for {dim_table.name}")

        # Extract unique values from real data for this dimension
        real_values_for_dimension = self._extract_dimension_values_from_real_data(dim_table, real_data)

        if not real_values_for_dimension:
            logger.info(f"⚠️ [REAL DML] No real data found for {dim_table.name}, skipping")
            return f"-- No real data available for {dim_table.name}\n"

        dml = f"-- Real data for {dim_table.name}\n"

        # Get all unique combinations of values
        import itertools

        # Create combinations of all attribute values
        attribute_names = [attr for attr in dim_table.attributes if attr != dim_table.surrogate_key]
        attribute_values = []

        for attr in attribute_names:
            if attr in real_values_for_dimension:
                attribute_values.append(real_values_for_dimension[attr])
            else:
                attribute_values.append([f"Unknown_{attr}"])

        if attribute_values:
            # Generate all combinations (limited to avoid too many records)
            combinations = list(itertools.product(*attribute_values))[:20]  # Limit to 20 combinations

            for combination in combinations:
                values = []

                # Add values for each attribute (excluding surrogate key)
                for j, attr in enumerate(attribute_names):
                    if j < len(combination):
                        values.append(f"'{combination[j]}'")
                    else:
                        values.append("NULL")

                # Add audit columns
                values.extend([
                    "CURRENT_TIMESTAMP",  # created_at
                    "CURRENT_TIMESTAMP"   # updated_at
                ])

                # Build column list (excluding surrogate key)
                columns = attribute_names + ["created_at", "updated_at"]

                columns_str = ", ".join(columns)
                values_str = ", ".join(values)

                dml += f"INSERT INTO {dim_table.name} ({columns_str}) VALUES ({values_str});\n"

        logger.info(f"✅ [REAL DML] Generated {len(combinations) if 'combinations' in locals() else 0} real data records for {dim_table.name}")
        return dml

    def _generate_fact_real_data(self, fact_table: FactTable, dimension_tables: List[DimensionTable], real_data: Dict[str, Dict[str, List[str]]]) -> str:
        """Generate INSERT statements for fact table using only real data"""
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"🔧 [REAL DML] Generating real data DML for {fact_table.name}")

        dml = f"-- Real data for {fact_table.name}\n"
        dml += f"-- Note: This uses real data extracted from the source\n\n"

        # Extract real measure values from source table if available
        real_measures = {}
        if fact_table.source_table != "generated":
            source_table = fact_table.source_table.lower()
            if source_table in real_data:
                source_columns = real_data[source_table]
                for measure in fact_table.measures:
                    measure_lower = measure.lower()
                    if measure_lower in source_columns:
                        real_measures[measure] = source_columns[measure_lower]

        # If no real measures found, create a count measure
        if not real_measures:
            real_measures = {"record_count": ["1"] * 5}  # Default count measure

        # Generate records based on real data
        num_records = min(10, max(len(values) for values in real_measures.values()) if real_measures else 5)

        for i in range(num_records):
            values = []

            # Foreign keys to dimensions (using sequential IDs)
            for dim_table in dimension_tables:
                values.append(str(i + 1))

            # Measures with real values
            for measure in fact_table.measures:
                if measure in real_measures and real_measures[measure]:
                    real_value = real_measures[measure][i % len(real_measures[measure])]
                    try:
                        # Try to parse as number
                        if '.' in real_value:
                            float(real_value)
                        else:
                            int(real_value)
                        values.append(real_value)
                    except (ValueError, TypeError):
                        values.append("1")  # Default value
                else:
                    values.append("1")  # Default count

            # Add audit columns
            values.extend([
                "CURRENT_TIMESTAMP",  # created_at
                f"'{i+1:06d}'"       # etl_batch_id
            ])

            # Build column list
            columns = []
            for dim_table in dimension_tables:
                columns.append(dim_table.surrogate_key)
            columns.extend(fact_table.measures)
            columns.extend(["created_at", "etl_batch_id"])

            columns_str = ", ".join(columns)
            values_str = ", ".join(values)

            dml += f"INSERT INTO {fact_table.name} ({columns_str}) VALUES ({values_str});\n"

        logger.info(f"✅ [REAL DML] Generated {num_records} real data records for {fact_table.name}")
        return dml

    def _extract_real_data_from_sql(self, sql_content: str) -> Dict[str, Dict[str, List[str]]]:
        """Extract real data from INSERT statements in the original SQL"""
        import re
        import logging

        logger = logging.getLogger(__name__)
        real_data = {}

        logger.info(f"🔍 [REAL DATA] Starting extraction from SQL content length: {len(sql_content)}")

        # First, extract table schemas to understand column names
        table_schemas = self._extract_table_schemas(sql_content)
        logger.info(f"🔍 [REAL DATA] Found table schemas: {list(table_schemas.keys())}")

        # Pattern to match INSERT statements with column names
        insert_pattern = r'INSERT\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)'

        matches = re.finditer(insert_pattern, sql_content, re.IGNORECASE | re.MULTILINE)

        for match in matches:
            table_name = match.group(1).lower()
            columns_str = match.group(2)
            values_str = match.group(3)

            logger.info(f"🔍 [REAL DATA] Processing INSERT for table: {table_name}")
            logger.info(f"🔍 [REAL DATA] Columns: {columns_str}")
            logger.info(f"🔍 [REAL DATA] Values: {values_str[:100]}...")

            # Parse column names
            columns = [col.strip().strip('`"[]') for col in columns_str.split(',')]
            logger.info(f"🔍 [REAL DATA] Parsed columns: {columns}")

            # Parse values (improved parsing - handles quoted strings and numbers)
            values = self._parse_insert_values(values_str)
            logger.info(f"🔍 [REAL DATA] Parsed values: {values}")

            if table_name not in real_data:
                real_data[table_name] = {}
                for col in columns:
                    real_data[table_name][col] = []

            # Map values to columns
            for i, value in enumerate(values):
                if i < len(columns):
                    col_name = columns[i]
                    if value and value.strip() and value.lower() not in ['null', 'current_timestamp']:
                        clean_value = value.strip().strip("'\"")
                        real_data[table_name][col_name].append(clean_value)
                        logger.info(f"🔍 [REAL DATA] Added {col_name}: {clean_value}")

        logger.info(f"🔍 [REAL DATA] Final extracted data: {real_data}")
        return real_data

    def _extract_table_schemas(self, sql_content: str) -> Dict[str, List[str]]:
        """Extract table schemas from CREATE TABLE statements"""
        import re

        schemas = {}
        create_pattern = r'CREATE\s+TABLE\s+(\w+)\s*\(([^;]+)\)'

        matches = re.finditer(create_pattern, sql_content, re.IGNORECASE | re.MULTILINE | re.DOTALL)

        for match in matches:
            table_name = match.group(1).lower()
            columns_def = match.group(2)

            # Extract column names (simplified)
            column_pattern = r'(\w+)\s+\w+'
            column_matches = re.finditer(column_pattern, columns_def)

            columns = []
            for col_match in column_matches:
                col_name = col_match.group(1)
                if col_name.upper() not in ['FOREIGN', 'PRIMARY', 'KEY', 'CONSTRAINT']:
                    columns.append(col_name)

            schemas[table_name] = columns

        return schemas

    def _parse_insert_values(self, values_str: str) -> List[str]:
        """Parse INSERT VALUES with proper handling of quotes and commas"""
        values = []
        current_value = ""
        in_quotes = False
        quote_char = None
        paren_count = 0
        escape_next = False

        for i, char in enumerate(values_str):
            if escape_next:
                current_value += char
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                current_value += char
                continue

            if char in ["'", '"'] and not in_quotes:
                in_quotes = True
                quote_char = char
                current_value += char
            elif char == quote_char and in_quotes:
                # Check if this is an escaped quote
                if i + 1 < len(values_str) and values_str[i + 1] == quote_char:
                    current_value += char + char
                    escape_next = True  # Skip the next quote
                else:
                    in_quotes = False
                    quote_char = None
                    current_value += char
            elif char == '(' and not in_quotes:
                paren_count += 1
                current_value += char
            elif char == ')' and not in_quotes:
                paren_count -= 1
                current_value += char
            elif char == ',' and not in_quotes and paren_count == 0:
                values.append(current_value.strip())
                current_value = ""
            else:
                current_value += char

        # Add the last value
        if current_value.strip():
            values.append(current_value.strip())

        return values

    def _extract_dimension_values_from_real_data(self, dim_table: DimensionTable, real_data: Dict[str, Dict[str, List[str]]] = None) -> Dict[str, List[str]]:
        """Extract unique values for dimension attributes from real data"""
        import logging
        logger = logging.getLogger(__name__)

        if not real_data:
            return {}

        dimension_values = {}

        logger.info(f"🔍 [EXTRACT DIM] Processing dimension: {dim_table.name}")
        logger.info(f"🔍 [EXTRACT DIM] Source table: {dim_table.source_table}")
        logger.info(f"🔍 [EXTRACT DIM] Available real data tables: {list(real_data.keys())}")
        logger.info(f"🔍 [EXTRACT DIM] Dimension attributes: {dim_table.attributes}")

        # Try to find the source table for this dimension
        source_table = dim_table.source_table.lower() if dim_table.source_table != "generated" else None

        # If source table not found directly, try to find any table in real_data
        if source_table not in real_data and real_data:
            # Use the first available table as fallback
            source_table = list(real_data.keys())[0]
            logger.info(f"🔍 [EXTRACT DIM] Using fallback table: {source_table}")

        if source_table and source_table in real_data:
            source_columns = real_data[source_table]
            logger.info(f"🔍 [EXTRACT DIM] Source columns available: {list(source_columns.keys())}")

            for attr in dim_table.attributes:
                if attr == dim_table.surrogate_key:
                    continue  # Skip surrogate key

                # Try to find matching column in source data
                attr_lower = attr.lower()
                logger.info(f"🔍 [EXTRACT DIM] Looking for attribute: {attr} ({attr_lower})")

                # Look for exact match first
                if attr_lower in source_columns:
                    unique_values = list(set(source_columns[attr_lower]))[:20]
                    if unique_values:
                        dimension_values[attr] = unique_values
                        logger.info(f"✅ [EXTRACT DIM] Found exact match for {attr}: {len(unique_values)} values - {unique_values[:3]}")
                else:
                    # Look for similar column names
                    found_match = False
                    for col_name, col_values in source_columns.items():
                        if (attr_lower in col_name.lower() or
                            col_name.lower() in attr_lower or
                            self._are_similar_names(attr_lower, col_name.lower())):
                            unique_values = list(set(col_values))[:20]
                            if unique_values:
                                dimension_values[attr] = unique_values
                                logger.info(f"✅ [EXTRACT DIM] Found similar match for {attr} -> {col_name}: {len(unique_values)} values - {unique_values[:3]}")
                                found_match = True
                                break

                    if not found_match:
                        logger.info(f"❌ [EXTRACT DIM] No match found for attribute: {attr}")

        logger.info(f"🔍 [EXTRACT DIM] Final dimension values: {dimension_values}")
        return dimension_values

    def _are_similar_names(self, name1: str, name2: str) -> bool:
        """Check if two column names are similar"""
        # Simple similarity check - can be improved
        name1_parts = name1.replace('_', ' ').split()
        name2_parts = name2.replace('_', ' ').split()

        for part1 in name1_parts:
            for part2 in name2_parts:
                if part1 in part2 or part2 in part1:
                    return True
        return False

    def _generate_dimension_sample_data(self, dim_table: DimensionTable, num_records: int, real_data: Dict[str, Dict[str, List[str]]] = None) -> str:
        """Generate sample INSERT statements for dimension table"""
        import random
        import logging
        from datetime import datetime, timedelta

        type_map = self.type_mappings

        # Extract unique values from real data for this dimension
        real_values_for_dimension = self._extract_dimension_values_from_real_data(
            dim_table, real_data
        )

        # Sample data generators based on attribute names
        def generate_sample_value(attr_name: str) -> str:
            attr_lower = attr_name.lower()

            # First try to use real data if available
            if real_values_for_dimension and attr_name in real_values_for_dimension:
                available_values = real_values_for_dimension[attr_name]
                if available_values:
                    return f"'{random.choice(available_values)}'"

            # If no real data found, generate synthetic data based on attribute name patterns
            if any(keyword in attr_lower for keyword in ['name', 'nome']):
                names = ['João Silva', 'Maria Santos', 'Pedro Oliveira', 'Ana Costa', 'Carlos Souza']
                return f"'{random.choice(names)}'"
            elif any(keyword in attr_lower for keyword in ['email']):
                domains = ['gmail.com', 'hotmail.com', 'yahoo.com.br', 'bol.com.br']
                return f"'usuario{random.randint(1, 999)}@{random.choice(domains)}'"
            elif any(keyword in attr_lower for keyword in ['telefone', 'phone']):
                return f"'({random.randint(11, 85):02d}) {random.randint(1000, 9999)}-{random.randint(1000, 9999)}'"
            elif any(keyword in attr_lower for keyword in ['cpf']):
                return f"'{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}'"
            elif any(keyword in attr_lower for keyword in ['tipo', 'type', 'categoria', 'category']):
                types = ['Tipo A', 'Tipo B', 'Tipo C', 'Categoria 1', 'Categoria 2']
                return f"'{random.choice(types)}'"
            elif any(keyword in attr_lower for keyword in ['bloco', 'block']):
                return f"'{random.choice(['A', 'B', 'C', 'D'])}'"
            elif any(keyword in attr_lower for keyword in ['apartamento', 'apt', 'numero', 'number']):
                return f"'{random.randint(1, 250)}'"
            elif any(keyword in attr_lower for keyword in ['placa', 'plate']):
                letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                return f"'{random.choice(letters)}{random.choice(letters)}{random.choice(letters)}-{random.randint(1000, 9999)}'"
            elif any(keyword in attr_lower for keyword in ['motivo', 'reason']):
                reasons = ['Trabalho', 'Visita', 'Entrega', 'Manutenção', 'Reunião']
                return f"'{random.choice(reasons)}'"
            elif any(keyword in attr_lower for keyword in ['observacao', 'observation', 'comment']):
                return f"'Observação {random.randint(1, 100)}'"
            else:
                # Generic fallback
                return f"'{attr_name}_{random.randint(1, 100)}'"
                
        dml = f"-- Sample data for {dim_table.name}\n"

        for i in range(1, num_records + 1):
            values = []

            # Skip surrogate key (auto-increment)
            for attr in dim_table.attributes:
                if attr != dim_table.surrogate_key:
                    if attr == dim_table.natural_key:
                        # Generate unique natural key
                        values.append(f"'{dim_table.name}_{i:03d}'")
                    else:
                        values.append(generate_sample_value(attr))

            # Add SCD columns for Type 2
            if dim_table.scd_type == 2:
                values.extend([
                    "CURRENT_DATE",  # effective_date
                    "NULL",          # expiry_date
                    "TRUE",          # is_current
                ])

            # Add audit columns
            values.extend([
                "CURRENT_TIMESTAMP",  # created_at
                "CURRENT_TIMESTAMP"   # updated_at
            ])

            # Build column list (excluding surrogate key)
            columns = [attr for attr in dim_table.attributes if attr != dim_table.surrogate_key]
            if dim_table.scd_type == 2:
                columns.extend(["effective_date", "expiry_date", "is_current"])
            columns.extend(["created_at", "updated_at"])

            columns_str = ", ".join(columns)
            values_str = ", ".join(values)

            dml += f"INSERT INTO {dim_table.name} ({columns_str}) VALUES ({values_str});\n"

        return dml

    def _generate_fact_sample_data(self, fact_table: FactTable, dimension_tables: List[DimensionTable], num_records: int, real_data: Dict[str, Dict[str, List[str]]] = None) -> str:
        """Generate sample INSERT statements for fact table"""
        import random
        from datetime import datetime, timedelta

        dml = f"-- Sample data for {fact_table.name}\n"
        dml += f"-- Note: This assumes dimension tables have been populated with sample data\n\n"

        # Extract real measure values from source table if available
        real_measures = {}
        if real_data and fact_table.source_table != "generated":
            source_table = fact_table.source_table.lower()
            if source_table in real_data:
                source_columns = real_data[source_table]
                for measure in fact_table.measures:
                    measure_lower = measure.lower()
                    # Try to find matching column in source data
                    if measure_lower in source_columns:
                        real_measures[measure] = source_columns[measure_lower]
                    else:
                        # Look for similar column names
                        for col_name, col_values in source_columns.items():
                            if (measure_lower in col_name.lower() or
                                col_name.lower() in measure_lower or
                                self._are_similar_names(measure_lower, col_name.lower())):
                                real_measures[measure] = col_values
                                break

        for i in range(1, num_records + 1):
            values = []

            # Foreign keys to dimensions (using surrogate keys 1 to num_records)
            for dim_table in dimension_tables:
                # Random reference to existing dimension record
                surrogate_key_value = random.randint(1, min(num_records, 10))
                values.append(str(surrogate_key_value))

            # Measures with real or realistic sample values
            for measure in fact_table.measures:
                measure_lower = measure.lower()

                # Try to use real data first
                if measure in real_measures and real_measures[measure]:
                    real_value = random.choice(real_measures[measure])
                    # Clean and validate the value
                    try:
                        if '.' in real_value or any(keyword in measure_lower for keyword in ['amount', 'price', 'valor', 'preco']):
                            value = float(real_value)
                        else:
                            value = int(real_value)
                        values.append(str(value))
                    except (ValueError, TypeError):
                        # Fallback to synthetic data if real value is invalid
                        values.append(str(self._generate_synthetic_measure_value(measure_lower)))
                else:
                    # Fallback to synthetic data
                    values.append(str(self._generate_synthetic_measure_value(measure_lower)))

            # Add audit columns
            values.extend([
                "CURRENT_TIMESTAMP",  # created_at
                f"'{i:06d}'"         # etl_batch_id
            ])

            # Build column list
            columns = []
            for dim_table in dimension_tables:
                columns.append(dim_table.surrogate_key)
            columns.extend(fact_table.measures)
            columns.extend(["created_at", "etl_batch_id"])

            columns_str = ", ".join(columns)
            values_str = ", ".join(values)

            dml += f"INSERT INTO {fact_table.name} ({columns_str}) VALUES ({values_str});\n"

        return dml

    def _generate_synthetic_measure_value(self, measure_lower: str) -> float:
        """Generate synthetic values for measures based on name patterns"""
        import random

        if any(keyword in measure_lower for keyword in ['amount', 'valor', 'price', 'preco']):
            # Monetary values
            return round(random.uniform(10.0, 10000.0), 2)
        elif any(keyword in measure_lower for keyword in ['quantity', 'qty', 'quantidade']):
            # Quantity values
            return random.randint(1, 100)
        elif any(keyword in measure_lower for keyword in ['count', 'total', 'sum']):
            # Count/total values
            return random.randint(1, 1000)
        elif any(keyword in measure_lower for keyword in ['rate', 'percent', 'taxa']):
            # Percentage values
            return round(random.uniform(0.0, 100.0), 2)
        elif any(keyword in measure_lower for keyword in ['weight', 'peso', 'size', 'tamanho']):
            # Weight/size values
            return round(random.uniform(0.1, 1000.0), 2)
        else:
            # Default numeric value
            return round(random.uniform(1.0, 1000.0), 2)

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
