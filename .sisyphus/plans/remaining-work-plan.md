# Obsidian Local Sage - Remaining Work Plan

## Overview

This plan covers the remaining phases to complete the Obsidian Local Sage project, including CI/CD setup, PyPI deployment, monorepo conversion, and TypeScript Obsidian plugin development.

**Created:** 2026-01-22
**Plugin Name:** Sage AI
**Target:** Obsidian Community Plugin Store

---

## Phase A: CI/CD & PyPI Deployment

### A.1 GitHub Actions CI Pipeline

**Goal:** Set up automated testing, linting, and coverage reporting

**Files to Create:**
- `.github/workflows/ci.yml`

**Configuration:**
```yaml
Triggers: push to main, pull requests
Python versions: 3.8, 3.9, 3.10, 3.11
Jobs:
  - lint (flake8, black --check)
  - test (pytest with coverage)
  - coverage report (upload to codecov or github summary)
```

**Tasks:**
- [ ] A.1.1 Create `.github/workflows/ci.yml`
- [ ] A.1.2 Add pytest-cov to dev dependencies
- [ ] A.1.3 Create `.flake8` config file
- [ ] A.1.4 Add coverage badge to README
- [ ] A.1.5 Test workflow runs successfully

### A.2 PyPI Deployment Pipeline

**Goal:** Automate package publishing to PyPI

**Files to Create:**
- `.github/workflows/publish.yml`

**Configuration:**
```yaml
Trigger: GitHub release created
Jobs:
  - build (python -m build)
  - publish (twine upload to PyPI)
Secrets required: PYPI_API_TOKEN
```

**Tasks:**
- [ ] A.2.1 Create PyPI account (if not exists)
- [ ] A.2.2 Generate PyPI API token
- [ ] A.2.3 Add PYPI_API_TOKEN to GitHub secrets
- [ ] A.2.4 Create `.github/workflows/publish.yml`
- [ ] A.2.5 Update pyproject.toml with final metadata
- [ ] A.2.6 Test publish with v0.1.0 release

---

## Phase B: Monorepo Conversion

### B.1 Project Structure Migration

**Goal:** Convert to pnpm workspaces monorepo

**New Structure:**
```
obsidian-local-sage/
├── packages/
│   ├── cli/                      # Python CLI (existing code moved here)
│   │   ├── src/
│   │   │   ├── core/
│   │   │   ├── search/
│   │   │   ├── jump/
│   │   │   ├── batch/
│   │   │   ├── health/
│   │   │   ├── analysis/
│   │   │   └── cli.py
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   ├── requirements.txt
│   │   └── requirements-dev.txt
│   │
│   └── obsidian-plugin/          # TypeScript Plugin (new)
│       ├── src/
│       ├── manifest.json
│       ├── package.json
│       └── tsconfig.json
│
├── shared/
│   └── docs/                     # Shared documentation
│
├── .github/workflows/
│   ├── cli-ci.yml               # Python CI
│   ├── cli-publish.yml          # PyPI publish
│   ├── plugin-ci.yml            # TypeScript CI
│   └── plugin-release.yml       # Obsidian release
│
├── package.json                  # pnpm workspaces root
├── pnpm-workspace.yaml
└── README.md                     # Root readme
```

**Tasks:**
- [ ] B.1.1 Install pnpm globally
- [ ] B.1.2 Create root `package.json` with workspaces config
- [ ] B.1.3 Create `pnpm-workspace.yaml`
- [ ] B.1.4 Create `packages/` directory
- [ ] B.1.5 Move Python code to `packages/cli/`
- [ ] B.1.6 Update Python import paths if needed
- [ ] B.1.7 Update CI workflows for new structure
- [ ] B.1.8 Update install.sh for new structure
- [ ] B.1.9 Create root README.md pointing to packages
- [ ] B.1.10 Verify all tests still pass

---

## Phase C: Sage AI Obsidian Plugin

### C.1 Plugin Project Setup

**Goal:** Initialize TypeScript Obsidian plugin project

**Files to Create:**
```
packages/obsidian-plugin/
├── src/
│   └── main.ts
├── manifest.json
├── package.json
├── tsconfig.json
├── esbuild.config.mjs
├── .eslintrc.js
└── styles.css
```

**Tasks:**
- [ ] C.1.1 Create `packages/obsidian-plugin/` directory
- [ ] C.1.2 Initialize package.json with Obsidian plugin deps
- [ ] C.1.3 Create tsconfig.json for Obsidian
- [ ] C.1.4 Create manifest.json (id: sage-ai, name: Sage AI)
- [ ] C.1.5 Create esbuild.config.mjs for build
- [ ] C.1.6 Create basic main.ts with plugin skeleton
- [ ] C.1.7 Add build scripts (dev, build)
- [ ] C.1.8 Verify `pnpm run build` works

### C.2 Settings & Configuration

**Goal:** Plugin settings UI for Ollama/Qdrant connection

**Features:**
- Ollama API URL (default: http://127.0.0.1:11434)
- Ollama model name (default: bge-m3)
- Qdrant URL (default: http://127.0.0.1:6333)
- Qdrant collection name
- Search result limit
- Minimum score threshold

**Files:**
- `src/settings.ts` - Settings tab implementation
- `src/types.ts` - TypeScript interfaces

**Tasks:**
- [ ] C.2.1 Create settings interface (SageAISettings)
- [ ] C.2.2 Create SettingsTab class
- [ ] C.2.3 Add settings UI components
- [ ] C.2.4 Implement save/load settings
- [ ] C.2.5 Add connection test buttons

### C.3 Ollama Integration

**Goal:** Direct REST API calls to Ollama for embeddings

**API Endpoint:** `POST /api/embeddings`
```json
{
  "model": "bge-m3",
  "prompt": "text to embed"
}
```

**Files:**
- `src/services/ollama.ts`

**Tasks:**
- [ ] C.3.1 Create OllamaService class
- [ ] C.3.2 Implement getEmbedding(text) method
- [ ] C.3.3 Implement getBatchEmbeddings(texts) method
- [ ] C.3.4 Add error handling and retry logic
- [ ] C.3.5 Add connection health check

### C.4 Qdrant Integration

**Goal:** Direct REST API calls to Qdrant for vector search

**API Endpoints:**
- `GET /collections/{name}` - Check collection exists
- `POST /collections/{name}/points/search` - Vector search
- `PUT /collections/{name}/points` - Upsert vectors

**Files:**
- `src/services/qdrant.ts`

**Tasks:**
- [ ] C.4.1 Create QdrantService class
- [ ] C.4.2 Implement search(vector, limit) method
- [ ] C.4.3 Implement upsert(points) method
- [ ] C.4.4 Implement getCollectionInfo() method
- [ ] C.4.5 Add error handling

### C.5 Document Indexing

**Goal:** Index vault documents into Qdrant

**Features:**
- Scan vault for markdown files
- Generate embeddings via Ollama
- Store in Qdrant with metadata
- Track indexed files (avoid re-indexing)
- Incremental indexing support

**Files:**
- `src/indexer.ts`

**Tasks:**
- [ ] C.5.1 Create DocumentIndexer class
- [ ] C.5.2 Implement vault file scanning
- [ ] C.5.3 Implement content chunking
- [ ] C.5.4 Implement batch embedding generation
- [ ] C.5.5 Implement Qdrant upsert
- [ ] C.5.6 Add progress indicator UI
- [ ] C.5.7 Implement incremental indexing
- [ ] C.5.8 Add "Rebuild Index" command

### C.6 Semantic Search Feature

**Goal:** AI-powered semantic search with results modal

**Features:**
- Command palette: "Sage AI: Search"
- Search input modal
- Results displayed in modal with:
  - Document title
  - Similarity score
  - Content preview
  - Click to open document
- Create results note option

**Files:**
- `src/search.ts`
- `src/ui/SearchModal.ts`
- `src/ui/ResultsModal.ts`

**Tasks:**
- [ ] C.6.1 Create SearchModal class (input UI)
- [ ] C.6.2 Create ResultsModal class (results display)
- [ ] C.6.3 Implement search command
- [ ] C.6.4 Integrate Ollama + Qdrant for search
- [ ] C.6.5 Add "Open document" action
- [ ] C.6.6 Add "Create results note" action
- [ ] C.6.7 Add keyboard navigation in results

### C.7 Document Jump Feature

**Goal:** Quick document finder with fuzzy search

**Features:**
- Command palette: "Sage AI: Jump to Document"
- Fuzzy search modal (SuggestModal)
- Recent documents tracking
- Full-text search across titles/content

**Files:**
- `src/jump.ts`
- `src/ui/JumpModal.ts`

**Tasks:**
- [ ] C.7.1 Create JumpModal extending SuggestModal
- [ ] C.7.2 Implement fuzzy matching
- [ ] C.7.3 Track recent documents (localStorage)
- [ ] C.7.4 Add document preview on hover
- [ ] C.7.5 Implement jump command

### C.8 Plugin Polish

**Goal:** Final polish and documentation

**Tasks:**
- [ ] C.8.1 Add plugin description to manifest.json
- [ ] C.8.2 Create README.md for plugin
- [ ] C.8.3 Add hotkey support for commands
- [ ] C.8.4 Add mobile support check
- [ ] C.8.5 Test on Windows/Mac/Linux
- [ ] C.8.6 Create demo GIF/video

---

## Phase D: Community Deployment

### D.1 Obsidian Plugin Submission

**Goal:** Submit to Obsidian community plugin store

**Requirements:**
- GitHub repository is public
- manifest.json is valid
- main.js and styles.css in root
- README.md with installation instructions
- No console.log in production

**Tasks:**
- [ ] D.1.1 Review Obsidian plugin guidelines
- [ ] D.1.2 Create GitHub release workflow
- [ ] D.1.3 Ensure manifest.json meets requirements
- [ ] D.1.4 Create PR to obsidian-releases repo
- [ ] D.1.5 Respond to review feedback
- [ ] D.1.6 Announce plugin release

### D.2 Documentation & Marketing

**Tasks:**
- [ ] D.2.1 Create plugin landing page
- [ ] D.2.2 Write blog post / announcement
- [ ] D.2.3 Create video tutorial
- [ ] D.2.4 Share on Reddit/Discord/Twitter

---

## Dependencies & Prerequisites

### Required Services (User must have installed)
- **Ollama** with bge-m3 model
- **Qdrant** vector database (Docker)

### Development Dependencies

**Python (packages/cli):**
- pytest, pytest-cov
- black, flake8
- mypy

**TypeScript (packages/obsidian-plugin):**
- typescript
- obsidian (types)
- esbuild
- eslint

---

## Timeline Estimate

| Phase | Estimated Effort |
|-------|------------------|
| Phase A: CI/CD & PyPI | 2-3 hours |
| Phase B: Monorepo | 2-3 hours |
| Phase C: Plugin | 15-20 hours |
| Phase D: Deployment | 3-5 hours |

**Total:** 22-31 hours

---

## Success Criteria

- [ ] CI pipeline runs on every push
- [ ] Package published to PyPI
- [ ] Monorepo structure working with pnpm
- [ ] Sage AI plugin builds successfully
- [ ] Search feature works in Obsidian
- [ ] Document jump feature works
- [ ] Plugin submitted to community store

---

## Notes

- Keep Ollama/Qdrant as required dependencies (power user target)
- Can add optional cloud backend in future version
- Consider adding link suggestions in v2
- Consider adding document comparison in v2
