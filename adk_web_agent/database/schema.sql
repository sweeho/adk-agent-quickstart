-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,          -- Email address
    password_hash TEXT NOT NULL,       -- bcrypt hashed password
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE
);

-- Sessions table (integrates with Google ADK Session Object)
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,       -- Google ADK session ID
    user_id TEXT NOT NULL,             -- Owner of this session
    session_name TEXT,                 -- User-defined or auto-generated name
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    last_message_preview TEXT,
    agent_count INTEGER DEFAULT 0,     -- Number of agents invoked
    session_data TEXT,                 -- JSON: Google ADK session metadata
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Critical index for session isolation
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id, updated_at DESC);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,                -- 'user' or 'assistant'
    content TEXT NOT NULL,
    thought_summary TEXT,              -- Gemini thought summary (if available)
    delegated_agent TEXT,              -- Which agent produced this response
    delegation_chain TEXT,             -- JSON array of delegation path
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent_execution_id TEXT,           -- Link to agent execution
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id, timestamp DESC);

-- Agent executions table
CREATE TABLE IF NOT EXISTS agent_executions (
    execution_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    main_agent_data TEXT,              -- JSON: main agent execution details
    sub_agents_data TEXT,              -- JSON: array of sub-agent executions
    thought_summary TEXT,              -- Gemini thought summary
    delegated_agent TEXT,              -- Final agent that handled work
    delegation_chain TEXT,             -- JSON array of delegation path
    thinking_tokens INTEGER,           -- Thinking tokens consumed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    status TEXT,                       -- 'pending', 'running', 'completed', 'failed'
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES messages(message_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_executions_session ON agent_executions(session_id);
CREATE INDEX IF NOT EXISTS idx_executions_user ON agent_executions(user_id);
