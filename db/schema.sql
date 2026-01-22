-- Schema for Jira QA Automation System MVP
-- Automations are logged for auditability and rollback safety.

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS automation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jira_key TEXT NOT NULL UNIQUE,
    jira_summary TEXT,
    status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'review_pending')),
    branch_name TEXT,
    pr_url TEXT,
    files_changed INTEGER,
    lines_added INTEGER,
    lines_deleted INTEGER,
    claude_output TEXT,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_at DATETIME,
    review_result TEXT CHECK (review_result IN ('approved', 'rejected', 'closed'))
);

CREATE INDEX IF NOT EXISTS idx_jira_key ON automation_logs(jira_key);
CREATE INDEX IF NOT EXISTS idx_status ON automation_logs(status);
CREATE INDEX IF NOT EXISTS idx_created_at ON automation_logs(created_at);

-- Weekly Report Automation Logs
CREATE TABLE IF NOT EXISTS weekly_report_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agit_post_id TEXT NOT NULL,
    report_content TEXT,
    jira_completed_count INTEGER,
    jira_in_progress_count INTEGER,
    status TEXT NOT NULL CHECK (status IN ('success', 'failed')),
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_weekly_agit_post_id ON weekly_report_logs(agit_post_id);
CREATE INDEX IF NOT EXISTS idx_weekly_created_at ON weekly_report_logs(created_at);

-- Nightly Task Automation
CREATE TABLE IF NOT EXISTS nightly_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    token_reset_time TEXT NOT NULL DEFAULT '19:00',
    night_window_start TEXT NOT NULL DEFAULT '19:00',
    night_window_end TEXT NOT NULL DEFAULT '07:00',
    timezone TEXT NOT NULL DEFAULT 'Asia/Seoul',
    max_tasks_per_slot INTEGER NOT NULL DEFAULT 1,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nightly_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'done', 'failed', 'paused')),
    prompt TEXT NOT NULL,
    target_repo TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nightly_task_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'skipped')),
    slot_key TEXT NOT NULL,
    pr_url TEXT,
    report_url TEXT,
    report_text TEXT,
    error_message TEXT,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME,
    FOREIGN KEY (task_id) REFERENCES nightly_tasks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_nightly_tasks_status ON nightly_tasks(status);
CREATE INDEX IF NOT EXISTS idx_nightly_tasks_priority ON nightly_tasks(priority);
CREATE INDEX IF NOT EXISTS idx_nightly_runs_task ON nightly_task_runs(task_id);
CREATE INDEX IF NOT EXISTS idx_nightly_runs_slot ON nightly_task_runs(slot_key);

-- Document Index for Obsidian Title Jump
CREATE TABLE IF NOT EXISTS document_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    title TEXT NOT NULL,
    aliases TEXT,
    category TEXT,
    tags TEXT,
    modified_at DATETIME NOT NULL,
    indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_doc_file_path ON document_index(file_path);
CREATE INDEX IF NOT EXISTS idx_doc_title ON document_index(title);
CREATE INDEX IF NOT EXISTS idx_doc_category ON document_index(category);
CREATE INDEX IF NOT EXISTS idx_doc_modified ON document_index(modified_at);

-- Full-Text Search for document titles and aliases
CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
    title,
    aliases,
    file_name,
    content='document_index',
    content_rowid='id',
    tokenize='porter unicode61'
);

-- Triggers to keep FTS in sync with document_index
CREATE TRIGGER IF NOT EXISTS document_fts_insert AFTER INSERT ON document_index BEGIN
    INSERT INTO document_fts(rowid, title, aliases, file_name)
    VALUES (new.id, new.title, new.aliases, new.file_name);
END;

CREATE TRIGGER IF NOT EXISTS document_fts_delete AFTER DELETE ON document_index BEGIN
    DELETE FROM document_fts WHERE rowid = old.id;
END;

CREATE TRIGGER IF NOT EXISTS document_fts_update AFTER UPDATE ON document_index BEGIN
    UPDATE document_fts SET title = new.title, aliases = new.aliases, file_name = new.file_name
    WHERE rowid = new.id;
END;

-- Recent Documents Tracking
CREATE TABLE IF NOT EXISTS recent_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    title TEXT NOT NULL,
    accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_recent_file_path ON recent_documents(file_path);
CREATE INDEX IF NOT EXISTS idx_recent_accessed ON recent_documents(accessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_recent_access_count ON recent_documents(access_count DESC);

-- Document Summarization System
CREATE TABLE IF NOT EXISTS document_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    one_line_summary TEXT NOT NULL,
    executive_summary TEXT NOT NULL,
    detailed_summary TEXT NOT NULL,
    suggested_tags TEXT,
    word_count INTEGER,
    char_count INTEGER,
    summarized_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_summary_file_path ON document_summaries(file_path);
CREATE INDEX IF NOT EXISTS idx_summary_summarized ON document_summaries(summarized_at DESC);

-- Batch Summarization Jobs
CREATE TABLE IF NOT EXISTS batch_summary_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_path TEXT NOT NULL,
    total_files INTEGER NOT NULL DEFAULT 0,
    processed_files INTEGER NOT NULL DEFAULT 0,
    failed_files INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    started_at DATETIME,
    finished_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_batch_jobs_status ON batch_summary_jobs(status);
CREATE INDEX IF NOT EXISTS idx_batch_jobs_created ON batch_summary_jobs(created_at DESC);

-- Summary Tags for Auto-tagging
CREATE TABLE IF NOT EXISTS summary_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    FOREIGN KEY (summary_id) REFERENCES document_summaries(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_summary_tags_summary ON summary_tags(summary_id);
CREATE INDEX IF NOT EXISTS idx_summary_tags_tag ON summary_tags(tag);

-- TIL (Today I Learned) Generation Logs
CREATE TABLE IF NOT EXISTS til_generation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generation_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'skipped')),
    notes_scanned INTEGER NOT NULL DEFAULT 0,
    learnings_extracted INTEGER NOT NULL DEFAULT 0,
    til_note_path TEXT,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_til_generation_date ON til_generation_logs(generation_date);
CREATE INDEX IF NOT EXISTS idx_til_status ON til_generation_logs(status);
CREATE INDEX IF NOT EXISTS idx_til_created ON til_generation_logs(created_at DESC);

-- Chat History for RAG Conversations
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL DEFAULT 'work',
    title TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    sources TEXT,
    token_count INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_session_updated ON chat_sessions(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_session_category ON chat_sessions(category);

-- Voice Notes System
CREATE TABLE IF NOT EXISTS voice_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_file TEXT NOT NULL,
    note_type TEXT NOT NULL CHECK (note_type IN ('idea', 'meeting', 'memo', 'journal')),
    note_file_path TEXT,
    transcription_chars INTEGER,
    status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'processing')),
    error_message TEXT,
    transcription_method TEXT CHECK (transcription_method IN ('local', 'api')),
    language TEXT DEFAULT 'ko',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_voice_notes_status ON voice_notes(status);
CREATE INDEX IF NOT EXISTS idx_voice_notes_type ON voice_notes(note_type);
CREATE INDEX IF NOT EXISTS idx_voice_notes_created ON voice_notes(created_at DESC);
