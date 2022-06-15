CREATE DATABASE IF NOT EXISTS Music;
USE Music;

CREATE TABLE IF NOT EXISTS Album (
    id VARCHAR(22) NOT NULL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    image_url VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS Artist (
    id VARCHAR(22) NOT NULL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS Song (
    id VARCHAR(22) NOT NULL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    id_album VARCHAR(255) NOT NULL,
    date_played DATE NOT NULL,
    cnt_played SMALLINT NOT NULL,
    FOREIGN KEY (id_album) REFERENCES Album(id)
);

CREATE TABLE IF NOT EXISTS AlbumArtists (
    id_album VARCHAR(22) NOT NULL,
    id_artist VARCHAR(22) NOT NULL,
    FOREIGN KEY (id_album) REFERENCES Album(id),
    FOREIGN KEY (id_artist) REFERENCES Artist(id)
);

CREATE TABLE IF NOT EXISTS SongArtists (
    id_song VARCHAR(22) NOT NULL,
    id_artist VARCHAR(22) NOT NULL,
    FOREIGN KEY (id_song) REFERENCES Song(id),
    FOREIGN KEY (id_artist) REFERENCES Artist(id)
);
