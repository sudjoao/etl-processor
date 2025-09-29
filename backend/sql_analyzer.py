"""
SQL Analyzer Module for Data Warehouse Modeling
Analyzes SQL DDL and DML to extract table structures and identify dimensional patterns
"""

import re
import sqlparse
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ColumnType(Enum):
    """Column type classification for dimensional modeling"""
    NUMERIC = "numeric"
    TEXT = "text"
    DATE = "date"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


class DimensionalRole(Enum):
    """Potential dimensional role of a column"""
    FACT_MEASURE = "fact_measure"
    DIMENSION_KEY = "dimension_key"
    DIMENSION_ATTRIBUTE = "dimension_attribute"
    TIME_DIMENSION = "time_dimension"
    SURROGATE_KEY = "surrogate_key"
    UNKNOWN = "unknown"


@dataclass
class ColumnInfo:
    """Information about a database column"""
    name: str
    data_type: str
    column_type: ColumnType
    is_nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    dimensional_role: DimensionalRole = DimensionalRole.UNKNOWN
    cardinality_estimate: Optional[str] = None  # LOW, MEDIUM, HIGH
    sample_values: List[str] = None


@dataclass
class TableInfo:
    """Information about a database table"""
    name: str
    columns: List[ColumnInfo]
    primary_keys: List[str]
    foreign_keys: Dict[str, str]  # column_name -> referenced_table.column
    table_type: str = "BASE_TABLE"  # BASE_TABLE, FACT, DIMENSION
    estimated_rows: Optional[int] = None


class SQLAnalyzer:
    """Analyzes SQL statements to extract table structures and patterns"""
    
    def __init__(self):
        self.tables: Dict[str, TableInfo] = {}
        self.sql_statements: List[str] = []
        
        # Patterns for identifying column characteristics
        self.numeric_patterns = [
            r'(decimal|numeric|int|float|double|real|money)',
            r'(quantidade|valor|preco|total|soma|count)',
            r'(amount|price|cost|total|sum|qty|quantity)'
        ]
        
        self.date_patterns = [
            r'(date|time|timestamp|datetime)',
            r'(data|hora|tempo)',
            r'(created|updated|modified).*at'
        ]
        
        self.dimension_patterns = [
            r'.*(name|nome|description|descricao|type|tipo|category|categoria)',
            r'.*(status|estado|situacao|codigo|code)',
            r'.*(cidade|city|estado|state|pais|country)',
            r'.*(cpf|email|telefone|phone|pessoa|person)',
            r'.*(bloco|block|apartamento|apartment|local|location)',
            r'.*(veiculo|vehicle|placa|plate|carro|car)',
            r'.*(motivo|reason|observacao|observation|comment)',
            r'.*(visita|visit|tipo_visita|visit_type)'
        ]

        self.fact_patterns = [
            r'.*(valor|value|amount|total|sum|count|qty|quantity)',
            r'.*(preco|price|cost|custo|receita|revenue)',
            r'.*(vendas|sales|compras|purchases)',
            r'.*(entrada|saida|visit|access|evento|event)'
        ]

    def parse_sql(self, sql_content: str) -> Dict[str, Any]:
        """Parse SQL content and extract table information"""
        try:
            # Split SQL into individual statements
            statements = sqlparse.split(sql_content)

            analysis_result = {
                "tables": [],
                "relationships": [],
                "dimensional_analysis": {},
                "recommendations": []
            }

            for statement in statements:
                if statement.strip():
                    self.sql_statements.append(statement)
                    parsed = sqlparse.parse(statement)[0]

                    if self._is_create_table(parsed):
                        table_info = self._analyze_create_table(parsed)
                        if table_info:
                            self.tables[table_info.name] = table_info
                            analysis_result["tables"].append(self._table_to_dict(table_info))

                    elif self._is_insert_statement(parsed):
                        self._analyze_insert_statement(parsed)
            
            # Perform dimensional analysis
            analysis_result["dimensional_analysis"] = self._perform_dimensional_analysis()
            analysis_result["recommendations"] = self._generate_recommendations()
            
            return analysis_result
            
        except Exception as e:
            return {
                "error": f"Error parsing SQL: {str(e)}",
                "tables": [],
                "relationships": [],
                "dimensional_analysis": {},
                "recommendations": []
            }

    def _is_create_table(self, parsed_statement) -> bool:
        """Check if statement is CREATE TABLE"""
        # Filter out whitespace and comments
        tokens = [token for token in parsed_statement.flatten()
                 if not token.is_whitespace and not token.ttype in sqlparse.tokens.Comment]

        return (len(tokens) >= 2 and
                tokens[0].ttype is sqlparse.tokens.Keyword.DDL and
                tokens[0].value.upper() == 'CREATE' and
                tokens[1].value.upper() == 'TABLE')

    def _is_insert_statement(self, parsed_statement) -> bool:
        """Check if statement is INSERT"""
        tokens = [token for token in parsed_statement.flatten() if not token.is_whitespace]
        return (len(tokens) >= 1 and 
                tokens[0].ttype is sqlparse.tokens.Keyword.DML and
                tokens[0].value.upper() == 'INSERT')

    def _analyze_create_table(self, parsed_statement) -> Optional[TableInfo]:
        """Analyze CREATE TABLE statement"""
        try:
            statement_str = str(parsed_statement)
            
            # Extract table name
            table_name_match = re.search(r'CREATE\s+TABLE\s+[`"]?(\w+)[`"]?\s*\(', statement_str, re.IGNORECASE)
            if not table_name_match:
                return None
            
            table_name = table_name_match.group(1)
            
            # Extract column definitions
            columns = []
            primary_keys = []
            foreign_keys = {}
            
            # Find column definitions between parentheses
            columns_section = re.search(r'\((.*)\)', statement_str, re.DOTALL)
            if columns_section:
                columns_text = columns_section.group(1)
                column_lines = [line.strip() for line in columns_text.split(',')]
                
                for line in column_lines:
                    if line.strip():
                        column_info = self._parse_column_definition(line)
                        if column_info:
                            columns.append(column_info)
                            if column_info.is_primary_key:
                                primary_keys.append(column_info.name)
            
            return TableInfo(
                name=table_name,
                columns=columns,
                primary_keys=primary_keys,
                foreign_keys=foreign_keys
            )
            
        except Exception as e:
            print(f"Error analyzing CREATE TABLE: {e}")
            return None

    def _parse_column_definition(self, column_def: str) -> Optional[ColumnInfo]:
        """Parse individual column definition"""
        try:
            # Clean up the definition
            column_def = column_def.strip().rstrip(',')
            
            # Skip constraint definitions
            if any(keyword in column_def.upper() for keyword in ['PRIMARY KEY', 'FOREIGN KEY', 'CONSTRAINT', 'INDEX']):
                return None
            
            # Extract column name and type
            parts = column_def.split()
            if len(parts) < 2:
                return None
            
            column_name = parts[0].strip('`"')
            data_type = parts[1].upper()
            
            # Determine column type
            column_type = self._classify_column_type(column_name, data_type)
            
            # Check for constraints
            is_nullable = 'NOT NULL' not in column_def.upper()
            is_primary_key = 'PRIMARY KEY' in column_def.upper()
            
            # Determine dimensional role
            dimensional_role = self._determine_dimensional_role(column_name, data_type, column_type)
            
            # Estimate cardinality
            cardinality = self._estimate_cardinality(column_name, data_type, column_type)
            
            return ColumnInfo(
                name=column_name,
                data_type=data_type,
                column_type=column_type,
                is_nullable=is_nullable,
                is_primary_key=is_primary_key,
                dimensional_role=dimensional_role,
                cardinality_estimate=cardinality,
                sample_values=[]
            )
            
        except Exception as e:
            print(f"Error parsing column definition '{column_def}': {e}")
            return None

    def _classify_column_type(self, column_name: str, data_type: str) -> ColumnType:
        """Classify column type based on name and SQL type"""
        data_type_lower = data_type.lower()
        column_name_lower = column_name.lower()
        
        # Check for numeric types
        if any(pattern in data_type_lower for pattern in ['int', 'decimal', 'numeric', 'float', 'double', 'real', 'money']):
            return ColumnType.NUMERIC
        
        # Check for date/time types
        if any(pattern in data_type_lower for pattern in ['date', 'time', 'timestamp', 'datetime']):
            return ColumnType.DATE
        
        # Check for boolean types
        if any(pattern in data_type_lower for pattern in ['bool', 'bit']):
            return ColumnType.BOOLEAN
        
        # Check column name patterns
        if any(re.search(pattern, column_name_lower) for pattern in self.date_patterns):
            return ColumnType.DATE
        
        # Default to text
        return ColumnType.TEXT

    def _determine_dimensional_role(self, column_name: str, data_type: str, column_type: ColumnType) -> DimensionalRole:
        """Determine the likely dimensional role of a column"""
        column_name_lower = column_name.lower()

        # Check for time dimensions
        if column_type == ColumnType.DATE or any(re.search(pattern, column_name_lower) for pattern in self.date_patterns):
            return DimensionalRole.TIME_DIMENSION

        # Enhanced fact measure detection - include text fields that represent events/facts
        if column_type == ColumnType.NUMERIC:
            if any(re.search(pattern, column_name_lower) for pattern in self.fact_patterns):
                return DimensionalRole.FACT_MEASURE
            elif 'id' in column_name_lower or 'key' in column_name_lower:
                return DimensionalRole.DIMENSION_KEY
        elif any(re.search(pattern, column_name_lower) for pattern in self.fact_patterns):
            # Text fields that represent factual events (like visit entries)
            return DimensionalRole.FACT_MEASURE

        # Check for dimension attributes
        if any(re.search(pattern, column_name_lower) for pattern in self.dimension_patterns):
            return DimensionalRole.DIMENSION_ATTRIBUTE

        # Check for keys
        if 'id' in column_name_lower or 'key' in column_name_lower:
            return DimensionalRole.DIMENSION_KEY

        # Default to dimension attribute for most text fields
        if column_type == ColumnType.TEXT:
            return DimensionalRole.DIMENSION_ATTRIBUTE

        return DimensionalRole.UNKNOWN

    def _estimate_cardinality(self, column_name: str, data_type: str, column_type: ColumnType) -> str:
        """Estimate the cardinality of a column"""
        column_name_lower = column_name.lower()
        
        # High cardinality indicators
        if any(indicator in column_name_lower for indicator in ['id', 'key', 'codigo', 'number']):
            return "HIGH"
        
        # Low cardinality indicators
        if any(indicator in column_name_lower for indicator in ['type', 'status', 'category', 'gender', 'boolean']):
            return "LOW"
        
        # Medium cardinality for names and descriptions
        if any(indicator in column_name_lower for indicator in ['name', 'description', 'title']):
            return "MEDIUM"
        
        # Based on data type
        if column_type == ColumnType.BOOLEAN:
            return "LOW"
        elif column_type == ColumnType.DATE:
            return "MEDIUM"
        elif column_type == ColumnType.NUMERIC:
            return "HIGH"
        
        return "MEDIUM"

    def _analyze_insert_statement(self, parsed_statement):
        """Analyze INSERT statement to gather data patterns"""
        # This could be enhanced to extract sample values
        # For now, we'll skip detailed INSERT analysis
        pass

    def _perform_dimensional_analysis(self) -> Dict[str, Any]:
        """Perform dimensional modeling analysis on all tables"""
        analysis = {
            "fact_candidates": [],
            "dimension_candidates": [],
            "time_dimensions": [],
            "measures": [],
            "attributes": []
        }
        
        for table_name, table_info in self.tables.items():
            table_analysis = self._analyze_table_for_dimensions(table_info)
            
            if table_analysis["is_fact_candidate"]:
                analysis["fact_candidates"].append({
                    "table_name": table_name,
                    "measures": table_analysis["measures"],
                    "dimension_keys": table_analysis["dimension_keys"]
                })
            
            if table_analysis["is_dimension_candidate"]:
                analysis["dimension_candidates"].append({
                    "table_name": table_name,
                    "attributes": table_analysis["attributes"],
                    "key_column": table_analysis["key_column"]
                })
        
        return analysis

    def _analyze_table_for_dimensions(self, table_info: TableInfo) -> Dict[str, Any]:
        """Analyze a single table for dimensional characteristics"""
        measures = []
        dimension_keys = []
        attributes = []
        time_columns = []
        
        for column in table_info.columns:
            if column.dimensional_role == DimensionalRole.FACT_MEASURE:
                measures.append(column.name)
            elif column.dimensional_role == DimensionalRole.DIMENSION_KEY:
                dimension_keys.append(column.name)
            elif column.dimensional_role == DimensionalRole.DIMENSION_ATTRIBUTE:
                attributes.append(column.name)
            elif column.dimensional_role == DimensionalRole.TIME_DIMENSION:
                time_columns.append(column.name)
        
        # Determine if table is fact or dimension candidate
        is_fact_candidate = len(measures) > 0 and len(dimension_keys) > 0
        is_dimension_candidate = len(attributes) > 0 and len(measures) == 0
        
        return {
            "is_fact_candidate": is_fact_candidate,
            "is_dimension_candidate": is_dimension_candidate,
            "measures": measures,
            "dimension_keys": dimension_keys,
            "attributes": attributes,
            "time_columns": time_columns,
            "key_column": table_info.primary_keys[0] if table_info.primary_keys else None
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations for dimensional modeling"""
        recommendations = []
        
        # Analyze overall structure
        total_tables = len(self.tables)
        fact_candidates = len([t for t in self.tables.values() 
                              if self._analyze_table_for_dimensions(t)["is_fact_candidate"]])
        
        if total_tables == 1:
            recommendations.append("Consider denormalizing this single table into fact and dimension tables")
        
        if fact_candidates == 0:
            recommendations.append("No clear fact table candidates found. Consider adding measurable numeric columns")
        
        if fact_candidates > 1:
            recommendations.append("Multiple fact table candidates found. Consider creating a unified fact table or separate fact tables for different business processes")
        
        return recommendations

    def _table_to_dict(self, table_info: TableInfo) -> Dict[str, Any]:
        """Convert TableInfo to dictionary for JSON serialization"""
        return {
            "name": table_info.name,
            "columns": [
                {
                    "name": col.name,
                    "data_type": col.data_type,
                    "column_type": col.column_type.value,
                    "dimensional_role": col.dimensional_role.value,
                    "cardinality_estimate": col.cardinality_estimate,
                    "is_nullable": col.is_nullable,
                    "is_primary_key": col.is_primary_key
                }
                for col in table_info.columns
            ],
            "primary_keys": table_info.primary_keys,
            "foreign_keys": table_info.foreign_keys,
            "table_type": table_info.table_type
        }
