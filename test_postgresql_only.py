#!/usr/bin/env python3
"""
Test PostgreSQL-only functionality after removing multi-dialect support
"""

import requests
import json
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from dimensional_modeling import DimensionalModelingEngine
from star_schema_generator import StarSchemaGenerator

def test_backend_components():
    """Test backend components work without dialect parameters"""
    print("🧪 Testing backend components...")
    
    # Test DimensionalModelingEngine
    try:
        modeling_engine = DimensionalModelingEngine()
        print("✅ DimensionalModelingEngine initialized successfully")
    except Exception as e:
        print(f"❌ DimensionalModelingEngine failed: {e}")
        return False
    
    # Test StarSchemaGenerator
    try:
        schema_generator = StarSchemaGenerator()
        print("✅ StarSchemaGenerator initialized successfully")
    except Exception as e:
        print(f"❌ StarSchemaGenerator failed: {e}")
        return False
    
    return True

def test_api_endpoints():
    """Test API endpoints generate PostgreSQL-only syntax"""
    print("\n🌐 Testing API endpoints...")
    
    base_url = "http://localhost:5001"
    
    # Test SQL for data warehouse generation
    test_sql = """
    CREATE TABLE vendas (
        id INT PRIMARY KEY,
        produto VARCHAR(100),
        categoria VARCHAR(50),
        preco DECIMAL(10,2),
        data_venda DATE,
        vendedor VARCHAR(100),
        regiao VARCHAR(50)
    );
    """
    
    # Test 1: Generate DW Model (should be PostgreSQL by default)
    print("\n1. Testing /api/generate-dw-model endpoint...")
    
    payload = {
        "sql": test_sql,
        "model_name": "PostgreSQLOnlyTest",
        "include_indexes": True,
        "include_partitioning": False
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/generate-dw-model",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ DW model generation successful")
            
            # Check dialect
            if 'complete_schema' in result:
                dialect = result['complete_schema'].get('dialect', 'unknown')
                print(f"📊 Dialect: {dialect}")
                
                if dialect == 'postgresql':
                    print("✅ PostgreSQL is the default and only dialect")
                else:
                    print(f"❌ Expected PostgreSQL, got {dialect}")
                    return False
                
                # Check for PostgreSQL-specific syntax
                ddl_statements = result['complete_schema'].get('ddl_statements', [])
                all_ddl = ' '.join(ddl_statements)
                
                postgresql_features = [
                    ('BIGSERIAL', 'PostgreSQL auto-increment'),
                    ('NUMERIC(', 'PostgreSQL decimal type'),
                    ('TIMESTAMP WITH TIME ZONE', 'PostgreSQL timestamp'),
                ]
                
                print("  🔍 Checking for PostgreSQL syntax:")
                for feature, description in postgresql_features:
                    if feature in all_ddl:
                        print(f"    ✅ {description}: Found {feature}")
                    else:
                        print(f"    ⚠️  {description}: Not found")
                
                # Check for MySQL-specific syntax (should not exist)
                mysql_features = [
                    ('AUTO_INCREMENT', 'MySQL auto-increment'),
                    ('ENGINE=', 'MySQL storage engine'),
                    ('`', 'MySQL backticks'),
                ]
                
                print("  🔍 Checking for MySQL syntax (should not exist):")
                mysql_found = False
                for feature, description in mysql_features:
                    if feature in all_ddl:
                        print(f"    ❌ {description}: Found {feature}")
                        mysql_found = True
                
                if not mysql_found:
                    print("    ✅ No MySQL-specific syntax found")
                
            else:
                print("⚠️  No complete_schema in response")
                
        else:
            print(f"❌ DW model generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing DW model generation: {e}")
        return False
    
    # Test 2: CSV Transform endpoint
    print("\n2. Testing /api/transform endpoint...")
    
    csv_payload = {
        "csvContent": "name,age,salary\nJohn,30,50000\nJane,25,45000",
        "fields": [
            {"name": "name", "selected": True, "format": "text", "order": 0},
            {"name": "age", "selected": True, "format": "number", "order": 1},
            {"name": "salary", "selected": True, "format": "currency", "order": 2}
        ],
        "tableName": "employees",
        "delimiter": ",",
        "includeCreateTable": True
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/transform",
            json=csv_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ CSV transform successful")
            
            sql = result.get('sql', '')
            print("  🔍 Checking generated SQL:")
            
            # Check for PostgreSQL syntax
            if 'NUMERIC(' in sql:
                print("    ✅ PostgreSQL NUMERIC type found")
            else:
                print("    ❌ PostgreSQL NUMERIC type not found")
                return False
            
            if '"' in sql and '`' not in sql:
                print("    ✅ PostgreSQL quoted identifiers found (no MySQL backticks)")
            else:
                print("    ❌ Incorrect identifier quoting")
                return False
                
        else:
            print(f"❌ CSV transform failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing CSV transform: {e}")
        return False
    
    return True

def test_metadata_endpoint():
    """Test metadata endpoint shows PostgreSQL-only support"""
    print("\n3. Testing /api/dw-metadata endpoint...")
    
    base_url = "http://localhost:5001"
    
    try:
        response = requests.get(f"{base_url}/api/dw-metadata")
        
        if response.status_code == 200:
            response_data = response.json()
            print("✅ Metadata endpoint successful")

            # Extract supported_dialects from nested metadata
            metadata = response_data.get('metadata', {})
            supported_dialects = metadata.get('supported_dialects', [])
            print(f"📊 Supported dialects: {supported_dialects}")

            if supported_dialects == ['postgresql']:
                print("✅ Only PostgreSQL is supported")
                return True
            else:
                print(f"❌ Expected ['postgresql'], got {supported_dialects}")
                return False
                
        else:
            print(f"❌ Metadata endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing metadata endpoint: {e}")
        return False

def main():
    """Run all PostgreSQL-only tests"""
    print("🚀 Testing PostgreSQL-only functionality")
    print("=" * 50)
    
    # Test backend components
    backend_ok = test_backend_components()
    
    # Test API endpoints
    api_ok = test_api_endpoints()
    
    # Test metadata
    metadata_ok = test_metadata_endpoint()
    
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"  Backend Components: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"  API Endpoints: {'✅ PASS' if api_ok else '❌ FAIL'}")
    print(f"  Metadata: {'✅ PASS' if metadata_ok else '❌ FAIL'}")
    
    if backend_ok and api_ok and metadata_ok:
        print("\n🎉 All tests passed! PostgreSQL-only migration successful!")
        return True
    else:
        print("\n❌ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
