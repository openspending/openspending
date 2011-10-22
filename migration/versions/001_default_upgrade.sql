CREATE TABLE account (
	id INTEGER NOT NULL, 
	name VARCHAR(255), 
	fullname VARCHAR(2000), 
	email VARCHAR(2000), 
	password VARCHAR(2000), 
	api_key VARCHAR(2000), 
	admin BOOLEAN, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	CHECK (admin IN (0, 1))
);
CREATE TABLE dataset (
	id INTEGER NOT NULL, 
	name VARCHAR(255), 
	label VARCHAR(2000), 
	description VARCHAR, 
	currency VARCHAR, 
	default_time VARCHAR, 
	data TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);