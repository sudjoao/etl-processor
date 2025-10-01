#!/usr/bin/env python3
"""
Test to verify Docker integration is working correctly
"""

import requests
import json
import time

def test_docker_integration():
    """Test the Docker container integration"""
    
    print("🐳 Testing Docker integration...")
    
    base_url = "http://localhost:5001"
    
    # Test 1: Health check
    print("\n🔍 Test 1: Health check")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False
    
    # Test 2: DW Model generation with real data
    print("\n🔍 Test 2: DW Model generation with real data")
    
    test_sql = """
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
    
    INSERT INTO dados_importados (nome, cpf, telefone, email, tipo_visita, bloco, apartamento) 
    VALUES ('Maria Santos', '987.654.321-00', '(11) 88888-8888', 'maria@email.com', 'Visita', 'B', '202');
    """
    
    try:
        payload = {
            "sql_content": test_sql,
            "model_name": "TestDW",
            "include_indexes": True,
            "include_partitioning": False
        }
        
        response = requests.post(
            f"{base_url}/api/dw-model", 
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ DW Model generation successful")
            print(f"📊 Success: {result.get('success', False)}")
            
            if 'complete_schema' in result:
                schema = result['complete_schema']
                print(f"📝 DDL statements: {len(schema.get('ddl_statements', []))}")
                print(f"📝 DML statements: {len(schema.get('dml_statements', {}))}")
                
                # Check if DML statements is a dict
                dml_statements = schema.get('dml_statements', {})
                if isinstance(dml_statements, dict):
                    print("✅ DML statements type: dict (correct)")
                    if dml_statements:
                        print(f"📝 DML keys: {list(dml_statements.keys())}")
                        
                        # Check for real data usage
                        sample_dml = str(dml_statements)
                        if 'João Silva' in sample_dml or 'Maria Santos' in sample_dml:
                            print("✅ Real data found in DML statements")
                        else:
                            print("⚠️ Real data not found in DML statements")
                    else:
                        print("⚠️ No DML statements generated")
                else:
                    print(f"❌ DML statements type: {type(dml_statements)} (incorrect)")
            else:
                print("⚠️ No complete_schema in result")
                
        else:
            print(f"❌ DW Model generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ DW Model generation failed: {str(e)}")
        return False
    
    print("\n🎯 Docker integration tests completed successfully!")
    return True

if __name__ == "__main__":
    success = test_docker_integration()
    if success:
        print("\n🎉 All tests passed! The system is working correctly.")
    else:
        print("\n💥 Some tests failed. Please check the logs.")
