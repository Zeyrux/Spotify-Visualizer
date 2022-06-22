export class Artist {
    constructor (artist) {
        this.id = artist["id"];
        this.name = artist["name"];
    }
}


export class Track {
    constructor (track) {
        this.id = track["id"];
        this.name = track["name"];
        this.artists = []
        track["artists"].forEach(artist => {
            this.artists.push(new Artist(artist));
        });
        this.duration_ms = track["duration_ms"];
    }
}


export class Album {
    constructor (album) {
        this.id = album["id"];
        this.name = album["name"];
        this.tracks = [];
        album["tracks"].forEach(track => {
            this.tracks.push(new Track(track));
        });
        this.image_url = album["image_url"];
        this.artists = [];
        album["artists"].forEach(artist => {
            this.artists.push(new Artist(artist));
        });
    }
}


export class Playlist {
    constructor (playlist) {
        this.id = playlist["id"];
        this.name = playlist["name"];
        this.tracks = [];
        playlist["tracks"].forEach(track => {
            this.tracks.push(new Track(track));
        });
    }
}
