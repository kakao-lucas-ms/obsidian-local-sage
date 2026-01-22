import { App, Modal, SuggestModal, TFile, Notice } from 'obsidian';
import { DocumentComparisonService, ComparisonResult } from '../services/documentComparison';

// File selection modal
export class FileSelectionModal extends SuggestModal<TFile> {
  private onSelect: (file: TFile) => void;
  private currentFile: TFile;

  constructor(app: App, currentFile: TFile, onSelect: (file: TFile) => void) {
    super(app);
    this.currentFile = currentFile;
    this.onSelect = onSelect;

    this.setPlaceholder('Select a document to compare with...');
  }

  getSuggestions(query: string): TFile[] {
    const files = this.app.vault.getMarkdownFiles();

    // Filter out current file and apply query
    const filtered = files.filter(
      file =>
        file.path !== this.currentFile.path &&
        file.path.toLowerCase().includes(query.toLowerCase())
    );

    return filtered.sort((a, b) => b.stat.mtime - a.stat.mtime);
  }

  renderSuggestion(file: TFile, el: HTMLElement) {
    el.createDiv({ text: file.basename, cls: 'suggestion-title' });
    el.createDiv({ text: file.path, cls: 'suggestion-note' });
  }

  onChooseSuggestion(file: TFile) {
    this.onSelect(file);
  }
}

// Comparison result modal
export class DocumentComparisonModal extends Modal {
  private result: ComparisonResult;

  constructor(app: App, result: ComparisonResult) {
    super(app);
    this.result = result;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.addClass('sage-ai-comparison-modal');

    // Header
    const header = contentEl.createDiv('sage-ai-modal-header');
    header.createEl('h2', { text: '📊 Document Comparison' });
    header.createEl('p', {
      text: 'Detailed analysis of similarities and differences',
      cls: 'sage-ai-modal-description',
    });

    // Results container
    const resultsEl = contentEl.createDiv('sage-ai-comparison-results');

    this.renderMetadata(resultsEl);
    this.renderSemanticSimilarity(resultsEl);
    this.renderContentComparison(resultsEl);
    this.renderCommonElements(resultsEl);
    this.renderKeywords(resultsEl);
    this.renderSuggestions(resultsEl);
  }

  private renderMetadata(container: HTMLElement) {
    const section = container.createDiv('sage-ai-comparison-section');
    section.createEl('h3', { text: '📄 Document Metadata' });

    const grid = section.createDiv('sage-ai-comparison-grid');

    // Document 1
    const doc1 = grid.createDiv('sage-ai-comparison-doc');
    doc1.createEl('h4', { text: `1. ${this.result.meta1.title}` });

    const stats1 = doc1.createDiv('sage-ai-comparison-stats');
    stats1.createEl('div', {
      text: `Words: ${this.result.meta1.wordCount} | Lines: ${this.result.meta1.lines}`,
    });
    stats1.createEl('div', {
      text: `Headings: ${this.result.meta1.headings.length} | Tags: ${this.result.meta1.tags.length} | Links: ${this.result.meta1.links.length}`,
    });

    const path1 = doc1.createDiv('sage-ai-comparison-path');
    path1.setText(this.result.file1.path);

    // Document 2
    const doc2 = grid.createDiv('sage-ai-comparison-doc');
    doc2.createEl('h4', { text: `2. ${this.result.meta2.title}` });

    const stats2 = doc2.createDiv('sage-ai-comparison-stats');
    stats2.createEl('div', {
      text: `Words: ${this.result.meta2.wordCount} | Lines: ${this.result.meta2.lines}`,
    });
    stats2.createEl('div', {
      text: `Headings: ${this.result.meta2.headings.length} | Tags: ${this.result.meta2.tags.length} | Links: ${this.result.meta2.links.length}`,
    });

    const path2 = doc2.createDiv('sage-ai-comparison-path');
    path2.setText(this.result.file2.path);
  }

  private renderSemanticSimilarity(container: HTMLElement) {
    const section = container.createDiv('sage-ai-comparison-section');
    section.createEl('h3', { text: '🔍 Semantic Similarity' });

    const simBox = section.createDiv('sage-ai-comparison-similarity');

    const percent = Math.round(this.result.semanticSimilarity * 100);
    const bar = simBox.createDiv('sage-ai-comparison-similarity-bar');
    const fill = bar.createDiv('sage-ai-comparison-similarity-fill');
    fill.style.width = `${percent}%`;

    // Color based on similarity
    if (percent > 80) {
      fill.style.background = 'var(--interactive-success)';
    } else if (percent > 60) {
      fill.style.background = 'var(--interactive-accent)';
    } else if (percent > 40) {
      fill.style.background = 'var(--text-warning)';
    } else {
      fill.style.background = 'var(--text-error)';
    }

    const label = simBox.createDiv('sage-ai-comparison-similarity-label');
    label.setText(`${percent}%`);

    const desc = simBox.createDiv('sage-ai-comparison-similarity-desc');
    if (percent > 80) {
      desc.setText('✅ Very similar documents');
    } else if (percent > 60) {
      desc.setText('✅ Similar topics');
    } else if (percent > 40) {
      desc.setText('⚠️ Some relevance');
    } else {
      desc.setText('❌ Different topics');
    }
  }

  private renderContentComparison(container: HTMLElement) {
    const section = container.createDiv('sage-ai-comparison-section');
    section.createEl('h3', { text: '📝 Content Comparison' });

    const comp = this.result.contentComparison;
    const percent = Math.round(comp.similarityRatio * 100);

    const stats = section.createDiv('sage-ai-comparison-content-stats');
    stats.createEl('div', { text: `Text Match: ${percent}%` });
    stats.createEl('div', {
      text: `Common Lines: ${comp.commonLines} / ${comp.totalLines}`,
    });
  }

  private renderCommonElements(container: HTMLElement) {
    const section = container.createDiv('sage-ai-comparison-section');
    section.createEl('h3', { text: '🔗 Common Elements' });

    // Common tags
    const tagsBox = section.createDiv('sage-ai-comparison-element');
    tagsBox.createEl('h4', { text: '🏷️ Tags' });
    if (this.result.commonTags.length > 0) {
      const tagList = tagsBox.createDiv('sage-ai-comparison-tag-list');
      this.result.commonTags.forEach(tag => {
        tagList.createEl('span', {
          text: `#${tag}`,
          cls: 'sage-ai-comparison-tag',
        });
      });
    } else {
      tagsBox.createEl('div', {
        text: '(None)',
        cls: 'sage-ai-comparison-empty',
      });
    }

    // Common links
    const linksBox = section.createDiv('sage-ai-comparison-element');
    linksBox.createEl('h4', { text: '🔗 Links' });
    if (this.result.commonLinks.length > 0) {
      const linkList = linksBox.createEl('ul');
      this.result.commonLinks.slice(0, 5).forEach(link => {
        linkList.createEl('li', { text: `[[${link}]]` });
      });
      if (this.result.commonLinks.length > 5) {
        linksBox.createEl('div', {
          text: `... +${this.result.commonLinks.length - 5} more`,
          cls: 'sage-ai-comparison-more',
        });
      }
    } else {
      linksBox.createEl('div', {
        text: '(None)',
        cls: 'sage-ai-comparison-empty',
      });
    }
  }

  private renderKeywords(container: HTMLElement) {
    const section = container.createDiv('sage-ai-comparison-section');
    section.createEl('h3', { text: '💡 Keywords' });

    // Common keywords
    const commonBox = section.createDiv('sage-ai-comparison-keywords');
    commonBox.createEl('h4', { text: 'Common Keywords' });
    if (this.result.commonKeywords.length > 0) {
      const keywordList = commonBox.createDiv('sage-ai-comparison-keyword-list');
      this.result.commonKeywords.forEach(kw => {
        keywordList.createEl('span', {
          text: kw,
          cls: 'sage-ai-comparison-keyword',
        });
      });
    } else {
      commonBox.createEl('div', {
        text: '(None)',
        cls: 'sage-ai-comparison-empty',
      });
    }

    // Unique keywords
    const grid = section.createDiv('sage-ai-comparison-grid');

    const unique1 = grid.createDiv('sage-ai-comparison-unique');
    unique1.createEl('h4', { text: `Document 1 Unique` });
    if (this.result.uniqueKeywords1.length > 0) {
      const list1 = unique1.createDiv('sage-ai-comparison-keyword-list');
      this.result.uniqueKeywords1.forEach(kw => {
        list1.createEl('span', {
          text: kw,
          cls: 'sage-ai-comparison-keyword-unique',
        });
      });
    } else {
      unique1.createEl('div', {
        text: '(None)',
        cls: 'sage-ai-comparison-empty',
      });
    }

    const unique2 = grid.createDiv('sage-ai-comparison-unique');
    unique2.createEl('h4', { text: `Document 2 Unique` });
    if (this.result.uniqueKeywords2.length > 0) {
      const list2 = unique2.createDiv('sage-ai-comparison-keyword-list');
      this.result.uniqueKeywords2.forEach(kw => {
        list2.createEl('span', {
          text: kw,
          cls: 'sage-ai-comparison-keyword-unique',
        });
      });
    } else {
      unique2.createEl('div', {
        text: '(None)',
        cls: 'sage-ai-comparison-empty',
      });
    }
  }

  private renderSuggestions(container: HTMLElement) {
    const section = container.createDiv('sage-ai-comparison-section');
    section.createEl('h3', { text: '💡 Suggestions' });

    const list = section.createEl('ul', { cls: 'sage-ai-comparison-suggestions' });
    this.result.suggestions.forEach(suggestion => {
      list.createEl('li', { text: suggestion });
    });
  }

  onClose() {
    const { contentEl } = this;
    contentEl.empty();
  }
}

// Main orchestrator modal
export class CompareDocumentsModal {
  constructor(
    private app: App,
    private currentFile: TFile,
    private comparisonService: DocumentComparisonService
  ) {}

  async open() {
    console.log('[CompareDocuments] Opening file selection modal');

    // Open file selection modal
    new FileSelectionModal(this.app, this.currentFile, async (selectedFile) => {
      console.log('[CompareDocuments] Selected file:', selectedFile.path);

      // Show loading notice
      const notice = new Notice('🔍 Comparing documents...', 0);

      try {
        // Run comparison
        const result = await this.comparisonService.compareDocuments(
          this.currentFile,
          selectedFile
        );

        notice.hide();
        new Notice('✅ Comparison complete!');

        // Show results
        new DocumentComparisonModal(this.app, result).open();
      } catch (error) {
        notice.hide();
        console.error('[CompareDocuments] Error:', error);
        new Notice(`❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }).open();
  }
}
