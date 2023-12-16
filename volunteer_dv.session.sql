SELECT * FROM users

-- Создание базы данных
CREATE DATABASE volunteer_db;

-- Использование созданной базы данных
\c volunteer_db;

-- Создание таблицы пользователей
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(50) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    city VARCHAR(50),
    phone_number VARCHAR(15) -- Телефон в международном формате
);

-- Создание таблицы мероприятий
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    description TEXT,
    organizer_id INTEGER REFERENCES users(id) -- Связь с организатором мероприятия
);

-- Пример данных для таблицы пользователей
INSERT INTO users (username, password, first_name, last_name, city, phone_number)
VALUES 
    ('user1', 'password1', 'John', 'Doe', 'City1', '+123456789012'),
    ('user2', 'password2', 'Jane', 'Smith', 'City2', '+987654321098');

-- Пример данных для таблицы мероприятий
INSERT INTO events (name, date, description, organizer_id)
VALUES 
    ('Event 1', '2023-01-01', 'Description of Event 1', 1),
    ('Event 2', '2023-02-01', 'Description of Event 2', 2);
