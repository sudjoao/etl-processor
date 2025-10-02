#!/usr/bin/env python3
"""
Comprehensive test to verify all functionality is working correctly
"""

import sys
import os
sys.path.append('backend')

from dimensional_modeling import DimensionalModelingEngine
from star_schema_generator import StarSchemaGenerator, DatabaseDialect
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def test_comprehensive():
    """Test all major functionality"""
    
    print("🧪 Running comprehensive tests...")
    
    # Test SQL with different scenarios
    test_cases = [
        {
            "name": "Simple visitor data",
            "sql": """
            CREATE TABLE dados_importados (
                nome VARCHAR(255),
                cpf VARCHAR(255),
                telefone VARCHAR(255),
                email VARCHAR(255),
                tipo_visita VARCHAR(255),
                bloco VARCHAR(255),
                apartamento VARCHAR(255)
            );
            
            INSERT INTO dados_importados (nome, cpf, telefone, email, tipo_visita, bloco, apartamento) 
            VALUES ('João Silva', '123.456.789-00', '(11) 99999-9999', 'joao@email.com', 'Entrega', 'A', '101');
            """
        },
        {
            "name": "No real data (DDL only)",
            "sql": """
            CREATE TABLE produtos (
                id INT PRIMARY KEY,
                nome VARCHAR(255),
                categoria VARCHAR(100),
                preco DECIMAL(10,2)
            );
            """
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        
        try:
            # Create dimensional modeling engine
            engine = DimensionalModelingEngine()
            
            # Create dimensional model
            result = engine.create_dimensional_model(
                sql_content=test_case['sql'],
                model_name=f"Test_{i}"
            )
            
            if result['success']:
                star_schema = result['star_schema']

                # Check if star_schema is a dict or object
                if isinstance(star_schema, dict):
                    print(f"✅ Star schema created: {star_schema.get('name', 'Unknown')}")
                    print(f"📊 Fact table: {star_schema.get('fact_table', {}).get('name', 'Unknown')}")
                    print(f"📊 Dimension tables: {len(star_schema.get('dimension_tables', []))}")
                    print("⚠️ Star schema returned as dict, skipping schema generator test")
                    continue
                else:
                    print(f"✅ Star schema created: {star_schema.name}")
                    print(f"📊 Fact table: {star_schema.fact_table.name}")
                    print(f"📊 Dimension tables: {len(star_schema.dimension_tables)}")

                # Test schema generator
                schema_generator = StarSchemaGenerator(DatabaseDialect.POSTGRESQL)

                complete_schema = schema_generator.generate_complete_schema(
                    star_schema,
                    include_sample_data=False,
                    original_sql=test_case['sql']
                )
                
                print(f"✅ Complete schema generated")
                print(f"📝 DDL statements: {len(complete_schema['ddl_statements'])}")
                print(f"📝 DML statements: {len(complete_schema['dml_statements'])}")
                
                # Check if DML statements is a dict
                if isinstance(complete_schema['dml_statements'], dict):
                    print(f"✅ DML statements type: dict (correct)")
                    print(f"📝 DML keys: {list(complete_schema['dml_statements'].keys())}")
                else:
                    print(f"❌ DML statements type: {type(complete_schema['dml_statements'])} (incorrect)")
                
            else:
                print(f"❌ Failed to create star schema: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Test {i} failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n🎯 Comprehensive tests completed!")

if __name__ == "__main__":
    test_comprehensive()
