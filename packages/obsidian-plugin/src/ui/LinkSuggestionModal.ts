import { App, Modal, TFile, Notice } from 'obsidian';
import { LinkSuggestionService } from '../services/linkSuggestion';

interface SimilarDocument {
  file: TFile;
  score: number;
  snippets: string[];
  wikilink: string;
}

export class LinkSuggestionModal extends Modal {
  private currentFile: TFile;
  private linkService: LinkSuggestionService;
  private suggestions: SimilarDocument[] = [];
  private isLoading: boolean = false;

  constructor(
    app: App,
    currentFile: TFile,
    linkService: LinkSuggestionService
  ) {
    super(app);
    this.currentFile = currentFile;
    this.linkService = linkService;
  }

  async onOpen() {
    console.log('[LinkSuggestionModal] Modal opened for file:', this.currentFile.path);

    const { contentEl } = this;
    contentEl.empty();
    contentEl.addClass('sage-ai-link-modal');

    // Header
    const header = contentEl.createDiv('sage-ai-modal-header');
    header.createEl('h2', { text: 'Link Suggestions' });
    header.createEl('p', {
      text: `Finding documents related to "${this.currentFile.basename}"`,
      cls: 'sage-ai-modal-description',
    });

    // Status
    const statusEl = contentEl.createDiv('sage-ai-link-status');
    statusEl.setText('🔍 Searching for related documents...');

    // Results container
    const resultsEl = contentEl.createDiv('sage-ai-link-results');

    // Load suggestions
    this.isLoading = true;
    try {
      console.log('[LinkSuggestionModal] Calling findSimilarDocuments...');
      this.suggestions = await this.linkService.findSimilarDocuments(
        this.currentFile,
        8
      );
      console.log('[LinkSuggestionModal] Got suggestions:', this.suggestions.length);
      this.isLoading = false;

      if (this.suggestions.length === 0) {
        statusEl.setText('No related documents found');
        resultsEl.empty();
        return;
      }

      statusEl.setText(
        `✅ Found ${this.suggestions.length} related document${
          this.suggestions.length > 1 ? 's' : ''
        }`
      );

      this.renderSuggestions(resultsEl);
    } catch (error) {
      this.isLoading = false;
      statusEl.setText('❌ Error finding suggestions');
      console.error('Link suggestion error:', error);
      new Notice(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private renderSuggestions(container: HTMLElement) {
    container.empty();

    this.suggestions.forEach((suggestion, index) => {
      const item = container.createDiv('sage-ai-link-item');

      // Title and score
      const headerRow = item.createDiv('sage-ai-link-header');

      const titleEl = headerRow.createDiv('sage-ai-link-title');
      titleEl.setText(`${index + 1}. ${suggestion.file.basename}`);

      const scoreEl = headerRow.createDiv('sage-ai-link-score');
      scoreEl.setText(`${(suggestion.score * 100).toFixed(1)}%`);

      // Wikilink
      const wikilinkRow = item.createDiv('sage-ai-link-wikilink');
      const wikilinkCode = wikilinkRow.createEl('code');
      wikilinkCode.setText(suggestion.wikilink);

      // Copy button
      const copyBtn = wikilinkRow.createEl('button', {
        text: '📋 Copy',
        cls: 'sage-ai-copy-btn',
      });
      copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(suggestion.wikilink);
        new Notice('Wikilink copied to clipboard!');
      });

      // Snippet
      if (suggestion.snippets && suggestion.snippets.length > 0) {
        const snippetEl = item.createDiv('sage-ai-link-snippet');
        let snippet = suggestion.snippets[0].replace(/\n/g, ' ').trim();
        if (snippet.length > 150) {
          snippet = snippet.slice(0, 150) + '...';
        }
        snippetEl.setText(snippet);
      }

      // Click to open
      item.addEventListener('click', (e) => {
        if (!(e.target as HTMLElement).classList.contains('sage-ai-copy-btn')) {
          this.app.workspace.getLeaf().openFile(suggestion.file);
          this.close();
        }
      });
    });

    // Help text
    const helpEl = container.createDiv('sage-ai-link-help');
    helpEl.setText(
      '💡 Click a document to open it, or click 📋 Copy to copy the wikilink'
    );
  }

  onClose() {
    const { contentEl } = this;
    contentEl.empty();
  }
}
