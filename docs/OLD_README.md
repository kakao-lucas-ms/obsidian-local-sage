# Jira QA Automation System MVP

간단 이슈(Jira 라벨 `auto-fix`)를 자동으로 처리하여 Draft PR을 생성하는 로컬 자동화 도구입니다. n8n + PM2로 워크플로우를 구동하고, 스크립트는 로컬 Git 리포지토리에서 실행됩니다.

## Prerequisites

- macOS (zsh)
- Node.js 18+ / npm

## Install Tools (n8n, PM2)

```zsh
# Install globally
npm install -g n8n pm2

# Verify
n8n --version
pm2 --version
```

## Environment Variables

프로젝트 루트에 `.env` 파일을 준비하세요. 예시는 `.env.example` 참고.

```zsh
cp .env.example .env
# 편집기로 열어 실제 값 입력 (Jira/GitHub/Slack 토큰 등)
```

### Required Variables

| Variable | Description | Example |
|----------|-------------|----------|
| `JIRA_BASE_URL` | Jira 인스턴스 URL | `https://your-org.atlassian.net` |
| `JIRA_EMAIL` | Jira API 인증 이메일 | `you@example.com` |
| `JIRA_API_TOKEN` | Jira API token ([생성](https://id.atlassian.com/manage-profile/security/api-tokens)) | `ATATT3xFfGF0...` |
| `GITHUB_TOKEN` | GitHub Personal Access Token (repo 권한) | `ghp_xxxxxxxxxxxx` |
| `SLACK_BOT_TOKEN` | Slack Bot User OAuth Token | `xoxb-xxxxxxxxxx` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `TARGET_REPO_PATH` | 자동화 대상 리포지토리 경로 | Current directory |
| `DEFAULT_BRANCH` | 기본 브랜치명 | `main` |
| `N8N_BASE_URL` | n8n 접속 URL | `http://localhost:5678` |

**Security**: `.env` 파일은 절대 Git에 커밋하지 마세요 (`.gitignore`에 이미 포함됨)

## Start n8n with PM2

```zsh
# Run n8n in background
pm2 start n8n
pm2 save

# See processes
pm2 status

# Open n8n (default)
open http://localhost:5678
```

## Setup Workflow

### 1. Initialize Database

```zsh
sqlite3 db/automation.db < db/schema.sql
```

### 2. Import n8n Workflow

1. Open n8n: `http://localhost:5678`
2. Go to **Workflows** → **Import from File**
3. Select `workflows/auto-fix.json`
4. Update credentials:
   - **Jira API**: Replace `YOUR_JIRA_CREDENTIAL_ID` with your Jira credential
5. Update absolute paths in nodes:
   - `Generate Prompt`: `/absolute/path/to/scripts/prompt-template.js`
   - `SQLite Filter`: `/absolute/path/to/db/automation.db`
   - `Execute Command`: `/absolute/path/to/scripts/auto-fix.sh`
6. Set environment variable in n8n:
   - `TARGET_REPO_PATH`: path to your target repository
7. Activate workflow

### 3. Verify Setup

```zsh
# Check Claude CLI
./scripts/check-claude.sh

# Test database
sqlite3 db/automation.db "SELECT * FROM automation_logs;"

# Check workflow status in n8n UI
```

## Nightly Tasks (Batch Claude Work)

### 1. Start Task UI

```zsh
python3 scripts/nightly-task-ui.py
```

Open `http://127.0.0.1:8099` and configure:
- Token reset time (manual)
- Night window
- Max tasks per slot
- Create queued tasks with prompt and priority

### 2. Import n8n Workflow

1. Open n8n: `http://localhost:5678`
2. Go to **Workflows** → **Import from File**
3. Select `workflows/active/nightly-tasks.json`
4. Activate workflow

### 3. Optional Agit Report

Set these in `.env` if you want automatic Agit posts:
- `AGIT_WEBHOOK_URL`
- `AGIT_GROUP_ID`

## TIL Auto-Generator (New!)

Automatically generate daily TIL (Today I Learned) summaries from your Obsidian notes.

### Quick Setup

```zsh
# 1. Update database schema
sqlite3 db/automation.db < db/schema.sql

# 2. Set environment variables
export CLAUDE_API_KEY=your_anthropic_api_key
export OBSIDIAN_VAULT_PATH=~/Documents/Obsidian

# 3. Add TIL task to nightly queue
python3 scripts/add-til-task.py

# 4. Test manually
python3 scripts/til-generator.py --dry-run
```

### Features

- **Automatic Daily Execution**: Runs at midnight (Asia/Seoul timezone)
- **AI-Powered Analysis**: Uses Claude to extract key learnings
- **Obsidian Integration**: Auto-links to Daily Notes
- **Smart Detection**: Scans notes created/modified today
- **Comprehensive Logging**: Tracks all generations in database

### Documentation

See `workflows/active/README-TIL.md` for complete documentation including:
- Installation and configuration
- Manual and automated usage
- Troubleshooting guide
- Advanced customization

## Safety & Constraints

- 린트/타입체크 및 변경 범위 제한은 `scripts/auto-fix.sh`에서 자동 수행
- 최대 5 파일, 100 라인 변경 제한
- package.json, config, env 파일 수정 금지
- 실패 시 자동 롤백 및 DB 로깅

## Graph Analysis & Smart Linking

Analyze your Obsidian vault's link structure and get AI-powered link suggestions.

### Quick Start

```zsh
# Install dependencies
pip install -r requirements-graph.txt

# Run comprehensive analysis
./scripts/analyze-vault.sh

# Or run individual tools
./scripts/find-orphans.sh                    # Quick orphan detection
python3 scripts/graph-analyzer.py            # Full graph analysis
python3 scripts/suggest-links.py             # AI link suggestions
```

### Features

- **Hub Detection**: Find highly connected notes (knowledge hubs)
- **Orphan Detection**: Identify isolated notes with no connections
- **Community Detection**: Discover clusters of related notes
- **Smart Link Suggestions**: AI-powered recommendations using semantic similarity
- **PageRank Analysis**: Find the most important notes in your vault
- **Visualization Export**: D3.js, GraphML, DOT, and more

### Output

All reports are saved to `reports/`:
- `orphan_report_*.md` - Orphan and weak orphan lists
- `graph_analysis_*.json` - Complete graph metrics
- `link_suggestions_*.json` - AI-generated link recommendations
- `link_suggestions_*.md` - Human-readable suggestions
- `vault_analysis_summary_*.md` - Combined summary

See [docs/GRAPH_ANALYSIS.md](docs/GRAPH_ANALYSIS.md) for detailed documentation.

## Monitoring Dashboard

### Daily Status

```zsh
# View today's automation stats
./scripts/daily-status.sh

# View last 7 days
./scripts/daily-status.sh "7 day"
```

**Output includes**:
- Total runs, success/failed/review_pending counts
- Files and lines changed summary
- Recent 20 automation runs with PR URLs
- PM2 process status

### Query Logs Directly

```zsh
# All successful runs
sqlite3 db/automation.db "SELECT jira_key, pr_url, created_at FROM automation_logs WHERE status='success' ORDER BY created_at DESC LIMIT 10;"

# Failed runs with errors
sqlite3 db/automation.db "SELECT jira_key, error_message, created_at FROM automation_logs WHERE status='failed' ORDER BY created_at DESC;"
```
## Troubleshooting

### Lock File Stuck

```zsh
# Check lock age
ls -lh /tmp/claude-automation.lock

# Force remove (if stale > 10min)
rm -f /tmp/claude-automation.lock
```

### Script Fails on Lint/TypeCheck

- 대상 리포에 `npm run lint`, `npm run typecheck` 스크립트 존재 확인
- 없으면 `scripts/auto-fix.sh`에서 해당 단계 주석 처리 가능

### gh CLI Not Found

```zsh
# macOS에서 설치
brew install gh

# 인증
gh auth login
```

### n8n Workflow Not Triggering

1. n8n 워크플로 활성화 확인 (UI에서 토글)
2. PM2 프로세스 확인: `pm2 status`
3. n8n 로그 확인: `pm2 logs n8n`

### Database Locked Error

```zsh
# WAL 모드 확인
sqlite3 db/automation.db "PRAGMA journal_mode;"

# 필요시 재설정
sqlite3 db/automation.db "PRAGMA journal_mode=WAL;"
```

## Hybrid Search (NEW)

Advanced search combining **Vector Similarity** + **BM25 Keyword Search** for superior relevance.

### Quick Start

```bash
# Install dependency
pip3 install rank-bm25

# Build BM25 index
python3 scripts/hybrid-search.py rebuild-index work

# Try hybrid search
python3 scripts/hybrid-search.py search "독서클럽"
```

### Features

- **Vector Search**: Semantic understanding (BGE-M3 embeddings)
- **BM25 Search**: Exact keyword matching (Okapi BM25)
- **RRF Fusion**: Reciprocal Rank Fusion combines both rankings
- **Query Expansion**: Automatic synonym/alias expansion
- **BGE Reranking**: Cross-encoder for final refinement

### Usage Examples

```bash
# Basic hybrid search
python3 scripts/hybrid-search.py search "브런치 개발" work

# Faster: no reranking
python3 scripts/hybrid-search.py search "독서클럽" work --no-rerank

# Enhanced existing script with hybrid mode
python3 scripts/search-with-reranking.py "독서클럽" work --hybrid
```

### n8n Workflow

Enhanced workflow at `/obe-search-enhanced` endpoint:

```bash
curl -X POST http://localhost:5678/webhook/obe-search-enhanced \
  -H "Content-Type: application/json" \
  -d '{"query": "독서클럽", "category": "work"}'
```

### Documentation

- **Quick Start**: [docs/HYBRID_SEARCH_QUICKSTART.md](docs/HYBRID_SEARCH_QUICKSTART.md)
- **Full Architecture**: [docs/HYBRID_SEARCH.md](docs/HYBRID_SEARCH.md)

### Files

- `scripts/hybrid-search.py` - Standalone hybrid search
- `scripts/search-with-reranking.py` - Enhanced with `--hybrid` flag
- `scripts/ingest-with-bm25.py` - Ingestion with BM25 index building
- `workflows/active/obe-search-enhanced.json` - n8n workflow

## AI-Powered Document Summarization (NEW)

Automatically generate 3-level summaries and smart tag suggestions for your Obsidian documents.

### Quick Start

```bash
# 1. Update database schema
sqlite3 db/automation.db < db/schema.sql

# 2. Import n8n workflows
# - workflows/active/obe-summarize.json (single document)
# - workflows/active/obe-batch-summarize.json (batch processing)

# 3. Summarize a document
./scripts/obsidian-summarize.sh ~/Documents/Obsidian/Notes/project.md

# 4. Batch summarize a folder
./scripts/obsidian-batch-summarize.sh ~/Documents/Obsidian/Notes/Projects

# 5. Auto-tag suggestions
python3 scripts/auto-tag.py ~/Documents/Obsidian/Notes/project.md --apply
```

### Features

- **3-Level Summarization**:
  - One-line summary (≤100 chars)
  - Executive summary (3-5 sentences)
  - Detailed summary (structured, markdown)
- **Auto-Tag System**: AI-powered tag suggestions with confidence scores
- **Batch Processing**: Process entire folders efficiently
- **Korean Optimized**: Prompts optimized for Korean language output
- **Database Storage**: All summaries stored in SQLite for querying
- **Obsidian Integration**: Works with Shell Commands plugin

### Usage Examples

```bash
# Single document summarization
./scripts/obsidian-summarize.sh ~/Notes/meeting-notes.md -v

# Batch with custom pattern
./scripts/obsidian-batch-summarize.sh ~/Notes/Projects -p "tech-*.md" -m 50

# Tag suggestions (dry-run)
python3 scripts/auto-tag.py ~/Notes/project.md --dry-run

# Apply tags to file
python3 scripts/auto-tag.py ~/Notes/project.md --apply

# Query summaries
sqlite3 db/automation.db "SELECT file_name, one_line_summary FROM document_summaries ORDER BY summarized_at DESC LIMIT 10;"
```

### Documentation

- **Quick Start**: [scripts/SUMMARIZATION_QUICK_START.md](scripts/SUMMARIZATION_QUICK_START.md)
- **Full Guide**: [scripts/DOCUMENT_SUMMARIZATION.md](scripts/DOCUMENT_SUMMARIZATION.md)

### Files

- `workflows/active/obe-summarize.json` - Single document workflow
- `workflows/active/obe-batch-summarize.json` - Batch processing workflow
- `workflows/prompts/document-summarization-prompt.txt` - Summarization prompt
- `workflows/prompts/auto-tag-prompt.txt` - Auto-tag prompt
- `scripts/obsidian-summarize.sh` - Single document script
- `scripts/obsidian-batch-summarize.sh` - Batch processing script
- `scripts/auto-tag.py` - Auto-tagging system

## AI Chat Interface (NEW)

Chat with your Obsidian notes using conversational RAG. Maintains context, manages conversation history, and automatically cites sources.

### Quick Start

```bash
# 1. Update database schema (if not already done)
sqlite3 db/automation.db < db/schema.sql

# 2. Import n8n workflow
# Import workflows/active/obe-chat.json in n8n

# 3. Start interactive chat
./scripts/obsidian-chat.sh

# Or create specific session
./scripts/obsidian-chat.sh --new work
```

### Features

- **Conversational RAG**: Multi-turn conversations with context awareness
- **Session Management**: Multiple chat sessions with history
- **Smart Context Window**: Auto-trimming to manage token limits (12K tokens)
- **Source Citations**: Automatic [[note]] references in responses
- **Category Filtering**: Separate work/personal note searches
- **Korean Optimized**: Full Korean language support
- **Local LLM**: Uses Ollama (qwen2.5-coder:32b)

### Interactive Chat Commands

```
/help       - Show help
/clear      - Clear screen
/history    - Show session history
/new        - Create new session
/sessions   - List all sessions
/quit       - Exit chat
```

### Usage Examples

```bash
# Interactive chat (recommended)
./scripts/obsidian-chat.sh

# Start new personal category session
./scripts/obsidian-chat.sh --new personal

# Resume specific session
./scripts/obsidian-chat.sh --session abc123

# List all sessions
./scripts/obsidian-chat.sh --list

# View session history
./scripts/obsidian-chat.sh --history abc123

# Delete session
./scripts/obsidian-chat.sh --delete abc123
```

### Python API

```python
from obsidian_chat import ChatDatabase, RAGChat

# Create new session
db = ChatDatabase()
session_id = db.create_session(category='work')

# Chat with notes
chat = RAGChat(session_id, category='work')
result = chat.chat("독서클럽에 대해 알려줘")

print(result['response'])
print(f"Sources: {', '.join(result['sources'])}")
```

### n8n API

```bash
# Create new session
curl -X POST http://localhost:5678/webhook/obe-chat \
  -H "Content-Type: application/json" \
  -d '{"action": "new", "category": "work"}'

# Send message
curl -X POST http://localhost:5678/webhook/obe-chat \
  -H "Content-Type: application/json" \
  -d '{
    "action": "chat",
    "session_id": "abc123",
    "message": "독서클럽에 대해 알려줘"
  }'

# List sessions
curl -X POST http://localhost:5678/webhook/obe-chat \
  -H "Content-Type: application/json" \
  -d '{"action": "list"}'

# Get history
curl -X POST http://localhost:5678/webhook/obe-chat \
  -H "Content-Type: application/json" \
  -d '{"action": "history", "session_id": "abc123"}'
```

### Context Window Management

The system automatically manages token limits:

- **Chat History**: 4,000 tokens (auto-trimmed from oldest)
- **RAG Context**: 8,000 tokens (top-ranked documents only)
- **Total Budget**: 12,000 tokens (fits most LLM contexts)

Token estimation for Korean/English mixed text:
- Korean: ~1.5 characters per token
- English: ~4 characters per token

### Requirements

```bash
# Install Ollama models
ollama pull bge-m3                # Embedding model
ollama pull qwen2.5-coder:32b     # Chat model (or smaller: qwen2.5:7b)

# Ensure Qdrant is running
docker run -d -p 6333:6333 qdrantdb/qdrant

# Index your notes (if not already done)
python3 scripts/ingest-with-bm25.py
```

### Testing

```bash
# Run comprehensive tests
./scripts/test-chat-system.sh
```

### Documentation

- **Full Guide**: [workflows/active/README-CHAT.md](workflows/active/README-CHAT.md)

### Files

- `scripts/obsidian-chat.py` - RAG chat engine
- `scripts/obsidian-chat.sh` - Interactive CLI interface
- `scripts/test-chat-system.sh` - Test suite
- `workflows/active/obe-chat.json` - n8n workflow
- `db/schema.sql` - Database schema (chat_sessions, chat_history tables)
