from flask import Flask, request, jsonify
from flask_cors import CORS
import csv
import io
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

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
        self.supported_databases = ["ansi", "mysql", "postgresql", "sqlite", "sqlserver"]
    
    def sanitize_identifier(self, name: str) -> str:
        """Sanitize SQL identifier names"""
        return re.sub(r'[^a-zA-Z0-9_]', '_', name).lower()
    
    def get_sql_type(self, field_format: str, database_type: str) -> str:
        """Get SQL type based on field format and database type"""
        type_mapping = {
            "mysql": {
                "number": "DECIMAL(10,2)",
                "currency": "DECIMAL(10,2)",
                "date": "DATE",
                "text": "VARCHAR(255)"
            },
            "postgresql": {
                "number": "NUMERIC(10,2)",
                "currency": "NUMERIC(10,2)",
                "date": "DATE",
                "text": "VARCHAR(255)"
            },
            "sqlite": {
                "number": "REAL",
                "currency": "REAL",
                "date": "TEXT",
                "text": "TEXT"
            },
            "sqlserver": {
                "number": "DECIMAL(10,2)",
                "currency": "MONEY",
                "date": "DATE",
                "text": "NVARCHAR(255)"
            },
            "ansi": {
                "number": "DECIMAL(10,2)",
                "currency": "DECIMAL(10,2)",
                "date": "DATE",
                "text": "VARCHAR(255)"
            }
        }
        
        return type_mapping.get(database_type, type_mapping["ansi"]).get(field_format, "VARCHAR(255)")
    
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
                    table_name: str, database_type: str, include_create_table: bool = True) -> str:
        """Generate SQL from CSV data and field configuration"""
        
        if database_type not in self.supported_databases:
            raise ValueError(f"Unsupported database type: {database_type}")
        
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
            sql += f"-- Criação da tabela\n"
            sql += f"CREATE TABLE {self._quote_identifier(sanitized_table_name, database_type)} (\n"
            
            columns = []
            for i, field in enumerate(selected_fields):
                column_name = self.sanitize_identifier(field["name"])
                sql_type = self.get_sql_type(field.get("format", "text"), database_type)
                quoted_column = self._quote_identifier(column_name, database_type)
                columns.append(f"  {quoted_column} {sql_type}")
            
            sql += ",\n".join(columns) + "\n"
            sql += ");\n\n"
        
        # INSERT statements
        sql += f"-- Inserção dos dados\n"
        
        column_names = []
        for field in selected_fields:
            column_name = self.sanitize_identifier(field["name"])
            quoted_column = self._quote_identifier(column_name, database_type)
            column_names.append(quoted_column)
        
        columns_str = ", ".join(column_names)
        quoted_table = self._quote_identifier(sanitized_table_name, database_type)
        
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
    
    def _quote_identifier(self, identifier: str, database_type: str) -> str:
        """Quote identifier based on database type"""
        if database_type == "mysql":
            return f"`{identifier}`"
        elif database_type == "postgresql":
            return f'"{identifier}"'
        else:
            return identifier

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
        database_type = data.get("databaseType", "ansi")
        include_create_table = data.get("includeCreateTable", True)
        
        # Validate delimiter
        if delimiter not in [",", ";", "\t", "|"]:
            return jsonify({"error": "Invalid delimiter"}), 400
        
        # Parse CSV
        csv_data = transformer.parse_csv_content(csv_content, delimiter)
        
        # Generate SQL
        sql_result = transformer.generate_sql(
            csv_data=csv_data,
            fields=fields,
            table_name=table_name,
            database_type=database_type,
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
