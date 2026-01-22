import { App, Modal, Notice } from 'obsidian';
import { DocumentIndexer } from '../services/indexer';

export class IndexModal extends Modal {
  private indexer: DocumentIndexer;
  private progressEl: HTMLElement;
  private statusEl: HTMLElement;
  private buttonEl: HTMLButtonElement;
  private isIndexing: boolean = false;

  constructor(app: App, indexer: DocumentIndexer) {
    super(app);
    this.indexer = indexer;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.addClass('sage-ai-index-modal');

    // Title
    contentEl.createEl('h2', { text: 'Sage AI: Rebuild Index' });

    // Description
    contentEl.createEl('p', {
      text: 'This will re-index all markdown files in your vault. Existing index data will be updated.',
      cls: 'sage-ai-index-description',
    });

    // Progress bar container
    const progressContainer = contentEl.createDiv({
      cls: 'sage-ai-progress-container',
    });
    this.progressEl = progressContainer.createDiv({
      cls: 'sage-ai-progress-bar',
    });

    // Status text
    this.statusEl = contentEl.createDiv({ cls: 'sage-ai-index-status' });

    // Button container
    const buttonContainer = contentEl.createDiv({
      cls: 'sage-ai-button-container',
    });

    this.buttonEl = buttonContainer.createEl('button', {
      text: 'Start Indexing',
      cls: 'mod-cta',
    });

    this.buttonEl.addEventListener('click', () => {
      this.startIndexing();
    });

    // Initial check
    this.checkHealth();
  }

  private async checkHealth() {
    this.statusEl.setText('Checking connections...');

    try {
      const health = await this.indexer.healthCheck();

      if (!health.ollama.healthy) {
        this.statusEl.setText(`Ollama: ${health.ollama.message}`);
        this.buttonEl.disabled = true;
        return;
      }

      // Qdrant collection might not exist yet, that's OK
      if (!health.qdrant.healthy && !health.qdrant.message.includes('not found')) {
        this.statusEl.setText(`Qdrant: ${health.qdrant.message}`);
        this.buttonEl.disabled = true;
        return;
      }

      const files = this.app.vault.getMarkdownFiles();
      this.statusEl.setText(`Ready to index ${files.length} files`);
      this.buttonEl.disabled = false;
    } catch (error) {
      this.statusEl.setText(
        `Error: ${error instanceof Error ? error.message : 'Connection failed'}`
      );
      this.buttonEl.disabled = true;
    }
  }

  private async startIndexing() {
    if (this.isIndexing) return;
    this.isIndexing = true;
    this.buttonEl.disabled = true;
    this.buttonEl.setText('Indexing...');

    const startTime = Date.now();

    try {
      const stats = await this.indexer.indexVault((current, total, file) => {
        const percent = (current / total) * 100;
        this.progressEl.style.width = `${percent}%`;
        this.statusEl.setText(`${current}/${total}: ${file}`);
      });

      const duration = ((Date.now() - startTime) / 1000).toFixed(1);
      this.statusEl.setText(
        `Indexed ${stats.totalDocuments} documents in ${duration}s`
      );
      this.progressEl.style.width = '100%';
      this.buttonEl.setText('Done');

      new Notice(
        `Sage AI: Indexed ${stats.totalDocuments} documents in ${duration}s`
      );
    } catch (error) {
      console.error('Indexing error:', error);
      this.statusEl.setText(
        `Error: ${error instanceof Error ? error.message : 'Indexing failed'}`
      );
      this.buttonEl.setText('Retry');
      this.buttonEl.disabled = false;
    } finally {
      this.isIndexing = false;
    }
  }

  onClose() {
    const { contentEl } = this;
    contentEl.empty();
  }
}
