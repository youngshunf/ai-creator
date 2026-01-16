-- 创流桌面端 SQLite Schema
-- 基于 docs/16-数据库设计与同步策略.md
-- @author Ysf

-- 用户表（仅当前用户）
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    uuid TEXT,
    email TEXT,
    phone TEXT,
    username TEXT,
    nickname TEXT,
    avatar TEXT,
    status INTEGER DEFAULT 1,
    is_superuser INTEGER DEFAULT 0,
    is_staff INTEGER DEFAULT 0,
    subscription_tier TEXT NOT NULL DEFAULT 'free',
    settings TEXT,
    synced_at INTEGER,
    server_version INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- 项目表
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    industry TEXT,
    sub_industries TEXT,
    brand_name TEXT,
    brand_tone TEXT,
    brand_keywords TEXT,
    topics TEXT,
    keywords TEXT,
    account_tags TEXT,
    preferred_platforms TEXT,
    content_style TEXT,
    settings TEXT,
    is_default INTEGER DEFAULT 0,
    is_deleted INTEGER DEFAULT 0,
    deleted_at INTEGER,
    synced_at INTEGER,
    server_version INTEGER DEFAULT 0,
    local_version INTEGER DEFAULT 0,
    sync_status TEXT DEFAULT 'synced',
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 平台账号表
CREATE TABLE IF NOT EXISTS platform_accounts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    account_id TEXT NOT NULL,
    account_name TEXT,
    avatar_url TEXT,
    is_active INTEGER DEFAULT 1,
    session_valid INTEGER DEFAULT 1,
    last_session_check INTEGER,
    followers_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    posts_count INTEGER DEFAULT 0,
    metadata TEXT,
    last_profile_sync_at INTEGER,
    is_deleted INTEGER DEFAULT 0,
    deleted_at INTEGER,
    synced_at INTEGER,
    server_version INTEGER DEFAULT 0,
    local_version INTEGER DEFAULT 0,
    sync_status TEXT DEFAULT 'synced',
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- 内容表
CREATE TABLE IF NOT EXISTS contents (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    title TEXT,
    content_type TEXT NOT NULL,
    status TEXT DEFAULT 'draft',
    text_content TEXT,
    summary TEXT,
    media_urls TEXT,
    cover_url TEXT,
    tags TEXT,
    keywords TEXT,
    word_count INTEGER DEFAULT 0,
    read_time_minutes INTEGER DEFAULT 0,
    ai_generated INTEGER DEFAULT 0,
    generation_params TEXT,
    version INTEGER DEFAULT 1,
    parent_id TEXT,
    is_deleted INTEGER DEFAULT 0,
    deleted_at INTEGER,
    synced_at INTEGER,
    server_version INTEGER DEFAULT 0,
    local_version INTEGER DEFAULT 0,
    sync_status TEXT DEFAULT 'synced',
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (parent_id) REFERENCES contents(id)
);

-- 发布任务表
CREATE TABLE IF NOT EXISTS publications (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    content_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    adapted_content TEXT,
    scheduled_at INTEGER,
    published_at INTEGER,
    platform_post_id TEXT,
    platform_post_url TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    last_retry_at INTEGER,
    synced_at INTEGER,
    server_version INTEGER DEFAULT 0,
    local_version INTEGER DEFAULT 0,
    sync_status TEXT DEFAULT 'synced',
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (content_id) REFERENCES contents(id),
    FOREIGN KEY (account_id) REFERENCES platform_accounts(id)
);

-- 同步元数据表
CREATE TABLE IF NOT EXISTS sync_metadata (
    table_name TEXT PRIMARY KEY,
    last_sync_at INTEGER,
    last_server_version INTEGER DEFAULT 0,
    sync_cursor TEXT,
    sync_direction TEXT DEFAULT 'bidirectional'
);

-- 冲突记录表
CREATE TABLE IF NOT EXISTS sync_conflicts (
    id TEXT PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    local_data TEXT NOT NULL,
    server_data TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    resolved_at INTEGER,
    resolution TEXT,
    created_at INTEGER NOT NULL
);

-- 待同步队列表
CREATE TABLE IF NOT EXISTS sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    data TEXT NOT NULL,
    local_version INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at INTEGER NOT NULL
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_platform_accounts_user_id ON platform_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_platform_accounts_project_id ON platform_accounts(project_id);
-- 确保同一项目下的同一平台账号唯一
CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_accounts_unique ON platform_accounts(project_id, platform, account_id);
CREATE INDEX IF NOT EXISTS idx_contents_user_id ON contents(user_id);
CREATE INDEX IF NOT EXISTS idx_contents_project_id ON contents(project_id);
CREATE INDEX IF NOT EXISTS idx_publications_user_id ON publications(user_id);
CREATE INDEX IF NOT EXISTS idx_publications_content_id ON publications(content_id);
CREATE INDEX IF NOT EXISTS idx_sync_queue_status ON sync_queue(status);
CREATE INDEX IF NOT EXISTS idx_sync_queue_table ON sync_queue(table_name, status);
CREATE INDEX IF NOT EXISTS idx_sync_conflicts_status ON sync_conflicts(status);
