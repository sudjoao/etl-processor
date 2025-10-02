#!/usr/bin/env python3
"""
Test to identify the dialect issue in the API
"""

import requests
import json

def test_dialect_issue():
    """Test to see what DDL is actually being returned by the API"""
    
    print("🔍 Testing dialect issue in /api/generate-dw-model...")
    
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
    
    # Test with explicit MySQL dialect
    print("\n1. Testing with explicit MySQL dialect...")
    payload_mysql = {
        "sql": test_sql,
        "model_name": "MySQLTest",
        "dialect": "mysql"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/generate-dw-model",
            json=payload_mysql,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ MySQL test successful")
            
            # Check DDL statements from DimensionalModelingEngine
            if 'ddl_statements' in result:
                print(f"📝 DDL statements count: {len(result['ddl_statements'])}")
                print("📄 First DDL statement (from DimensionalModelingEngine):")
                print(result['ddl_statements'][0][:200] + "...")
                
                # Check for MySQL vs PostgreSQL syntax
                all_ddl = "\n".join(result['ddl_statements'])
                if "AUTO_INCREMENT" in all_ddl:
                    print("❌ Found AUTO_INCREMENT (MySQL syntax)")
                if "BIGSERIAL" in all_ddl:
                    print("✅ Found BIGSERIAL (PostgreSQL syntax)")
            
            # Check complete_schema DDL
            if 'complete_schema' in result and 'ddl_statements' in result['complete_schema']:
                complete_ddl = result['complete_schema']['ddl_statements']
                print(f"📝 Complete schema DDL count: {len(complete_ddl)}")
                print("📄 First complete schema DDL:")
                print(complete_ddl[0][:200] + "...")
                
                all_complete_ddl = "\n".join(complete_ddl)
                if "AUTO_INCREMENT" in all_complete_ddl:
                    print("❌ Complete schema has AUTO_INCREMENT (MySQL syntax)")
                if "BIGSERIAL" in all_complete_ddl:
                    print("✅ Complete schema has BIGSERIAL (PostgreSQL syntax)")
                    
                print(f"📊 Complete schema dialect: {result['complete_schema'].get('dialect', 'unknown')}")
        else:
            print(f"❌ MySQL test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing MySQL: {e}")
    
    # Test with explicit PostgreSQL dialect
    print("\n2. Testing with explicit PostgreSQL dialect...")
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
            result = response.json()
            print("✅ PostgreSQL test successful")
            
            # Check DDL statements from DimensionalModelingEngine
            if 'ddl_statements' in result:
                print(f"📝 DDL statements count: {len(result['ddl_statements'])}")
                print("📄 First DDL statement (from DimensionalModelingEngine):")
                print(result['ddl_statements'][0][:200] + "...")
                
                # Check for MySQL vs PostgreSQL syntax
                all_ddl = "\n".join(result['ddl_statements'])
                if "AUTO_INCREMENT" in all_ddl:
                    print("❌ Found AUTO_INCREMENT (MySQL syntax)")
                if "BIGSERIAL" in all_ddl:
                    print("✅ Found BIGSERIAL (PostgreSQL syntax)")
            
            # Check complete_schema DDL
            if 'complete_schema' in result and 'ddl_statements' in result['complete_schema']:
                complete_ddl = result['complete_schema']['ddl_statements']
                print(f"📝 Complete schema DDL count: {len(complete_ddl)}")
                print("📄 First complete schema DDL:")
                print(complete_ddl[0][:200] + "...")
                
                all_complete_ddl = "\n".join(complete_ddl)
                if "AUTO_INCREMENT" in all_complete_ddl:
                    print("❌ Complete schema has AUTO_INCREMENT (MySQL syntax)")
                if "BIGSERIAL" in all_complete_ddl:
                    print("✅ Complete schema has BIGSERIAL (PostgreSQL syntax)")
                    
                print(f"📊 Complete schema dialect: {result['complete_schema'].get('dialect', 'unknown')}")
        else:
            print(f"❌ PostgreSQL test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing PostgreSQL: {e}")
    
    print("\n🎯 Dialect issue test completed!")

if __name__ == "__main__":
    test_dialect_issue()
