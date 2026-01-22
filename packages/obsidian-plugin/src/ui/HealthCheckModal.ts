import { App, Modal, Notice } from 'obsidian';
import { HealthCheckService, HealthCheckResult, HealthCheckIssue } from '../services/healthCheck';

export class HealthCheckModal extends Modal {
  private healthService: HealthCheckService;
  private result: HealthCheckResult | null = null;
  private isRunning: boolean = false;

  constructor(app: App, healthService: HealthCheckService) {
    super(app);
    this.healthService = healthService;
  }

  async onOpen() {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.addClass('sage-ai-health-modal');

    // Header
    const header = contentEl.createDiv('sage-ai-modal-header');
    header.createEl('h2', { text: '🏥 Vault Health Check' });
    header.createEl('p', {
      text: 'Analyzing your vault for potential issues...',
      cls: 'sage-ai-modal-description',
    });

    // Progress status
    const statusEl = contentEl.createDiv('sage-ai-health-status');
    statusEl.setText('🔍 Starting health check...');

    // Progress bar
    const progressContainer = contentEl.createDiv('sage-ai-progress-container');
    const progressBar = progressContainer.createDiv('sage-ai-progress-bar');

    // Results container
    const resultsEl = contentEl.createDiv('sage-ai-health-results');

    // Run health check
    this.isRunning = true;
    try {
      this.result = await this.healthService.runHealthCheck(
        (current, total, checkName) => {
          const percent = (current / total) * 100;
          progressBar.style.width = `${percent}%`;
          statusEl.setText(`🔍 ${checkName} (${current}/${total})`);
        }
      );

      this.isRunning = false;
      statusEl.setText(
        `✅ Health check complete! Found ${this.result.totalIssues} issue${
          this.result.totalIssues !== 1 ? 's' : ''
        } in ${this.result.totalFiles} files.`
      );
      progressBar.style.width = '100%';

      this.renderResults(resultsEl);
    } catch (error) {
      this.isRunning = false;
      statusEl.setText('❌ Error running health check');
      console.error('Health check error:', error);
      new Notice(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private renderResults(container: HTMLElement) {
    container.empty();

    if (!this.result) return;

    if (this.result.totalIssues === 0) {
      const successEl = container.createDiv('sage-ai-health-success');
      successEl.createEl('h3', { text: '✅ Your vault is healthy!' });
      successEl.createEl('p', { text: 'No issues found.' });
      return;
    }

    // Summary
    const summaryEl = container.createDiv('sage-ai-health-summary');
    summaryEl.createEl('h3', { text: '📊 Summary' });
    summaryEl.createEl('p', {
      text: `Total files scanned: ${this.result.totalFiles}`,
    });
    summaryEl.createEl('p', {
      text: `Total issues found: ${this.result.totalIssues}`,
    });

    // Issue categories
    const issues = this.result.issues;

    this.renderIssueSection(container, '📄 Empty Documents', issues.empty);
    this.renderIssueSection(container, '⚠️ Nearly Empty Documents (< 20 chars)', issues.nearly_empty);
    this.renderIssueSection(container, '🔗 Orphaned Documents (No Incoming Links)', issues.orphaned);
    this.renderIssueSection(container, '🔗 Broken Links', issues.broken_links);
    this.renderIssueSection(container, '📁 Duplicate Names', issues.duplicates);
    this.renderIssueSection(container, '⏰ Old Documents (> 1 year)', issues.old);
    this.renderIssueSection(container, '📏 Large Documents (> 100KB)', issues.large);
    this.renderIssueSection(container, '🏷️ Documents Without Tags', issues.no_tags);
    this.renderIssueSection(container, '✅ Documents With Uncompleted TODOs', issues.todos);

    // Suggestions
    if (this.result.totalIssues > 0) {
      const suggestionsEl = container.createDiv('sage-ai-health-suggestions');
      suggestionsEl.createEl('h3', { text: '💡 Suggestions' });

      const list = suggestionsEl.createEl('ul');
      list.createEl('li', { text: 'Empty documents: Add content or delete them' });
      list.createEl('li', { text: 'Orphaned documents: Link them from other notes' });
      list.createEl('li', { text: 'Broken links: Fix or remove invalid links' });
      list.createEl('li', { text: 'Duplicate names: Rename to make them unique' });
      list.createEl('li', { text: 'Old documents: Archive or delete outdated content' });
    }
  }

  private renderIssueSection(
    container: HTMLElement,
    title: string,
    issues: HealthCheckIssue[]
  ) {
    if (issues.length === 0) return;

    const section = container.createDiv('sage-ai-health-section');
    const headerEl = section.createDiv('sage-ai-health-section-header');
    headerEl.createEl('h4', { text: `${title} (${issues.length})` });

    const listEl = section.createDiv('sage-ai-health-issue-list');

    const maxDisplay = 10;
    const displayIssues = issues.slice(0, maxDisplay);

    for (const issue of displayIssues) {
      const itemEl = listEl.createDiv('sage-ai-health-issue-item');

      const titleEl = itemEl.createDiv('sage-ai-health-issue-title');
      titleEl.setText(issue.file.path);

      if (issue.details) {
        const detailsEl = itemEl.createDiv('sage-ai-health-issue-details');
        detailsEl.setText(issue.details);
      }

      // Make clickable to open file
      itemEl.addEventListener('click', () => {
        this.app.workspace.getLeaf().openFile(issue.file);
        this.close();
      });
    }

    if (issues.length > maxDisplay) {
      const moreEl = listEl.createDiv('sage-ai-health-issue-more');
      moreEl.setText(`... and ${issues.length - maxDisplay} more`);
    }
  }

  onClose() {
    const { contentEl } = this;
    contentEl.empty();
  }
}
