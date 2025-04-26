CREATE TABLE IF NOT EXISTS books
(
    ISBN                TEXT PRIMARY KEY,
    Book_Title          TEXT,
    Book_Author         TEXT,
    Year_Of_Publication INTEGER,
    Publisher           TEXT,
    Image_URL           TEXT
);

CREATE TABLE IF NOT EXISTS users
(
    User_ID  SERIAL PRIMARY KEY,
    Username TEXT,
    Password TEXT,
    Role     TEXT CHECK (Role IN ('user', 'admin')) DEFAULT 'user'
);

CREATE TABLE IF NOT EXISTS ratings
(
    User_ID     INTEGER REFERENCES users (User_ID) ON DELETE CASCADE,
    ISBN        TEXT REFERENCES books (ISBN) ON DELETE CASCADE,
    Book_Rating INTEGER CHECK (Book_Rating BETWEEN 0 AND 10),
    PRIMARY KEY (User_ID, ISBN)
);

CREATE TABLE IF NOT EXISTS inventory
(
    ISBN     TEXT REFERENCES books (ISBN) ON DELETE CASCADE,
    Quantity INTEGER CHECK (Quantity >= 0),
    Price    NUMERIC CHECK (Price >= 0),
    PRIMARY KEY (ISBN)
);

CREATE TABLE IF NOT EXISTS orders
(
    Order_ID   SERIAL PRIMARY KEY,
    User_ID    INTEGER REFERENCES users (User_ID) ON DELETE CASCADE,
    Address    TEXT,
    Order_Date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items
(
    Order_ID INTEGER REFERENCES orders (Order_ID) ON DELETE CASCADE,
    ISBN     TEXT REFERENCES books (ISBN) ON DELETE CASCADE,
    PRIMARY KEY (Order_ID, ISBN)
);

CREATE TABLE IF NOT EXISTS cart_items
(
    User_ID INTEGER REFERENCES users (User_ID) ON DELETE CASCADE,
    ISBN    TEXT REFERENCES books (ISBN) ON DELETE CASCADE,
    PRIMARY KEY (User_ID, ISBN)
);

COPY books (ISBN, Book_Title, Book_Author, Year_Of_Publication, Publisher, Image_URL)
    FROM '/docker-entrypoint-initdb.d/books.csv'
    DELIMITER ',' CSV HEADER;

COPY users (User_ID, Username, Password)
    FROM '/docker-entrypoint-initdb.d/users.csv'
    DELIMITER ',' CSV HEADER;

INSERT INTO users (Username, Password, Role)
VALUES ('admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'admin');

COPY ratings (User_ID, ISBN, Book_Rating)
    FROM '/docker-entrypoint-initdb.d/ratings.csv'
    DELIMITER ',' CSV HEADER;

COPY inventory (ISBN, Quantity, Price)
    FROM '/docker-entrypoint-initdb.d/inventory.csv'
    DELIMITER ',' CSV HEADER;

-- Adjust the sequence for User_ID to avoid conflicts with already existing users
SELECT SETVAL('users_user_id_seq', (SELECT COALESCE(MAX(User_ID), 0) + 1 FROM users));
