from flask import Flask, request, jsonify
from flask_cors import CORS
import csv
import io
import re
import logging
from typing import List, Dict, Any
from datetime import datetime
from sql_analyzer import SQLAnalyzer
from dimensional_modeling import DimensionalModelingEngine
from star_schema_generator import StarSchemaGenerator
from ai_dimension_classifier import AIDimensionClassifier

app = Flask(__name__)

# Configure CORS with specific settings
CORS(app, 
     origins=["http://localhost:3000", "http://frontend:3000"],
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request logging middleware
@app.before_request
def log_request_info():
    logger.info(f"{request.method} {request.url} - {request.remote_addr}")

@app.after_request
def log_response_info(response):
    logger.info(f"Response: {response.status_code}")
    return response

@app.after_request
def after_request(response):
    # Additional CORS headers for preflight requests
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

class CSVToSQLTransformer:
    def __init__(self):
        # PostgreSQL-only transformer
        pass
    
    def sanitize_identifier(self, name: str) -> str:
        """Sanitize SQL identifier names"""
        return re.sub(r'[^a-zA-Z0-9_]', '_', name).lower()
    
    def get_sql_type(self, field_format: str) -> str:
        """Get PostgreSQL SQL type based on field format"""
        type_mapping = {
            "number": "NUMERIC(10,2)",
            "currency": "NUMERIC(10,2)",
            "date": "DATE",
            "text": "VARCHAR(255)"
        }

        return type_mapping.get(field_format, "VARCHAR(255)")
    
    def escape_value(self, value: str, field_format: str) -> str:
        """Escape SQL values based on field format"""
        if value == "" or value is None:
            return "NULL"
        
        if field_format in ["number", "currency"]:
            try:
                # Try to parse as float directly first
                num = float(str(value))
                return str(num)
            except ValueError:
                # If that fails, try to clean the string
                cleaned = re.sub(r'[^\d.-]', '', str(value))
                try:
                    num = float(cleaned)
                    return str(num)
                except ValueError:
                    return "NULL"
        
        # Escape single quotes for string values
        escaped_value = str(value).replace("'", "''")
        return f"'{escaped_value}'"
    
    def format_cell_value(self, value: str, field_format: str) -> str:
        """Format cell value based on field format"""
        if not value or value.strip() == "":
            return ""
        
        if field_format == "number":
            try:
                num = float(value)
                return f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except ValueError:
                return value
        
        elif field_format == "currency":
            try:
                num = float(value)
                return f"R$ {num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except ValueError:
                return value
        
        elif field_format == "date":
            # Convert YYYY-MM-DD to DD/MM/YYYY
            if re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                year, month, day = value.split("-")
                return f"{day}/{month}/{year}"
            return value
        
        return value
    
    def parse_csv_content(self, csv_content: str, delimiter: str) -> Dict[str, Any]:
        """Parse CSV content and return headers and rows"""
        try:
            # Use StringIO to treat string as file
            csv_file = io.StringIO(csv_content)
            reader = csv.reader(csv_file, delimiter=delimiter)
            
            rows = list(reader)
            if not rows:
                raise ValueError("CSV file is empty")
            
            headers = [header.strip().replace('"', '') for header in rows[0]]
            data_rows = []
            
            for row in rows[1:]:
                # Ensure row has same number of columns as headers
                padded_row = row + [''] * (len(headers) - len(row))
                cleaned_row = [cell.strip().replace('"', '') for cell in padded_row[:len(headers)]]
                data_rows.append(cleaned_row)
            
            return {
                "headers": headers,
                "rows": data_rows
            }
        except Exception as e:
            raise ValueError(f"Error parsing CSV: {str(e)}")
    
    def generate_sql(self, csv_data: Dict[str, Any], fields: List[Dict[str, Any]],
                    table_name: str, include_create_table: bool = True) -> str:
        """Generate PostgreSQL SQL from CSV data and field configuration"""
        
        # Filter and sort selected fields
        selected_fields = [field for field in fields if field.get("selected", False)]
        selected_fields.sort(key=lambda x: x.get("order", 0))
        
        if not selected_fields:
            raise ValueError("No fields selected")
        
        # Get column indices for selected fields
        headers = csv_data["headers"]
        column_indices = []
        for field in selected_fields:
            try:
                index = headers.index(field["name"])
                column_indices.append(index)
            except ValueError:
                raise ValueError(f"Field '{field['name']}' not found in CSV headers")
        
        # Format data
        formatted_rows = []
        for row in csv_data["rows"]:
            formatted_row = []
            for i, col_index in enumerate(column_indices):
                cell_value = row[col_index] if col_index < len(row) else ""
                field = selected_fields[i]
                formatted_value = self.format_cell_value(cell_value, field.get("format", "text"))
                formatted_row.append(formatted_value)
            formatted_rows.append(formatted_row)
        
        # Generate SQL
        sql = ""
        sanitized_table_name = self.sanitize_identifier(table_name)
        
        # CREATE TABLE statement
        if include_create_table:
            sql += f"-- Criação da tabela (PostgreSQL)\n"
            sql += f"CREATE TABLE {self._quote_identifier(sanitized_table_name)} (\n"

            columns = []
            for i, field in enumerate(selected_fields):
                column_name = self.sanitize_identifier(field["name"])
                sql_type = self.get_sql_type(field.get("format", "text"))
                quoted_column = self._quote_identifier(column_name)
                columns.append(f"  {quoted_column} {sql_type}")

            sql += ",\n".join(columns) + "\n"
            sql += ");\n\n"
        
        # INSERT statements
        sql += f"-- Inserção dos dados\n"
        
        column_names = []
        for field in selected_fields:
            column_name = self.sanitize_identifier(field["name"])
            quoted_column = self._quote_identifier(column_name)
            column_names.append(quoted_column)

        columns_str = ", ".join(column_names)
        quoted_table = self._quote_identifier(sanitized_table_name)
        
        # Use original data for SQL generation, not formatted data
        for row in csv_data["rows"]:
            values = []
            for i, col_index in enumerate(column_indices):
                cell_value = row[col_index] if col_index < len(row) else ""
                field = selected_fields[i]
                escaped_value = self.escape_value(cell_value, field.get("format", "text"))
                values.append(escaped_value)
            
            values_str = ", ".join(values)
            sql += f"INSERT INTO {quoted_table} ({columns_str}) VALUES ({values_str});\n"
        
        return sql
    
    def _quote_identifier(self, identifier: str) -> str:
        """Quote identifier for PostgreSQL"""
        return f'"{identifier}"'

# Initialize transformer
transformer = CSVToSQLTransformer()

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    """Health check endpoint"""
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({"status": "healthy", "service": "csv-to-sql-api"})

@app.route('/api/transform', methods=['POST', 'OPTIONS'])
def transform_csv_to_sql():
    """Transform CSV to SQL endpoint"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required fields
        required_fields = ["csvContent", "fields", "tableName", "delimiter"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        csv_content = data["csvContent"]
        fields = data["fields"]
        table_name = data["tableName"]
        delimiter = data["delimiter"]
        include_create_table = data.get("includeCreateTable", True)
        
        # Validate delimiter
        if delimiter not in [",", ";", "\t", "|"]:
            return jsonify({"error": "Invalid delimiter"}), 400
        
        # Parse CSV
        csv_data = transformer.parse_csv_content(csv_content, delimiter)
        
        # Generate SQL (PostgreSQL only)
        sql_result = transformer.generate_sql(
            csv_data=csv_data,
            fields=fields,
            table_name=table_name,
            include_create_table=include_create_table
        )
        
        return jsonify({
            "success": True,
            "sql": sql_result,
            "rowsProcessed": len(csv_data["rows"]),
            "fieldsSelected": len([f for f in fields if f.get("selected", False)])
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# Data Warehouse Modeling Endpoints

@app.route('/api/analyze-sql', methods=['POST', 'OPTIONS'])
def analyze_sql():
    """Analyze SQL structure for dimensional modeling"""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.get_json()

        if not data or 'sql' not in data:
            return jsonify({'error': 'SQL content is required'}), 400

        sql_content = data['sql']

        # Initialize SQL analyzer
        analyzer = SQLAnalyzer()

        # Analyze SQL structure
        analysis_result = analyzer.parse_sql(sql_content)

        return jsonify({
            'success': True,
            'analysis': analysis_result
        })

    except Exception as e:
        app.logger.error(f"Error analyzing SQL: {str(e)}")
        return jsonify({'error': f'Error analyzing SQL: {str(e)}'}), 500


@app.route('/api/generate-dw-model', methods=['POST', 'OPTIONS'])
def generate_dw_model():
    """Generate dimensional model (star schema) from SQL"""
    if request.method == 'OPTIONS':
        return '', 200

    app.logger.info("🚀 [DW MODEL] Starting DW model generation...")
    try:
        data = request.get_json()
        app.logger.info(f"🚀 [DW MODEL] Received request data keys: {list(data.keys()) if data else 'None'}")

        if not data or 'sql' not in data:
            app.logger.error("❌ [DW MODEL] SQL content is required but not provided")
            return jsonify({'error': 'SQL content is required'}), 400

        sql_content = data['sql']
        model_name = data.get('model_name', 'DataWarehouse')
        include_indexes = data.get('include_indexes', True)
        include_partitioning = data.get('include_partitioning', False)

        app.logger.info(f"🚀 [DW MODEL] Parameters - Model: {model_name}, Dialect: PostgreSQL")
        app.logger.info(f"🚀 [DW MODEL] SQL content length: {len(sql_content)} characters")

        # Initialize dimensional modeling engine
        app.logger.info("🚀 [DW MODEL] Initializing dimensional modeling engine...")
        modeling_engine = DimensionalModelingEngine()

        # Create dimensional model
        app.logger.info("🚀 [DW MODEL] Creating dimensional model...")
        model_result = modeling_engine.create_dimensional_model(sql_content, model_name)
        app.logger.info(f"🚀 [DW MODEL] Model creation result keys: {list(model_result.keys())}")

        if 'error' in model_result:
            return jsonify(model_result), 400

        # Generate optimized DDL
        schema_generator = StarSchemaGenerator()
        star_schema = modeling_engine.star_schemas[0] if modeling_engine.star_schemas else None

        app.logger.info(f"🚀 [DW MODEL] Star schemas available: {len(modeling_engine.star_schemas)}")
        app.logger.info(f"🚀 [DW MODEL] Star schema object: {star_schema is not None}")

        if star_schema:
            app.logger.info("🚀 [DW MODEL] Generating complete schema with DML...")
            complete_schema = schema_generator.generate_complete_schema(
                star_schema,
                include_indexes=include_indexes,
                include_partitioning=include_partitioning,
                include_sample_data=False,
                sample_records=10,
                original_sql=sql_content
            )
            app.logger.info(f"🚀 [DW MODEL] Complete schema keys: {list(complete_schema.keys())}")
            model_result['complete_schema'] = complete_schema

            # Override DDL statements with the ones from StarSchemaGenerator (more complete)
            if 'ddl_statements' in complete_schema:
                model_result['ddl_statements'] = complete_schema['ddl_statements']
                app.logger.info(f"🚀 [DW MODEL] Updated DDL statements count: {len(complete_schema['ddl_statements'])}")

            # Generate ETL templates
            etl_templates = schema_generator.generate_etl_templates(star_schema)
            model_result['etl_templates'] = etl_templates

            # Extract DML statements for easier access
            if 'dml_statements' in complete_schema:
                dml_statements = complete_schema['dml_statements']
                if isinstance(dml_statements, dict):
                    app.logger.info(f"🚀 [DW MODEL] DML statements found: {list(dml_statements.keys())}")
                    model_result['dml_statements'] = dml_statements
                else:
                    app.logger.info(f"🚀 [DW MODEL] DML statements type: {type(dml_statements)}, content: {dml_statements}")
                    model_result['dml_statements'] = {}
            else:
                app.logger.warning("🚀 [DW MODEL] No DML statements found in complete_schema")

        return jsonify(model_result)

    except Exception as e:
        app.logger.error(f"Error generating DW model: {str(e)}")
        return jsonify({'error': f'Error generating DW model: {str(e)}'}), 500


@app.route('/api/dw-recommendations', methods=['POST', 'OPTIONS'])
def get_dw_recommendations():
    """Get recommendations for dimensional modeling optimization"""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.get_json()

        if not data or 'star_schema' not in data:
            return jsonify({'error': 'Star schema data is required'}), 400

        star_schema_data = data['star_schema']

        # Generate advanced recommendations
        recommendations = {
            'performance': [
                'Consider partitioning fact table by date for better query performance',
                'Add bitmap indexes on low-cardinality dimension attributes',
                'Implement aggregate tables for frequently queried metrics'
            ],
            'data_quality': [
                'Implement data validation rules for dimension attributes',
                'Add referential integrity constraints between fact and dimension tables',
                'Consider implementing slowly changing dimensions (SCD) for historical tracking'
            ],
            'maintenance': [
                'Schedule regular statistics updates for query optimization',
                'Implement incremental ETL processes for large fact tables',
                'Monitor and archive old partitions to manage storage'
            ],
            'analytics': [
                'Create materialized views for common analytical queries',
                'Consider implementing OLAP cubes for multidimensional analysis',
                'Add calculated measures for business KPIs'
            ]
        }

        # Analyze schema complexity
        fact_table = star_schema_data.get('fact_table', {})
        dimension_tables = star_schema_data.get('dimension_tables', [])

        complexity_score = len(dimension_tables) * 10 + len(fact_table.get('measures', [])) * 5

        if complexity_score > 100:
            recommendations['scalability'] = [
                'Consider implementing data mart architecture for better performance',
                'Evaluate columnar storage for analytical workloads',
                'Implement data compression strategies'
            ]

        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'complexity_score': complexity_score,
            'complexity_level': 'high' if complexity_score > 100 else 'medium' if complexity_score > 50 else 'low'
        })

    except Exception as e:
        app.logger.error(f"Error generating recommendations: {str(e)}")
        return jsonify({'error': f'Error generating recommendations: {str(e)}'}), 500


@app.route('/api/dw-metadata', methods=['GET', 'OPTIONS'])
def get_dw_metadata():
    """Get metadata about dimensional modeling capabilities"""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        metadata = {
            'supported_dialects': ['postgresql'],  # PostgreSQL only
            'modeling_features': {
                'star_schema': True,
                'snowflake_schema': False,  # Future enhancement
                'slowly_changing_dimensions': True,
                'fact_table_types': ['transaction', 'snapshot', 'accumulating'],
                'dimension_types': ['conformed', 'degenerate', 'junk', 'role_playing']
            },
            'optimization_features': {
                'partitioning': True,
                'indexing': True,
                'compression': False,  # Future enhancement
                'materialized_views': True,
                'aggregate_tables': False  # Future enhancement
            },
            'etl_features': {
                'scd_type_1': True,
                'scd_type_2': True,
                'scd_type_3': False,  # Future enhancement
                'incremental_loading': True,
                'data_validation': True
            },
            'analytics_features': {
                'olap_cubes': False,  # Future enhancement
                'calculated_measures': False,  # Future enhancement
                'drill_down_drill_up': False,  # Future enhancement
                'time_intelligence': True
            }
        }

        return jsonify({
            'success': True,
            'metadata': metadata,
            'version': '1.0.0',
            'last_updated': datetime.now().isoformat()
        })

    except Exception as e:
        app.logger.error(f"Error getting metadata: {str(e)}")
        return jsonify({'error': f'Error getting metadata: {str(e)}'}), 500


@app.route('/api/test-ai-classification', methods=['POST'])
def test_ai_classification():
    """Test AI dimension classification"""
    try:
        data = request.get_json()

        if not data or 'sql' not in data:
            return jsonify({'error': 'SQL content is required'}), 400

        sql_content = data['sql']

        # Parse SQL to get table structure
        sql_analyzer = SQLAnalyzer()
        analysis = sql_analyzer.parse_sql(sql_content)

        if not analysis.get('tables'):
            return jsonify({'error': 'No tables found in SQL'}), 400

        # Get first table for testing
        table = analysis['tables'][0]

        # Test AI classification
        ai_classifier = AIDimensionClassifier()
        classifications = ai_classifier.classify_table_dimensions(table['name'], table['columns'])

        # Format response
        result = {
            'table_name': table['name'],
            'ai_enabled': ai_classifier.enabled,
            'model_used': ai_classifier.model if ai_classifier.enabled else 'fallback',
            'classifications': []
        }

        for classification in classifications:
            result['classifications'].append({
                'column_name': classification.column_name,
                'dimension_type': classification.dimension_type,
                'dimensional_role': classification.dimensional_role,
                'confidence': classification.confidence,
                'reasoning': classification.reasoning
            })

        return jsonify({
            'success': True,
            'result': result
        })

    except Exception as e:
        app.logger.error(f"Error testing AI classification: {str(e)}")
        return jsonify({'error': f'Error testing AI classification: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
