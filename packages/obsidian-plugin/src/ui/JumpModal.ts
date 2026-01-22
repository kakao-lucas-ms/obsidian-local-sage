import { App, FuzzySuggestModal, TFile, FuzzyMatch } from 'obsidian';

export class JumpModal extends FuzzySuggestModal<TFile> {
  constructor(app: App) {
    super(app);
    this.setPlaceholder('Jump to document...');
    this.setInstructions([
      { command: '↑↓', purpose: 'navigate' },
      { command: '↵', purpose: 'open' },
      { command: 'esc', purpose: 'dismiss' },
    ]);
  }

  getItems(): TFile[] {
    return this.app.vault.getMarkdownFiles().sort((a, b) => {
      // Sort by modification time (most recent first)
      return b.stat.mtime - a.stat.mtime;
    });
  }

  getItemText(file: TFile): string {
    // Return path without extension for better matching
    return file.path.replace(/\.md$/, '');
  }

  renderSuggestion(match: FuzzyMatch<TFile>, el: HTMLElement): void {
    const file = match.item;
    const container = el.createDiv({ cls: 'sage-ai-jump-suggestion' });

    // File name
    container.createDiv({
      text: file.basename,
      cls: 'sage-ai-jump-title',
    });

    // Full path (if in folder)
    if (file.parent && file.parent.path !== '/') {
      container.createDiv({
        text: file.parent.path,
        cls: 'sage-ai-jump-path',
      });
    }

    // Last modified
    const mtime = new Date(file.stat.mtime);
    const timeAgo = this.formatTimeAgo(mtime);
    container.createDiv({
      text: timeAgo,
      cls: 'sage-ai-jump-mtime',
    });
  }

  onChooseItem(file: TFile): void {
    this.app.workspace.openLinkText(file.path, '', false);
  }

  private formatTimeAgo(date: Date): string {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) {
      return 'just now';
    } else if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  }
}
