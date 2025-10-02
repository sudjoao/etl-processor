#!/usr/bin/env python3
"""
Test API endpoints with PostgreSQL as default dialect
"""

import requests
import json

def test_api_postgresql():
    """Test API endpoints to ensure PostgreSQL is the default"""
    
    print("🌐 Testing API endpoints with PostgreSQL...")
    
    # Test data
    test_sql = """
    CREATE TABLE customers (
        customer_id INT PRIMARY KEY,
        customer_name VARCHAR(100),
        email VARCHAR(100),
        city VARCHAR(50)
    );
    
    CREATE TABLE orders (
        order_id INT PRIMARY KEY,
        customer_id INT,
        order_date DATE,
        total_amount DECIMAL(10,2)
    );
    """
    
    base_url = "http://localhost:5001"
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the backend is running.")
        print("   Run: cd backend && python app.py")
        return
    
    # Test 2: Generate DW model with default dialect (should be PostgreSQL)
    print("\n2. Testing DW model generation with default dialect...")
    
    payload = {
        "sql": test_sql,
        "model_name": "TestDataWarehouse"
        # Note: Not specifying dialect to test default
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
            
            # Check if PostgreSQL dialect was used
            if 'complete_schema' in result:
                schema = result['complete_schema']
                dialect = schema.get('dialect', 'unknown')
                print(f"📊 Dialect used: {dialect}")
                
                if dialect == 'postgresql':
                    print("✅ PostgreSQL is the default dialect")
                else:
                    print(f"❌ Expected PostgreSQL, got {dialect}")
                
                # Check DDL for PostgreSQL syntax
                ddl_statements = schema.get('ddl_statements', [])
                if ddl_statements:
                    all_ddl = "\n".join(ddl_statements)
                    
                    print("\n🔍 Checking generated DDL for PostgreSQL syntax...")
                    
                    # PostgreSQL features to check
                    pg_features = [
                        ("BIGSERIAL", "Auto-increment columns"),
                        ("NUMERIC(", "Decimal types"),
                        ("TIMESTAMP WITH TIME ZONE", "Timestamp types"),
                        ("COMMENT ON", "Table/column comments")
                    ]
                    
                    for feature, description in pg_features:
                        if feature in all_ddl:
                            print(f"  ✅ {description}: Found {feature}")
                        else:
                            print(f"  ⚠️  {description}: {feature} not found")
                    
                    # MySQL features that should NOT be present
                    mysql_features = [
                        ("AUTO_INCREMENT", "MySQL auto-increment"),
                        ("`", "MySQL backticks"),
                        ("ENGINE=", "MySQL engine clause")
                    ]
                    
                    mysql_found = False
                    for feature, description in mysql_features:
                        if feature in all_ddl:
                            print(f"  ❌ {description}: Found {feature}")
                            mysql_found = True
                    
                    if not mysql_found:
                        print("  ✅ No MySQL-specific syntax found")
                
            else:
                print("⚠️  No complete_schema in response")
                
        else:
            print(f"❌ DW model generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing DW model generation: {e}")
    
    # Test 3: Explicitly test PostgreSQL dialect
    print("\n3. Testing explicit PostgreSQL dialect...")
    
    payload_pg = {
        "sql": test_sql,
        "model_name": "PostgreSQLTest",
        "dialect": "postgresql"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/generate-dw-model",
            json=payload_pg,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Explicit PostgreSQL dialect test successful")
        else:
            print(f"❌ Explicit PostgreSQL test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing explicit PostgreSQL: {e}")
    
    print("\n🎯 API PostgreSQL test completed!")

if __name__ == "__main__":
    test_api_postgresql()
