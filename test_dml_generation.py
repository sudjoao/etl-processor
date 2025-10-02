#!/usr/bin/env python3
"""
Test script to verify DML generation with real data
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

sys.path.append('backend')

from star_schema_generator import StarSchemaGenerator, DatabaseDialect
from dimensional_modeling import DimensionalModelingEngine

# Test SQL with real data
test_sql = """
-- Criação da tabela
CREATE TABLE dados_importados (
  nome VARCHAR(255),
  cpf VARCHAR(255),
  telefone VARCHAR(255),
  email VARCHAR(255),
  tipo_visita VARCHAR(255),
  bloco VARCHAR(255),
  apartamento VARCHAR(255),
  placa_veiculo VARCHAR(255),
  horario_entrada VARCHAR(255),
  horario_saida VARCHAR(255),
  pessoa_recebeu VARCHAR(255),
  motivo VARCHAR(255),
  observacoes VARCHAR(255)
);

-- Inserção dos dados
INSERT INTO dados_importados (nome, cpf, telefone, email, tipo_visita, bloco, apartamento, placa_veiculo, horario_entrada, horario_saida, pessoa_recebeu, motivo, observacoes) VALUES ('Ana Júlia Lopes', '623.489.150-06', '(031) 1974-2443', 'luiz-miguelporto@cardoso.br', 'Prestador de Serviço', 'B', '180', 'PIH-4718', '2025-09-15 12:44:50', '2025-09-15 18:33:18', 'Cecília Freitas', 'Atque quis voluptatibus corrupti assumenda.', 'Magni aperiam voluptas qui explicabo.');
INSERT INTO dados_importados (nome, cpf, telefone, email, tipo_visita, bloco, apartamento, placa_veiculo, horario_entrada, horario_saida, pessoa_recebeu, motivo, observacoes) VALUES ('Kaique Porto', '032.461.879-40', '+55 (084) 4442 8861', 'sabrina29@bol.com.br', 'Entregador', 'D', '17', 'AAY-0651', '2025-09-15 12:08:19', NULL, 'Marina Alves', 'Distinctio quis ea nisi aperiam.', NULL);
INSERT INTO dados_importados (nome, cpf, telefone, email, tipo_visita, bloco, apartamento, placa_veiculo, horario_entrada, horario_saida, pessoa_recebeu, motivo, observacoes) VALUES ('Igor Oliveira', '432.915.078-60', '+55 84 4069-5313', 'almeidathales@das.br', 'Mudança', 'C', '27', 'OXM-9946', '2025-09-15 18:13:16', '2025-09-15 22:26:27', 'Levi Sales', 'Nobis optio ea odit soluta.', NULL);
"""

def test_dml_generation():
    print("🧪 Testing DML generation with real data...")
    
    # Initialize engines
    modeling_engine = DimensionalModelingEngine()
    schema_generator = StarSchemaGenerator(DatabaseDialect.POSTGRESQL)
    
    # Create dimensional model
    print("📊 Creating dimensional model...")
    model_result = modeling_engine.create_dimensional_model(test_sql, "TestDataWarehouse")
    
    if "error" in model_result:
        print(f"❌ Error creating model: {model_result['error']}")
        return
    
    star_schema = model_result.get("star_schema")
    if not star_schema:
        print("❌ No star schema generated")
        return
    
    print(f"✅ Star schema created: {star_schema['name']}")
    print(f"📊 Fact table: {star_schema['fact_table']['name']}")
    print(f"📊 Dimension tables: {[dim['name'] for dim in star_schema['dimension_tables']]}")
    
    # Generate complete schema with DML
    print("\n🔧 Generating complete schema with DML...")
    
    # Convert dict back to objects for the generator
    from dimensional_modeling import StarSchema, FactTable, DimensionTable
    
    fact_table = FactTable(
        name=star_schema['fact_table']['name'],
        source_table=star_schema['fact_table']['source_table'],
        measures=star_schema['fact_table']['measures'],
        dimension_keys=star_schema['fact_table']['dimension_keys'],
        grain=star_schema['fact_table']['grain'],
        description=star_schema['fact_table']['description']
    )
    
    dimension_tables = []
    for dim_data in star_schema['dimension_tables']:
        dim_table = DimensionTable(
            name=dim_data['name'],
            source_table=dim_data['source_table'],
            surrogate_key=dim_data['surrogate_key'],
            natural_key=dim_data['natural_key'],
            attributes=dim_data['attributes'],
            scd_type=dim_data['scd_type'],
            description=dim_data['description']
        )
        dimension_tables.append(dim_table)
    
    star_schema_obj = StarSchema(
        name=star_schema['name'],
        fact_table=fact_table,
        dimension_tables=dimension_tables,
        relationships=star_schema['relationships'],
        metadata=star_schema['metadata']
    )
    
    complete_schema = schema_generator.generate_complete_schema(
        star_schema_obj,
        include_sample_data=True,
        sample_records=5,
        original_sql=test_sql
    )
    
    print(f"✅ Complete schema generated with keys: {list(complete_schema.keys())}")
    
    # Check DML statements
    if 'dml_statements' in complete_schema:
        print(f"\n📝 DML statements generated: {list(complete_schema['dml_statements'].keys())}")
        
        for table_name, dml in complete_schema['dml_statements'].items():
            print(f"\n--- {table_name} ---")
            print(dml[:500] + "..." if len(dml) > 500 else dml)
    else:
        print("❌ No DML statements found")

if __name__ == "__main__":
    test_dml_generation()
