-- Teste com dados reais para validar geração de DML
CREATE TABLE movies (
    id INT PRIMARY KEY,
    title VARCHAR(255),
    genre VARCHAR(100),
    director VARCHAR(100),
    year INT,
    rating DECIMAL(3,1),
    budget BIGINT,
    box_office BIGINT
);

CREATE TABLE actors (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    birth_year INT,
    nationality VARCHAR(50)
);

CREATE TABLE movie_actors (
    movie_id INT,
    actor_id INT,
    role VARCHAR(100),
    FOREIGN KEY (movie_id) REFERENCES movies(id),
    FOREIGN KEY (actor_id) REFERENCES actors(id)
);

-- Dados reais de filmes
INSERT INTO movies (id, title, genre, director, year, rating, budget, box_office) VALUES 
(1, 'The Shawshank Redemption', 'Drama', 'Frank Darabont', 1994, 9.3, 25000000, 16000000),
(2, 'The Godfather', 'Crime', 'Francis Ford Coppola', 1972, 9.2, 6000000, 245000000),
(3, 'The Dark Knight', 'Action', 'Christopher Nolan', 2008, 9.0, 185000000, 1004000000),
(4, 'Pulp Fiction', 'Crime', 'Quentin Tarantino', 1994, 8.9, 8000000, 214000000),
(5, 'Forrest Gump', 'Drama', 'Robert Zemeckis', 1994, 8.8, 55000000, 677000000);

-- Dados reais de atores
INSERT INTO actors (id, name, birth_year, nationality) VALUES 
(1, 'Morgan Freeman', 1937, 'American'),
(2, 'Tim Robbins', 1958, 'American'),
(3, 'Marlon Brando', 1924, 'American'),
(4, 'Al Pacino', 1940, 'American'),
(5, 'Christian Bale', 1974, 'British'),
(6, 'Heath Ledger', 1979, 'Australian'),
(7, 'John Travolta', 1954, 'American'),
(8, 'Samuel L. Jackson', 1948, 'American'),
(9, 'Tom Hanks', 1956, 'American');

-- Relacionamentos filme-ator
INSERT INTO movie_actors (movie_id, actor_id, role) VALUES 
(1, 1, 'Ellis Boyd Red Redding'),
(1, 2, 'Andy Dufresne'),
(2, 3, 'Vito Corleone'),
(2, 4, 'Michael Corleone'),
(3, 5, 'Bruce Wayne'),
(3, 6, 'Joker'),
(4, 7, 'Vincent Vega'),
(4, 8, 'Jules Winnfield'),
(5, 9, 'Forrest Gump');
