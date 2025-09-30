#!/usr/bin/env python3
"""
Script para testar a classificação de IA com o dataset de filmes
"""

import requests
import json
import csv

def get_movies_sql():
    """Retorna SQL de exemplo para filmes"""
    return """
CREATE TABLE movies (
    title VARCHAR(255),
    genre VARCHAR(100),
    rating VARCHAR(10),
    year INT,
    director VARCHAR(255),
    actors TEXT,
    budget BIGINT,
    box_office BIGINT,
    duration INT,
    country VARCHAR(100),
    language VARCHAR(100),
    imdb_score DECIMAL(3,1)
);

INSERT INTO movies VALUES ('The Quiet Dawn', 'Drama', 'PG-13', 2019, 'Sofia Coppola', 'Emma Stone, Timothy Chalamet', 5000000, 12000000, 102, 'USA', 'English', 7.2);
INSERT INTO movies VALUES ('Midnight Chase', 'Action', 'R', 2018, 'Christopher Nolan', 'Tom Hardy, Idris Elba, Emily Blunt', 85000000, 210000000, 130, 'UK', 'English', 7.8);
INSERT INTO movies VALUES ('Love in Lisbon', 'Romance', 'PG', 2017, 'Paula Ortiz', 'Penelope Cruz, Andres Velencoso', 10000000, 17000000, 95, 'Portugal', 'Portuguese', 6.9);
INSERT INTO movies VALUES ('Ghosts of Yesterday', 'Horror', 'R', 2020, 'Jordan Peele', 'Lupita Nyongo, Daniel Kaluuya', 12000000, 60000000, 110, 'USA', 'English', 7.4);
INSERT INTO movies VALUES ('The Last Harbor', 'Adventure', 'PG-13', 2015, 'Peter Weir', 'Chris Hemsworth, Naomi Watts', 90000000, 320000000, 145, 'Australia', 'English', 7.1);
"""

def test_dw_generation():
    """Testa a geração do modelo DW"""
    print("🎬 Testando classificação de IA com dataset de filmes...")
    
    # Ler dados dos filmes
    sql_content = get_movies_sql()
    print(f"📄 SQL gerado com {len(sql_content)} caracteres")
    
    # Fazer requisição para gerar modelo DW
    url = "http://localhost:5001/api/generate-dw-model"
    payload = {
        "sql": sql_content,
        "model_name": "MoviesDataWarehouse",
        "dialect": "mysql",
        "include_indexes": True,
        "include_partitioning": False
    }
    
    print("🌐 Fazendo requisição para gerar modelo DW...")
    try:
        response = requests.post(url, json=payload, timeout=60)
        print(f"📊 Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Modelo DW gerado com sucesso!")
            
            # Verificar se há star schema
            if 'star_schema' in result:
                star_schema = result['star_schema']
                print(f"⭐ Fact table: {star_schema.get('fact_table', {}).get('name', 'N/A')}")
                print(f"⭐ Dimension tables: {len(star_schema.get('dimension_tables', []))}")
                
                # Mostrar dimensões encontradas
                for dim in star_schema.get('dimension_tables', []):
                    print(f"   - {dim.get('name', 'N/A')}: {len(dim.get('attributes', []))} attributes")
            
            # Salvar resultado completo
            with open('test_result.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print("💾 Resultado salvo em test_result.json")
            
        else:
            print(f"❌ Erro na requisição: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")

if __name__ == "__main__":
    test_dw_generation()
