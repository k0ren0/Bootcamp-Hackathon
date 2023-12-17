SELECT * 
FROM users

SELECT * 
FROM events

cursor.execute("DROP TABLE IF EXISTS users CASCADE")

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    city VARCHAR(255),
    phone_number VARCHAR(50),
    role VARCHAR(10) NOT NULL,
    additional_role VARCHAR(10),
    password_hash VARCHAR(255) NOT NULL
);
