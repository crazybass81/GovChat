-- GovChat 데이터베이스 스키마
-- 사용자 테이블
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 지원사업 프로젝트 테이블
CREATE TABLE projects (
    project_id SERIAL PRIMARY KEY,
    policy_external_id VARCHAR(255) UNIQUE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    agency VARCHAR(200),
    target_audience TEXT,
    support_content TEXT,
    application_period VARCHAR(200),
    application_method TEXT,
    required_documents TEXT,
    contact_info TEXT,
    reference_url TEXT,
    source VARCHAR(20) DEFAULT 'external' CHECK (source IN ('external', 'manual')),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 사용자 세션 테이블 (JWT 블랙리스트용)
CREATE TABLE user_sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 관리자 활동 로그 테이블
CREATE TABLE admin_logs (
    log_id SERIAL PRIMARY KEY,
    admin_id INTEGER REFERENCES users(user_id),
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50),
    target_id INTEGER,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_projects_title ON projects USING gin(to_tsvector('korean', title));
CREATE INDEX idx_projects_description ON projects USING gin(to_tsvector('korean', description));
CREATE INDEX idx_projects_agency ON projects(agency);
CREATE INDEX idx_projects_active ON projects(active);
CREATE INDEX idx_user_sessions_token ON user_sessions(token_hash);
CREATE INDEX idx_admin_logs_admin_id ON admin_logs(admin_id);

-- 기본 관리자 계정 생성 (비밀번호는 bcrypt 해시)
INSERT INTO users (email, password_hash, name, verified, role) 
VALUES ('archt723@gmail.com', '$2b$10$placeholder_hash', 'Admin', TRUE, 'admin');