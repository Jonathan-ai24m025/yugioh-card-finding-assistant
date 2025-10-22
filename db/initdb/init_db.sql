CREATE TABLE cards (
    index_id INTEGER,
    name TEXT,
    description TEXT,
    set_id TEXT,
    rarity TEXT,
    price TEXT,
    volatility TEXT,
    type TEXT,
    sub_type TEXT,
    attribute TEXT,
    rank TEXT,
    attack TEXT,
    defense TEXT,
    set_name TEXT,
    set_release TEXT,
    name_official TEXT,
    index INTEGER,
    index_market INTEGER,
    join_id TEXT
);

COPY cards(index_id, name, description, set_id, rarity, price, volatility, type, sub_type,
           attribute, rank, attack, defense, set_name, set_release, name_official,
           index, index_market, join_id)
FROM '/docker-entrypoint-initdb.d/cards.csv'
DELIMITER ','
CSV HEADER
QUOTE '"'
ESCAPE '"';

