import { App, Modal, Setting, Notice, debounce } from 'obsidian';
import { DocumentIndexer } from '../services/indexer';

interface SearchResultItem {
  path: string;
  title: string;
  score: number;
  excerpt: string;
}

export class SearchModal extends Modal {
  private indexer: DocumentIndexer;
  private results: SearchResultItem[] = [];
  private resultsContainer: HTMLElement;
  private inputEl: HTMLInputElement;
  private statusEl: HTMLElement;
  private maxResults: number;
  private minScore: number;

  constructor(
    app: App,
    indexer: DocumentIndexer,
    maxResults: number = 10,
    minScore: number = 0.3
  ) {
    super(app);
    this.indexer = indexer;
    this.maxResults = maxResults;
    this.minScore = minScore;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.addClass('sage-ai-search-modal');

    // Title
    contentEl.createEl('h2', { text: 'Sage AI: Semantic Search' });

    // Search input
    const inputContainer = contentEl.createDiv({
      cls: 'sage-ai-search-input-container',
    });

    this.inputEl = inputContainer.createEl('input', {
      type: 'text',
      placeholder: 'Search by meaning...',
      cls: 'sage-ai-search-input',
    });

    this.inputEl.focus();

    // Status line
    this.statusEl = contentEl.createDiv({ cls: 'sage-ai-search-status' });
    this.statusEl.setText('Type to search');

    // Results container
    this.resultsContainer = contentEl.createDiv({
      cls: 'sage-ai-search-results',
    });

    // Debounced search
    const debouncedSearch = debounce(
      async (query: string) => {
        if (query.length < 2) {
          this.statusEl.setText('Type at least 2 characters');
          this.resultsContainer.empty();
          return;
        }

        this.statusEl.setText('Searching...');

        try {
          this.results = await this.indexer.search(
            query,
            this.maxResults,
            this.minScore
          );
          this.renderResults();

          if (this.results.length === 0) {
            this.statusEl.setText('No results found');
          } else {
            this.statusEl.setText(
              `Found ${this.results.length} result${this.results.length === 1 ? '' : 's'}`
            );
          }
        } catch (error) {
          console.error('Search error:', error);
          this.statusEl.setText(
            `Error: ${error instanceof Error ? error.message : 'Search failed'}`
          );
        }
      },
      300,
      true
    );

    this.inputEl.addEventListener('input', () => {
      debouncedSearch(this.inputEl.value);
    });

    // Handle keyboard navigation
    this.inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.close();
      } else if (e.key === 'Enter' && this.results.length > 0) {
        this.openResult(this.results[0]);
      }
    });
  }

  private renderResults() {
    this.resultsContainer.empty();

    for (const result of this.results) {
      const resultEl = this.resultsContainer.createDiv({
        cls: 'sage-ai-search-result',
      });

      // Title with score
      const titleRow = resultEl.createDiv({ cls: 'sage-ai-result-title-row' });
      titleRow.createSpan({ text: result.title, cls: 'sage-ai-result-title' });
      titleRow.createSpan({
        text: `${Math.round(result.score * 100)}%`,
        cls: 'sage-ai-result-score',
      });

      // Path
      resultEl.createDiv({
        text: result.path,
        cls: 'sage-ai-result-path',
      });

      // Excerpt
      if (result.excerpt) {
        const excerptText =
          result.excerpt.length > 150
            ? result.excerpt.substring(0, 150) + '...'
            : result.excerpt;
        resultEl.createDiv({
          text: excerptText,
          cls: 'sage-ai-result-excerpt',
        });
      }

      // Click handler
      resultEl.addEventListener('click', () => {
        this.openResult(result);
      });
    }
  }

  private async openResult(result: SearchResultItem) {
    const file = this.app.vault.getAbstractFileByPath(result.path);
    if (file) {
      await this.app.workspace.openLinkText(result.path, '', false);
      this.close();
    } else {
      new Notice(`File not found: ${result.path}`);
    }
  }

  onClose() {
    const { contentEl } = this;
    contentEl.empty();
  }
}
