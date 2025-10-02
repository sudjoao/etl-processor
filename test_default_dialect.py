#!/usr/bin/env python3
"""
Test default dialect behavior
"""

import requests
import json

def test_default_dialect():
    """Test that PostgreSQL is the default dialect when none is specified"""
    
    print("🔍 Testing default dialect behavior...")
    
    # Test SQL
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
    
    # Test without specifying dialect (should default to PostgreSQL)
    print("\n1. Testing without specifying dialect (should default to PostgreSQL)...")
    payload_default = {
        "sql": test_sql,
        "model_name": "DefaultDialectTest"
        # Note: No dialect specified
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/generate-dw-model",
            json=payload_default,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Default dialect test successful")
            
            # Check complete_schema dialect
            if 'complete_schema' in result:
                dialect = result['complete_schema'].get('dialect', 'unknown')
                print(f"📊 Detected dialect: {dialect}")
                
                if dialect == 'postgresql':
                    print("✅ PostgreSQL is the default dialect")
                else:
                    print(f"❌ Expected PostgreSQL, got {dialect}")
                
                # Check DDL syntax
                if 'ddl_statements' in result['complete_schema']:
                    complete_ddl = result['complete_schema']['ddl_statements']
                    all_ddl = "\n".join(complete_ddl)
                    
                    print("\n🔍 Checking DDL syntax...")
                    
                    # PostgreSQL features
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
                    
                    # Show a sample of the DDL
                    print(f"\n📄 Sample DDL (first 300 chars):")
                    print(all_ddl[:300] + "...")
                
            else:
                print("⚠️  No complete_schema in response")
                
        else:
            print(f"❌ Default dialect test failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing default dialect: {e}")
    
    print("\n🎯 Default dialect test completed!")

if __name__ == "__main__":
    test_default_dialect()
