#!/usr/bin/env python3
"""
Test PostgreSQL migration - verify that generated SQL is valid PostgreSQL syntax
"""

import sys
import os
sys.path.append('backend')

from dimensional_modeling import DimensionalModelingEngine
from star_schema_generator import StarSchemaGenerator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def test_postgresql_migration():
    """Test PostgreSQL migration by generating SQL and verifying syntax"""
    
    print("🐘 Testing PostgreSQL migration...")
    
    # Test SQL with sales data
    test_sql = """
    CREATE TABLE sales (
        sale_id INT PRIMARY KEY,
        customer_id INT,
        product_id INT,
        quantity INT,
        unit_price DECIMAL(10,2),
        total_amount DECIMAL(10,2),
        sale_date DATE,
        store_id INT
    );
    
    CREATE TABLE customers (
        customer_id INT PRIMARY KEY,
        customer_name VARCHAR(100),
        email VARCHAR(100),
        city VARCHAR(50),
        state VARCHAR(2)
    );
    
    CREATE TABLE products (
        product_id INT PRIMARY KEY,
        product_name VARCHAR(100),
        category VARCHAR(50),
        price DECIMAL(10,2)
    );
    """
    
    print("📊 Creating dimensional model...")
    
    # Initialize engines
    modeling_engine = DimensionalModelingEngine()
    
    # Create dimensional model
    model_result = modeling_engine.create_dimensional_model(test_sql, "SalesDataWarehouse")
    
    if "error" in model_result:
        print(f"❌ Error creating model: {model_result['error']}")
        return
    
    # Get the star schema from the modeling engine
    if not modeling_engine.star_schemas:
        print("❌ No star schema generated")
        return

    star_schema = modeling_engine.star_schemas[0]

    print("✅ Star schema created successfully")
    print(f"📊 Fact table: {star_schema.fact_table.name}")
    print(f"📊 Dimension tables: {len(star_schema.dimension_tables)}")

    # Test PostgreSQL schema generation
    print("\n🐘 Generating PostgreSQL DDL...")
    schema_generator = StarSchemaGenerator()

    complete_schema = schema_generator.generate_complete_schema(
        star_schema,
        include_indexes=True,
        include_constraints=True,
        include_sample_data=False
    )
    
    print("✅ PostgreSQL schema generated successfully")
    print(f"📝 DDL statements: {len(complete_schema['ddl_statements'])}")
    print(f"📝 Indexes: {len(complete_schema['indexes'])}")
    print(f"📝 Constraints: {len(complete_schema['constraints'])}")
    
    # Display generated DDL
    print("\n📄 Generated PostgreSQL DDL:")
    print("=" * 80)
    
    for i, ddl in enumerate(complete_schema['ddl_statements'], 1):
        print(f"\n-- DDL Statement {i}")
        print(ddl)
    
    # Display indexes
    if complete_schema['indexes']:
        print("\n-- Indexes")
        for index in complete_schema['indexes']:
            print(index)
    
    # Display constraints
    if complete_schema['constraints']:
        print("\n-- Foreign Key Constraints")
        for constraint in complete_schema['constraints']:
            print(constraint)
    
    # Verify PostgreSQL-specific syntax
    print("\n🔍 Verifying PostgreSQL syntax...")
    
    all_sql = "\n".join(complete_schema['ddl_statements'])
    
    # Check for PostgreSQL-specific features
    checks = [
        ("BIGSERIAL", "✅ Uses BIGSERIAL for auto-increment"),
        ("NUMERIC(", "✅ Uses NUMERIC for decimal types"),
        ("TIMESTAMP WITH TIME ZONE", "✅ Uses TIMESTAMP WITH TIME ZONE"),
        ("COMMENT ON TABLE", "✅ Uses COMMENT ON TABLE syntax"),
        ("COMMENT ON COLUMN", "✅ Uses COMMENT ON COLUMN syntax")
    ]
    
    # Check for MySQL-specific syntax that should NOT be present
    mysql_checks = [
        ("AUTO_INCREMENT", "❌ Found MySQL AUTO_INCREMENT"),
        ("DECIMAL(", "⚠️  Found DECIMAL (should be NUMERIC)"),
        ("`", "❌ Found MySQL backticks"),
        ("ENGINE=", "❌ Found MySQL ENGINE clause"),
        ("CHARSET=", "❌ Found MySQL CHARSET clause")
    ]
    
    print("\n✅ PostgreSQL Features:")
    for pattern, message in checks:
        if pattern in all_sql:
            print(f"  {message}")
    
    print("\n🚫 MySQL Syntax Check:")
    mysql_found = False
    for pattern, message in mysql_checks:
        if pattern in all_sql:
            print(f"  {message}")
            mysql_found = True
    
    if not mysql_found:
        print("  ✅ No MySQL-specific syntax found")
    
    print("\n🎯 PostgreSQL migration test completed!")
    
    return complete_schema

if __name__ == "__main__":
    test_postgresql_migration()
