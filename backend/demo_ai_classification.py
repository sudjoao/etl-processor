#!/usr/bin/env python3
"""
Demo script para mostrar a diferença entre classificação IA e fallback
"""

import os
import json
from ai_dimension_classifier import AIDimensionClassifier

def demo_classification():
    """Demonstra a classificação de dimensões"""
    
    # Dados de exemplo - tabela de vendas
    sample_columns = [
        {"name": "id_venda", "data_type": "INT", "sample_values": ["1", "2", "3"]},
        {"name": "data_venda", "data_type": "DATE", "sample_values": ["2024-01-15", "2024-01-16"]},
        {"name": "cliente_nome", "data_type": "VARCHAR(255)", "sample_values": ["João Silva", "Maria Santos"]},
        {"name": "cliente_email", "data_type": "VARCHAR(255)", "sample_values": ["joao@email.com", "maria@email.com"]},
        {"name": "produto_nome", "data_type": "VARCHAR(255)", "sample_values": ["Notebook", "Mouse"]},
        {"name": "categoria", "data_type": "VARCHAR(100)", "sample_values": ["Eletrônicos", "Acessórios"]},
        {"name": "quantidade", "data_type": "INT", "sample_values": ["1", "2", "5"]},
        {"name": "preco_unitario", "data_type": "DECIMAL(10,2)", "sample_values": ["1500.00", "25.90"]},
        {"name": "valor_total", "data_type": "DECIMAL(10,2)", "sample_values": ["1500.00", "51.80"]},
        {"name": "vendedor", "data_type": "VARCHAR(255)", "sample_values": ["Carlos", "Ana"]},
        {"name": "regiao", "data_type": "VARCHAR(100)", "sample_values": ["Sudeste", "Norte"]}
    ]
    
    print("🤖 Demo: Classificação IA de Dimensões")
    print("=" * 50)
    
    # Inicializar classificador
    classifier = AIDimensionClassifier()
    
    print(f"IA Habilitada: {classifier.enabled}")
    print(f"Modelo: {classifier.model}")
    print(f"Chave API configurada: {'Sim' if classifier.api_key else 'Não'}")
    print()
    
    # Classificar dimensões
    print("Classificando tabela 'vendas'...")
    classifications = classifier.classify_table_dimensions("vendas", sample_columns)
    
    print("\n📊 Resultados da Classificação:")
    print("-" * 80)
    print(f"{'Coluna':<20} {'Tipo Dimensão':<15} {'Papel':<20} {'Confiança':<10} {'Método'}")
    print("-" * 80)
    
    for classification in classifications:
        method = "IA" if "Fallback" not in classification.reasoning else "Fallback"
        print(f"{classification.column_name:<20} {classification.dimension_type:<15} {classification.dimensional_role:<20} {classification.confidence:<10.2f} {method}")
    
    print("\n💡 Detalhes das Classificações:")
    print("-" * 50)
    
    for classification in classifications:
        print(f"\n🔹 {classification.column_name}")
        print(f"   Tipo: {classification.dimension_type}")
        print(f"   Papel: {classification.dimensional_role}")
        print(f"   Confiança: {classification.confidence:.2f}")
        print(f"   Raciocínio: {classification.reasoning}")
    
    print("\n" + "=" * 50)
    print("✅ Demo concluída!")
    
    if not classifier.enabled or not classifier.api_key:
        print("\n💡 Dica: Para usar a classificação IA:")
        print("1. Obtenha uma chave em https://openrouter.ai/")
        print("2. Configure no .env: OPENROUTER_API_KEY=sk-or-v1-sua-chave")
        print("3. Execute novamente para ver a diferença!")

if __name__ == "__main__":
    demo_classification()
