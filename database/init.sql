CREATE DATABASE Music [IF NOT EXISTS];
CREATE TABLE [IF NOT EXISTS] Artists (
    artist_group_id varchar(255) NOT NULL,
    artist_ids varchar(255) NOT NULL,
    artist_names varchar(255) NOT NULL,
    PRIMARY KEY (artist_group_id)
)

CREATE TABLE [IF NOT EXISTS] Playlist (
    playlist_id = varchar(255) NOT NULL,
    playlist_name varchar(255) NOT NULL,
    PRIMARY KEY (playlist_id)
)

CREATE TABLE [IF NOT EXISTS] Song (
    song_id varchar(255) NOT NULL,
    song_name varchar(255) NOT NULL,
    song_playlist = varchar(255),
    song_artists = varchar(255),
    FOREIGN KEY (song_playlist) REFERENCES Playlist(playlist_id),
    FOREIGN KEY (song_artists) REFERENCES Artists(artist_ids)
    PRIMARY KEY (ID)
)