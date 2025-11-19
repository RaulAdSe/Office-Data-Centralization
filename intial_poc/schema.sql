CREATE TABLE elementos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL,
    grosor REAL,
    material TEXT,
    resistencia TEXT,
    descripcion TEXT
);

CREATE TABLE proyectos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    codigo TEXT UNIQUE NOT NULL,
    ubicacion TEXT,
    fecha_inicio TEXT
);

CREATE TABLE proyecto_elementos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proyecto_id INTEGER NOT NULL,
    elemento_id INTEGER NOT NULL,
    cantidad REAL,
    notas TEXT,
    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id),
    FOREIGN KEY (elemento_id) REFERENCES elementos(id),
    UNIQUE(proyecto_id, elemento_id)
);