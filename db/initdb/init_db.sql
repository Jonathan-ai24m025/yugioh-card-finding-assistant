-- ------------------------
-- Lookup tables
-- ------------------------
CREATE TABLE types (
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE attributes (
    attribute_id SERIAL PRIMARY KEY,
    attribute_name VARCHAR(50) UNIQUE
);

CREATE TABLE volatilities (
    volatility_id SERIAL PRIMARY KEY,
    volatility_name VARCHAR(50) NOT NULL UNIQUE
);

-- ------------------------
-- Main tables
-- ------------------------
CREATE TABLE card_sets (
    card_set_id INT PRIMARY KEY,
    set_id VARCHAR(50),
    set_name VARCHAR(255),
    set_release DATE,
    join_id VARCHAR(50)
);

CREATE TABLE cards (
    card_id INT PRIMARY KEY,
    card_set_id INT NOT NULL REFERENCES card_sets(card_set_id), -- foreign key to card_sets
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rarity VARCHAR(100),
    price FLOAT,
    volatility_id INT REFERENCES volatilities(volatility_id),
    type_id INT REFERENCES types(type_id),
    sub_type VARCHAR(100),
    attribute_id INT REFERENCES attributes(attribute_id),
    rank VARCHAR(100),
    attack FLOAT,
    defense FLOAT
);

-- ------------------------
-- Populate lookup tables
-- ------------------------
-- Types
INSERT INTO types (type_name) VALUES
('NONE'),
('MONSTER'),
('SPELL'),
('TRAP');

-- Attributes
INSERT INTO attributes (attribute_name) VALUES
('NONE'),
('EARTH'),
('WIND'),
('WATER'),
('DARK'),
('LIGHT'),
('FIRE'),
('DIVINE');

-- Volatility
INSERT INTO volatilities (volatility_name) VALUES
('NONE'),
('Low'),
('Med'),
('High'),
('Indeterminate');

-- ------------------------
-- Load CSV data
-- ------------------------


COPY card_sets(set_id, set_name, set_release, join_id, card_set_id)
FROM '/docker-entrypoint-initdb.d/cleaned_card_sets.csv'
DELIMITER ','
CSV HEADER;


COPY cards(card_id, card_set_id, name, description, rarity, price, volatility_id, type_id, sub_type, attribute_id, rank, attack, defense)
FROM '/docker-entrypoint-initdb.d/cleaned_cards.csv'
DELIMITER ','
CSV HEADER;



