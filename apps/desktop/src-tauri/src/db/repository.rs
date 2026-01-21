//! 数据库操作层
//! @author Ysf

use rusqlite::{params, Connection, Result as SqliteResult};
use std::path::Path;
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};

use super::models::*;

/// 获取当前时间戳
fn now() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs() as i64
}

/// 生成 UUID
fn gen_uuid() -> String {
    uuid::Uuid::new_v4().to_string()
}

/// 数据库仓库
#[derive(Clone)]
pub struct Repository {
    conn: Arc<Mutex<Connection>>,
}

impl Repository {
    /// 打开或创建数据库
    pub fn open<P: AsRef<Path>>(path: P) -> SqliteResult<Self> {
        let conn = Connection::open(path)?;
        conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")?;
        Ok(Self {
            conn: Arc::new(Mutex::new(conn)),
        })
    }

    /// 初始化数据库 Schema
    pub fn init_schema(&self) -> SqliteResult<()> {
        let schema = include_str!("schema.sql");
        {
            let conn = self.conn.lock().unwrap();
            conn.execute_batch(schema)?;
            
            // 尝试添加 cloud_id 列 (如果不存在)
            // 这是一个简单的迁移策略，适用于开发阶段
            let _ = conn.execute("ALTER TABLE projects ADD COLUMN cloud_id INTEGER", []);
        }
        // 移除了 run_migrations，开发阶段直接修改 schema.sql
        self.ensure_default_user()?;
        Ok(())
    }

    /// 确保默认用户存在
    fn ensure_default_user(&self) -> SqliteResult<()> {
        let ts = now();
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT OR IGNORE INTO users (id, email, username, nickname, subscription_tier, created_at, updated_at, status)
             VALUES ('current-user', 'local@localhost', 'local', '本地用户', 'free', ?1, ?1, 1)",
            params![ts],
        )?;
        Ok(())
    }

    /// 确保用户存在（用于满足外键约束的兜底方法）
    pub fn ensure_user_exists(&self, user_id: &str) -> SqliteResult<()> {
        let ts = now();
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT OR IGNORE INTO users (id, email, username, nickname, subscription_tier, created_at, updated_at, status)
             VALUES (?1, 'waiting_sync@local', 'pending_' || ?1, '同步中...', 'free', ?2, ?2, 1)",
            params![user_id, ts],
        )?;
        Ok(())
    }

    /// 确保项目存在（用于外键约束）
    pub fn ensure_project_exists(&self, project_id: &str, user_id: &str) -> SqliteResult<()> {
        // 先确保用户存在
        self.ensure_user_exists(user_id)?;
        
        let ts = now();
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT OR IGNORE INTO projects (id, user_id, name, sync_status, created_at, updated_at)
             VALUES (?1, ?2, '默认项目', 'pending', ?3, ?3)",
            params![project_id, user_id, ts],
        )?;
        Ok(())
    }

    /// 同步云端用户到本地（登录时调用）
    pub fn sync_user(&self, user_id: &str, email: Option<&str>, username: Option<&str>, nickname: Option<&str>, avatar: Option<&str>) -> SqliteResult<()> {
        let ts = now();
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO users (id, email, username, nickname, avatar, subscription_tier, created_at, updated_at, status)
             VALUES (?1, ?2, ?3, ?4, ?5, 'free', ?6, ?6, 1)
             ON CONFLICT(id) DO UPDATE SET
                email=COALESCE(excluded.email, email),
                username=COALESCE(excluded.username, username),
                nickname=COALESCE(excluded.nickname, nickname),
                avatar=COALESCE(excluded.avatar, avatar),
                updated_at=excluded.updated_at",
            params![user_id, email, username, nickname, avatar, ts],
        )?;
        Ok(())
    }

    /// 同步云端项目到本地（选择项目时调用）
    pub fn sync_project(&self, project_id: &str, user_id: &str, name: &str, description: Option<&str>, cloud_id: Option<i64>) -> SqliteResult<()> {
        let ts = now();
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO projects (id, user_id, name, description, sync_status, created_at, updated_at, cloud_id)
             VALUES (?1, ?2, ?3, ?4, 'synced', ?5, ?5, ?6)
             ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                description=COALESCE(excluded.description, description),
                sync_status='synced',
                updated_at=excluded.updated_at,
                cloud_id=COALESCE(excluded.cloud_id, cloud_id)",
            params![project_id, user_id, name, description, ts, cloud_id],
        )?;
        Ok(())
    }

    /// 通过 Cloud ID 获取项目 UUID
    pub fn get_project_uuid_by_cloud_id(&self, cloud_id: i64) -> SqliteResult<Option<String>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare("SELECT id FROM projects WHERE cloud_id = ?1 LIMIT 1")?;
        let mut rows = stmt.query(params![cloud_id])?;
        if let Some(row) = rows.next()? {
            Ok(Some(row.get(0)?))
        } else {
            Ok(None)
        }
    }

    // ============ 用户操作 ============

    /// 保存用户（upsert）
    pub fn save_user(&self, user: &User) -> SqliteResult<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO users (id, uuid, email, phone, username, nickname, avatar, status, is_superuser, is_staff, subscription_tier, settings, synced_at, server_version, created_at, updated_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?15, ?16)
             ON CONFLICT(id) DO UPDATE SET
                uuid=excluded.uuid, email=excluded.email, phone=excluded.phone,
                username=excluded.username, nickname=excluded.nickname, avatar=excluded.avatar,
                status=excluded.status, is_superuser=excluded.is_superuser, is_staff=excluded.is_staff,
                subscription_tier=excluded.subscription_tier, settings=excluded.settings,
                synced_at=excluded.synced_at, server_version=excluded.server_version,
                updated_at=excluded.updated_at",
            params![
                user.id, user.uuid, user.email, user.phone, user.username, user.nickname, user.avatar,
                user.status, user.is_superuser, user.is_staff, user.subscription_tier, user.settings,
                user.synced_at, user.server_version, user.created_at, user.updated_at
            ],
        )?;
        Ok(())
    }

    /// 获取当前用户
    pub fn get_user(&self) -> SqliteResult<Option<User>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare("SELECT * FROM users LIMIT 1")?;
        let mut rows = stmt.query([])?;
        if let Some(row) = rows.next()? {
            Ok(Some(self.row_to_user(row)?))
        } else {
            Ok(None)
        }
    }
    
    fn row_to_user(&self, row: &rusqlite::Row) -> SqliteResult<User> {
        Ok(User {
            id: row.get("id")?,
            uuid: row.get("uuid").unwrap_or(None),
            email: row.get("email")?,
            phone: row.get("phone").unwrap_or(None),
            username: row.get("username")?,
            nickname: row.get("nickname")?,
            avatar: row.get("avatar").or_else(|_| row.get("avatar_url")).unwrap_or(None),
            status: row.get("status").unwrap_or(1),
            is_superuser: row.get("is_superuser").unwrap_or(false),
            is_staff: row.get("is_staff").unwrap_or(false),
            subscription_tier: row.get("subscription_tier")?,
            settings: row.get("settings")?,
            synced_at: row.get("synced_at")?,
            server_version: row.get("server_version")?,
            created_at: row.get("created_at")?,
            updated_at: row.get("updated_at")?,
        })
    }

    // ============ 项目操作 ============

    /// 创建项目
    pub fn create_project(&self, user_id: &str, data: &CreateProject) -> SqliteResult<Project> {
        let id = gen_uuid();
        let now = now();
        let sub_industries = data.sub_industries.as_ref().map(|v| serde_json::to_string(v).unwrap());
        let brand_keywords = data.brand_keywords.as_ref().map(|v| serde_json::to_string(v).unwrap());
        let topics = data.topics.as_ref().map(|v| serde_json::to_string(v).unwrap());
        let keywords = data.keywords.as_ref().map(|v| serde_json::to_string(v).unwrap());

        {
            let conn = self.conn.lock().unwrap();
            conn.execute(
                "INSERT INTO projects (id, user_id, name, description, industry, sub_industries, brand_name, brand_tone, brand_keywords, topics, keywords, sync_status, created_at, updated_at)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, 'pending', ?12, ?13)",
                params![
                    id, user_id, data.name, data.description, data.industry, sub_industries,
                    data.brand_name, data.brand_tone, brand_keywords, topics, keywords, now, now
                ],
            )?;
        }

        self.get_project(&id).map(|p| p.unwrap())
    }

    /// 更新项目
    pub fn update_project(&self, id: &str, data: &UpdateProject) -> SqliteResult<()> {
        let now = now();
        
        let sub_industries = data.sub_industries.as_ref().map(|v| serde_json::to_string(v).unwrap());
        let brand_keywords = data.brand_keywords.as_ref().map(|v| serde_json::to_string(v).unwrap());
        let topics = data.topics.as_ref().map(|v| serde_json::to_string(v).unwrap());
        let keywords = data.keywords.as_ref().map(|v| serde_json::to_string(v).unwrap());
        let account_tags = data.account_tags.as_ref().map(|v| serde_json::to_string(v).unwrap());
        let preferred_platforms = data.preferred_platforms.as_ref().map(|v| serde_json::to_string(v).unwrap());

        let conn = self.conn.lock().unwrap();
        conn.execute(
            "UPDATE projects SET 
                name = COALESCE(?1, name),
                description = COALESCE(?2, description),
                industry = COALESCE(?3, industry),
                sub_industries = COALESCE(?4, sub_industries),
                brand_name = COALESCE(?5, brand_name),
                brand_tone = COALESCE(?6, brand_tone),
                brand_keywords = COALESCE(?7, brand_keywords),
                topics = COALESCE(?8, topics),
                keywords = COALESCE(?9, keywords),
                account_tags = COALESCE(?10, account_tags),
                preferred_platforms = COALESCE(?11, preferred_platforms),
                content_style = COALESCE(?12, content_style),
                sync_status = 'pending',
                local_version = local_version + 1,
                updated_at = ?13
             WHERE id = ?14",
            params![
                data.name, data.description, data.industry, sub_industries,
                data.brand_name, data.brand_tone, brand_keywords, topics, keywords,
                account_tags, preferred_platforms, data.content_style, now, id
            ],
        )?;
        Ok(())
    }

    /// 获取项目
    pub fn get_project(&self, id: &str) -> SqliteResult<Option<Project>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare("SELECT * FROM projects WHERE id = ?1 AND is_deleted = 0")?;
        let mut rows = stmt.query(params![id])?;
        if let Some(row) = rows.next()? {
            Ok(Some(self.row_to_project(row)?))
        } else {
            Ok(None)
        }
    }

    /// 获取用户所有项目
    pub fn list_projects(&self, user_id: &str) -> SqliteResult<Vec<Project>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT * FROM projects WHERE user_id = ?1 AND is_deleted = 0 ORDER BY is_default DESC, updated_at DESC"
        )?;
        let mut rows = stmt.query(params![user_id])?;
        let mut projects = Vec::new();
        while let Some(row) = rows.next()? {
            projects.push(self.row_to_project(row)?);
        }
        Ok(projects)
    }

    /// 设置用户的默认项目（保证同一用户仅有一个默认项目）
    pub fn set_default_project(&self, user_id: &str, project_id: &str) -> SqliteResult<()> {
        let now = now();
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "UPDATE projects
             SET is_default = CASE WHEN id = ?1 THEN 1 ELSE 0 END,
                 sync_status = 'pending',
                 local_version = local_version + 1,
                 updated_at = ?2
             WHERE user_id = ?3 AND is_deleted = 0",
            params![project_id, now, user_id],
        )?;
        Ok(())
    }

    /// 删除项目（软删除）
    pub fn delete_project(&self, id: &str) -> SqliteResult<()> {
        let now = now();
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "UPDATE projects SET is_deleted = 1, deleted_at = ?1, sync_status = 'pending', local_version = local_version + 1, updated_at = ?1 WHERE id = ?2",
            params![now, id],
        )?;
        Ok(())
    }

    fn row_to_project(&self, row: &rusqlite::Row) -> SqliteResult<Project> {
        Ok(Project {
            id: row.get(0)?,
            user_id: row.get(1)?,
            name: row.get(2)?,
            description: row.get(3)?,
            industry: row.get(4)?,
            sub_industries: row.get(5)?,
            brand_name: row.get(6)?,
            brand_tone: row.get(7)?,
            brand_keywords: row.get(8)?,
            topics: row.get(9)?,
            keywords: row.get(10)?,
            account_tags: row.get(11)?,
            preferred_platforms: row.get(12)?,
            content_style: row.get(13)?,
            settings: row.get(14)?,
            is_default: row.get::<_, i32>(15)? != 0,
            is_deleted: row.get::<_, i32>(16)? != 0,
            deleted_at: row.get(17)?,
            synced_at: row.get(18)?,
            server_version: row.get(19)?,
            local_version: row.get(20)?,
            sync_status: row.get(21)?,
            created_at: row.get(22)?,
            updated_at: row.get(23)?,
        })
    }

    // ============ 内容操作 ============

    /// 创建内容
    pub fn create_content(&self, user_id: &str, data: &CreateContent) -> SqliteResult<Content> {
        let id = gen_uuid();
        let now = now();
        let tags = data.tags.as_ref().map(|v| serde_json::to_string(v).unwrap());
        let word_count = data.text_content.as_ref().map(|t| t.chars().count() as i64).unwrap_or(0);

        {
            let conn = self.conn.lock().unwrap();
            conn.execute(
                "INSERT INTO contents (id, user_id, project_id, title, content_type, text_content, tags, word_count, sync_status, created_at, updated_at)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, 'pending', ?9, ?10)",
                params![id, user_id, data.project_id, data.title, data.content_type, data.text_content, tags, word_count, now, now],
            )?;
        }

        self.get_content(&id).map(|c| c.unwrap())
    }

    /// 获取内容
    pub fn get_content(&self, id: &str) -> SqliteResult<Option<Content>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare("SELECT * FROM contents WHERE id = ?1 AND is_deleted = 0")?;
        let mut rows = stmt.query(params![id])?;
        if let Some(row) = rows.next()? {
            Ok(Some(self.row_to_content(row)?))
        } else {
            Ok(None)
        }
    }

    /// 获取项目内容列表
    pub fn list_contents(&self, project_id: &str) -> SqliteResult<Vec<Content>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT * FROM contents WHERE project_id = ?1 AND is_deleted = 0 ORDER BY updated_at DESC"
        )?;
        let mut rows = stmt.query(params![project_id])?;
        let mut contents = Vec::new();
        while let Some(row) = rows.next()? {
            contents.push(self.row_to_content(row)?);
        }
        Ok(contents)
    }

    /// 更新内容
    pub fn update_content(&self, id: &str, title: Option<&str>, text_content: Option<&str>) -> SqliteResult<()> {
        let now = now();
        let word_count = text_content.map(|t| t.chars().count() as i64);
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "UPDATE contents SET title = COALESCE(?1, title), text_content = COALESCE(?2, text_content),
             word_count = COALESCE(?3, word_count), sync_status = 'pending', local_version = local_version + 1, updated_at = ?4 WHERE id = ?5",
            params![title, text_content, word_count, now, id],
        )?;
        Ok(())
    }

    /// 删除内容（软删除）
    pub fn delete_content(&self, id: &str) -> SqliteResult<()> {
        let now = now();
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "UPDATE contents SET is_deleted = 1, deleted_at = ?1, sync_status = 'pending', local_version = local_version + 1, updated_at = ?1 WHERE id = ?2",
            params![now, id],
        )?;
        Ok(())
    }

    fn row_to_content(&self, row: &rusqlite::Row) -> SqliteResult<Content> {
        Ok(Content {
            id: row.get(0)?,
            user_id: row.get(1)?,
            project_id: row.get(2)?,
            title: row.get(3)?,
            content_type: row.get(4)?,
            status: row.get(5)?,
            text_content: row.get(6)?,
            summary: row.get(7)?,
            media_urls: row.get(8)?,
            cover_url: row.get(9)?,
            tags: row.get(10)?,
            keywords: row.get(11)?,
            word_count: row.get(12)?,
            read_time_minutes: row.get(13)?,
            ai_generated: row.get::<_, i32>(14)? != 0,
            generation_params: row.get(15)?,
            version: row.get(16)?,
            parent_id: row.get(17)?,
            is_deleted: row.get::<_, i32>(18)? != 0,
            deleted_at: row.get(19)?,
            synced_at: row.get(20)?,
            server_version: row.get(21)?,
            local_version: row.get(22)?,
            sync_status: row.get(23)?,
            created_at: row.get(24)?,
            updated_at: row.get(25)?,
        })
    }

    // ============ 平台账号操作 ============

    /// 创建平台账号
    pub fn create_platform_account(&self, user_id: &str, project_id: &str, platform: &str, account_id: &str, account_name: Option<&str>) -> SqliteResult<PlatformAccount> {
        let id = gen_uuid();
        let now = now();
        
        let actual_id: String;
        {
            let conn = self.conn.lock().unwrap();
            actual_id = conn.query_row(
                "INSERT INTO platform_accounts (id, user_id, project_id, platform, account_id, account_name, sync_status, created_at, updated_at)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, 'pending', ?7, ?8)
                 ON CONFLICT(project_id, platform, account_id) DO UPDATE SET
                    account_name = COALESCE(excluded.account_name, account_name),
                    sync_status = 'pending',
                    updated_at = excluded.updated_at
                 RETURNING id",
                params![id, user_id, project_id, platform, account_id, account_name, now, now],
                |row| row.get(0),
            )?;
        }

        self.get_platform_account(&actual_id).map(|a| a.unwrap())
    }

    /// 获取平台账号
    pub fn get_platform_account(&self, id: &str) -> SqliteResult<Option<PlatformAccount>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare("SELECT * FROM platform_accounts WHERE id = ?1 AND is_deleted = 0")?;
        let mut rows = stmt.query(params![id])?;
        if let Some(row) = rows.next()? {
            Ok(Some(self.row_to_platform_account(row)?))
        } else {
            Ok(None)
        }
    }

    /// 获取项目平台账号列表
    pub fn list_platform_accounts(&self, project_id: &str) -> SqliteResult<Vec<PlatformAccount>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT * FROM platform_accounts WHERE project_id = ?1 AND is_deleted = 0 ORDER BY created_at DESC"
        )?;
        let mut rows = stmt.query(params![project_id])?;
        let mut accounts = Vec::new();
        while let Some(row) = rows.next()? {
            accounts.push(self.row_to_platform_account(row)?);
        }
        Ok(accounts)
    }

    fn row_to_platform_account(&self, row: &rusqlite::Row) -> SqliteResult<PlatformAccount> {
        Ok(PlatformAccount {
            id: row.get("id")?,
            user_id: row.get("user_id")?,
            project_id: row.get("project_id")?,
            platform: row.get("platform")?,
            account_id: row.get("account_id")?,
            account_name: row.get("account_name")?,
            avatar_url: row.get("avatar_url")?,
            is_active: row.get::<_, i32>("is_active")? != 0,
            session_valid: row.get::<_, i32>("session_valid")? != 0,
            last_session_check: row.get("last_session_check")?,
            followers_count: row.get("followers_count")?,
            following_count: row.get("following_count")?,
            posts_count: row.get("posts_count")?,
            metadata: row.get("metadata")?,
            last_profile_sync_at: row.get("last_profile_sync_at").unwrap_or(None),
            is_deleted: row.get::<_, i32>("is_deleted")? != 0,
            deleted_at: row.get("deleted_at")?,
            synced_at: row.get("synced_at")?,
            server_version: row.get("server_version")?,
            local_version: row.get("local_version")?,
            sync_status: row.get("sync_status")?,
            created_at: row.get("created_at")?,
            updated_at: row.get("updated_at")?,
        })
    }

    /// 更新平台账号资料（同步后调用）
    pub fn update_platform_account_profile(
        &self,
        id: &str,
        account_name: Option<&str>,
        avatar_url: Option<&str>,
        followers_count: i64,
        following_count: i64,
        posts_count: i64,
        metadata: Option<&str>,
    ) -> SqliteResult<()> {
        let now = now();
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "UPDATE platform_accounts SET
                 account_name = ?1,
                 avatar_url = ?2,
                 followers_count = ?3,
                 following_count = ?4,
                 posts_count = ?5,
                 metadata = ?6,
                 last_profile_sync_at = ?7,
                 updated_at = ?8
             WHERE id = ?9",
            params![
                account_name,
                avatar_url,
                followers_count,
                following_count,
                posts_count,
                metadata,
                now,
                now,
                id
            ],
        )?;
        Ok(())
    }

    /// 删除平台账号
    pub fn delete_platform_account(&self, id: &str) -> SqliteResult<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute("DELETE FROM platform_accounts WHERE id = ?1", params![id])?;
        Ok(())
    }

    // ============ 发布任务操作 ============

    /// 创建发布任务
    pub fn create_publication(&self, user_id: &str, data: &CreatePublication) -> SqliteResult<Publication> {
        let id = gen_uuid();
        let now = now();
        {
            let conn = self.conn.lock().unwrap();
            conn.execute(
                "INSERT INTO publications (id, user_id, content_id, account_id, platform, scheduled_at, sync_status, created_at, updated_at)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, 'pending', ?7, ?8)",
                params![id, user_id, data.content_id, data.account_id, data.platform, data.scheduled_at, now, now],
            )?;
        }
        self.get_publication(&id).map(|p| p.unwrap())
    }

    /// 获取发布任务
    pub fn get_publication(&self, id: &str) -> SqliteResult<Option<Publication>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare("SELECT * FROM publications WHERE id = ?1")?;
        let mut rows = stmt.query(params![id])?;
        if let Some(row) = rows.next()? {
            Ok(Some(self.row_to_publication(row)?))
        } else {
            Ok(None)
        }
    }

    /// 获取内容的发布任务列表
    pub fn list_publications(&self, content_id: &str) -> SqliteResult<Vec<Publication>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT * FROM publications WHERE content_id = ?1 ORDER BY created_at DESC"
        )?;
        let mut rows = stmt.query(params![content_id])?;
        let mut publications = Vec::new();
        while let Some(row) = rows.next()? {
            publications.push(self.row_to_publication(row)?);
        }
        Ok(publications)
    }

    /// 更新发布状态
    pub fn update_publication_status(&self, id: &str, status: &str, error_message: Option<&str>) -> SqliteResult<()> {
        let now = now();
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "UPDATE publications SET status = ?1, error_message = ?2, sync_status = 'pending', local_version = local_version + 1, updated_at = ?3 WHERE id = ?4",
            params![status, error_message, now, id],
        )?;
        Ok(())
    }

    fn row_to_publication(&self, row: &rusqlite::Row) -> SqliteResult<Publication> {
        Ok(Publication {
            id: row.get(0)?,
            user_id: row.get(1)?,
            content_id: row.get(2)?,
            account_id: row.get(3)?,
            platform: row.get(4)?,
            status: row.get(5)?,
            adapted_content: row.get(6)?,
            scheduled_at: row.get(7)?,
            published_at: row.get(8)?,
            platform_post_id: row.get(9)?,
            platform_post_url: row.get(10)?,
            error_message: row.get(11)?,
            retry_count: row.get(12)?,
            last_retry_at: row.get(13)?,
            synced_at: row.get(14)?,
            server_version: row.get(15)?,
            local_version: row.get(16)?,
            sync_status: row.get(17)?,
            created_at: row.get(18)?,
            updated_at: row.get(19)?,
        })
    }
}
