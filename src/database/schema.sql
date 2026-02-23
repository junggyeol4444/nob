-- NovelWriter Local 데이터베이스 스키마

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    genre TEXT,
    description TEXT,
    tone TEXT,
    viewpoint TEXT DEFAULT '3인칭',
    plot TEXT,
    plot_source TEXT DEFAULT 'user',
    total_chapters INTEGER DEFAULT 100,
    chapter_length INTEGER DEFAULT 2000,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS outlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    chapter_num INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    source TEXT DEFAULT 'user',
    order_index INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE(project_id, chapter_num)
);

CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    outline_id INTEGER,
    chapter_num INTEGER NOT NULL,
    title TEXT,
    content TEXT,
    summary TEXT,
    word_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'draft',
    generation_prompt TEXT,
    generation_time REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (outline_id) REFERENCES outlines(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    role TEXT,
    age INTEGER,
    gender TEXT,
    personality TEXT,
    appearance TEXT,
    background TEXT,
    abilities TEXT,
    relationships TEXT,
    character_arc TEXT,
    notes TEXT,
    source TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS worldbuilding (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    category TEXT,
    title TEXT,
    content TEXT,
    source TEXT DEFAULT 'user',
    tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS generation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER NOT NULL,
    version INTEGER,
    content TEXT,
    prompt TEXT,
    generation_params TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS generation_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    job_type TEXT NOT NULL,
    start_chapter INTEGER,
    end_chapter INTEGER,
    status TEXT DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    current_chapter INTEGER,
    total_chapters INTEGER,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
