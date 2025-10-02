#!/usr/bin/env python3

import requests
import json

# Create a session first
response = requests.post('http://localhost:5001/api/nlq/session/create', 
                        json={"metadata": {"test": "view-only"}})
session_data = response.json()
session_id = session_data['session']['session_id']
print(f"Created session: {session_id}")

# Test with just the DDL and the problematic CREATE VIEW (without the bad INSERT data)
view_only_sql = """
-- Create the tables first
CREATE TABLE dim_Genre (
    Genre_sk BIGSERIAL PRIMARY KEY,
    genre VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_Content_Rating (
    Content_Rating_sk BIGSERIAL PRIMARY KEY,
    rating VARCHAR(10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_Director (
    Director_sk BIGSERIAL PRIMARY KEY,
    director VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_Cast (
    Cast_sk BIGSERIAL PRIMARY KEY,
    actors VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_Movie (
    Movie_sk BIGSERIAL PRIMARY KEY,
    duration VARCHAR(100) NOT NULL,
    imdb_score VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_Location (
    Location_sk BIGSERIAL PRIMARY KEY,
    country VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_Language (
    Language_sk BIGSERIAL PRIMARY KEY,
    language VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_date (
    date_sk BIGSERIAL PRIMARY KEY,
    date_key VARCHAR(100) NOT NULL,
    full_date DATE NOT NULL,
    day_of_week VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fact_dados_importados (
    Genre_sk BIGINT NOT NULL,
    Content_Rating_sk BIGINT NOT NULL,
    Director_sk BIGINT NOT NULL,
    Cast_sk BIGINT NOT NULL,
    Movie_sk BIGINT NOT NULL,
    Location_sk BIGINT NOT NULL,
    Language_sk BIGINT NOT NULL,
    date_sk BIGINT NOT NULL,
    budget DECIMAL(15,2),
    box_office DECIMAL(15,2)
);

-- Now the problematic CREATE VIEW that should work with our fix
CREATE VIEW vw_fact_dados_importados_summary AS
SELECT 
    Genre.genre, Content_Rating.rating, Director.director, Cast.actors, Movie.duration, Movie.imdb_score, Location.country, Language.language, date.date_key, date.full_date, date.day_of_week,
    SUM(f.budget) as total_budget, SUM(f.box_office) as total_box_office,
    COUNT(*) as record_count
FROM fact_dados_importados f
LEFT JOIN dim_Genre Genre ON f.Genre_sk = Genre.Genre_sk
LEFT JOIN dim_Content_Rating Content_Rating ON f.Content_Rating_sk = Content_Rating.Content_Rating_sk
LEFT JOIN dim_Director Director ON f.Director_sk = Director.Director_sk
LEFT JOIN dim_Cast Cast ON f.Cast_sk = Cast.Cast_sk
LEFT JOIN dim_Movie Movie ON f.Movie_sk = Movie.Movie_sk
LEFT JOIN dim_Location Location ON f.Location_sk = Location.Location_sk
LEFT JOIN dim_Language Language ON f.Language_sk = Language.Language_sk
LEFT JOIN dim_date date ON f.date_sk = date.date_sk
GROUP BY Genre.genre, Content_Rating.rating, Director.director, Cast.actors, Movie.duration, Movie.imdb_score, Location.country, Language.language, date.date_key, date.full_date, date.day_of_week;
"""

# Try to provision with the view-only SQL
response = requests.post(f'http://localhost:5001/api/nlq/session/{session_id}/provision',
                        json={"sql": view_only_sql})

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
