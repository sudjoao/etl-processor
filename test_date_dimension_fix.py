#!/usr/bin/env python3

import requests
import json

# Test CSV data from movies_10.csv
csv_data = {
    "headers": ["title", "genre", "rating", "year", "director", "actors", "budget", "box_office", "duration", "country", "language", "imdb_score"],
    "rows": [
        ["The Quiet Dawn", "Drama", "PG-13", "2019", "Sofia Coppola", "Emma Stone,Timothy Chalamet", "5000000", "12000000", "102", "USA", "English", "7.2"],
        ["Midnight Chase", "Action", "R", "2018", "Christopher Nolan", "Tom Hardy,Idris Elba,Emily Blunt", "85000000", "210000000", "130", "UK", "English", "7.8"],
        ["Love in Lisbon", "Romance", "PG", "2017", "Paula Ortiz", "Penélope Cruz,Andrés Velencoso", "10000000", "17000000", "95", "Portugal", "Portuguese", "6.9"]
    ]
}

print("🔄 Testing date dimension fix...")

# First, generate SQL from CSV data
print("\n🔄 Step 1: Generating SQL from CSV data...")
transform_payload = {
    "csvContent": "title,genre,rating,year,director,actors,budget,box_office,duration,country,language,imdb_score\nThe Quiet Dawn,Drama,PG-13,2019,Sofia Coppola,\"Emma Stone,Timothy Chalamet\",5000000,12000000,102,USA,English,7.2\nMidnight Chase,Action,R,2018,Christopher Nolan,\"Tom Hardy,Idris Elba,Emily Blunt\",85000000,210000000,130,UK,English,7.8\nLove in Lisbon,Romance,PG,2017,Paula Ortiz,\"Penélope Cruz,Andrés Velencoso\",10000000,17000000,95,Portugal,Portuguese,6.9",
    "fields": [
        {"name": "title", "selected": True, "format": "text", "order": 0},
        {"name": "genre", "selected": True, "format": "text", "order": 1},
        {"name": "rating", "selected": True, "format": "text", "order": 2},
        {"name": "year", "selected": True, "format": "number", "order": 3},
        {"name": "director", "selected": True, "format": "text", "order": 4},
        {"name": "actors", "selected": True, "format": "text", "order": 5},
        {"name": "budget", "selected": True, "format": "currency", "order": 6},
        {"name": "box_office", "selected": True, "format": "currency", "order": 7},
        {"name": "duration", "selected": True, "format": "number", "order": 8},
        {"name": "country", "selected": True, "format": "text", "order": 9},
        {"name": "language", "selected": True, "format": "text", "order": 10},
        {"name": "imdb_score", "selected": True, "format": "number", "order": 11}
    ],
    "tableName": "movies",
    "delimiter": ",",
    "includeCreateTable": True
}

response = requests.post('http://localhost:5001/api/transform', json=transform_payload)
if response.status_code != 200:
    print(f"❌ Failed to generate SQL: {response.status_code}")
    print(response.text)
    exit(1)

sql_result = response.json()
sql_content = sql_result['sql']
print(f"✅ SQL generated successfully ({len(sql_content)} characters)")

# Now test DW model generation with CSV data
print("\n🔄 Step 2: Generating DW model with CSV data and date dimension fix...")
dw_payload = {
    "sql": sql_content,
    "model_name": "TestDataWarehouse",
    "include_indexes": True,
    "include_partitioning": False,
    "csv_data": csv_data
}

response = requests.post('http://localhost:5001/api/generate-dw-model', json=dw_payload)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print("✅ DW Model generation successful!")
    
    # Construct complete SQL from DDL and DML statements
    complete_sql_parts = []
    
    # Add DDL statements
    ddl_statements = result['complete_schema'].get('ddl_statements', [])
    if ddl_statements:
        complete_sql_parts.extend(ddl_statements)
        print(f"📊 Added {len(ddl_statements)} DDL statements")
    
    # Add DML statements
    dml_statements = result['complete_schema'].get('dml_statements', {})
    if dml_statements:
        for table_name, dml in dml_statements.items():
            if dml:
                complete_sql_parts.append(dml)
        print(f"📊 Added {len(dml_statements)} DML statement groups")
    
    if complete_sql_parts:
        complete_sql = '\n\n'.join(complete_sql_parts)
        with open('data/test_date_dimension_fixed.sql', 'w') as f:
            f.write(complete_sql)
        print(f"💾 Complete SQL saved to data/test_date_dimension_fixed.sql ({len(complete_sql)} characters)")
        
        # Test provisioning
        print("\n🔄 Step 3: Testing provisioning with fixed date dimension...")
        session_response = requests.post('http://localhost:5001/api/nlq/session/create', 
                                       json={"metadata": {"test": "date-dimension-fix"}})
        
        if session_response.status_code == 200:
            session_data = session_response.json()
            session_id = session_data['session']['session_id']
            print(f"✅ Session created: {session_id}")
            
            # Provision the generated SQL
            provision_response = requests.post(f'http://localhost:5001/api/nlq/session/{session_id}/provision',
                                             json={"sql": complete_sql})
            print(f"Provision Status Code: {provision_response.status_code}")
            
            if provision_response.status_code == 200:
                print("🎉 PROVISIONING SUCCESSFUL!")
                print("✅ Date dimension fix working!")
                print("✅ Complete workflow working end-to-end!")
            else:
                print(f"❌ Provisioning failed: {provision_response.status_code}")
                try:
                    error_data = provision_response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Error text: {provision_response.text}")
        else:
            print(f"❌ Session creation failed: {session_response.status_code}")
    else:
        print("❌ No DDL or DML statements found")
        
else:
    print(f"❌ DW Model generation failed: {response.status_code}")
    print(f"Response: {response.text}")
