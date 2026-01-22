import { TFile, Vault } from 'obsidian';

export interface HealthCheckIssue {
  type: 'empty' | 'nearly_empty' | 'orphaned' | 'broken_link' | 'duplicate' | 'old' | 'large' | 'no_tags' | 'todos';
  file: TFile;
  details?: string;
  count?: number;
  size?: number;
  days?: number;
}

export interface HealthCheckResult {
  totalFiles: number;
  totalIssues: number;
  issues: {
    empty: HealthCheckIssue[];
    nearly_empty: HealthCheckIssue[];
    orphaned: HealthCheckIssue[];
    broken_links: HealthCheckIssue[];
    duplicates: HealthCheckIssue[];
    old: HealthCheckIssue[];
    large: HealthCheckIssue[];
    no_tags: HealthCheckIssue[];
    todos: HealthCheckIssue[];
  };
}

export class HealthCheckService {
  constructor(private vault: Vault) {}

  /**
   * Run full health check on vault
   */
  async runHealthCheck(
    onProgress?: (current: number, total: number, checkName: string) => void
  ): Promise<HealthCheckResult> {
    const files = this.vault.getMarkdownFiles();
    const totalChecks = 8;
    let currentCheck = 0;

    const result: HealthCheckResult = {
      totalFiles: files.length,
      totalIssues: 0,
      issues: {
        empty: [],
        nearly_empty: [],
        orphaned: [],
        broken_links: [],
        duplicates: [],
        old: [],
        large: [],
        no_tags: [],
        todos: [],
      },
    };

    // Check 1: Empty documents
    onProgress?.(++currentCheck, totalChecks, 'Checking empty documents...');
    await this.checkEmptyDocuments(files, result);

    // Check 2: Orphaned documents
    onProgress?.(++currentCheck, totalChecks, 'Checking orphaned documents...');
    await this.checkOrphanedDocuments(files, result);

    // Check 3: Broken links
    onProgress?.(++currentCheck, totalChecks, 'Checking broken links...');
    await this.checkBrokenLinks(files, result);

    // Check 4: Duplicate names
    onProgress?.(++currentCheck, totalChecks, 'Checking duplicate names...');
    this.checkDuplicateNames(files, result);

    // Check 5: Old documents
    onProgress?.(++currentCheck, totalChecks, 'Checking old documents...');
    this.checkOldDocuments(files, result);

    // Check 6: Large documents
    onProgress?.(++currentCheck, totalChecks, 'Checking large documents...');
    await this.checkLargeDocuments(files, result);

    // Check 7: Missing tags
    onProgress?.(++currentCheck, totalChecks, 'Checking missing tags...');
    await this.checkMissingTags(files, result);

    // Check 8: TODO items
    onProgress?.(++currentCheck, totalChecks, 'Checking TODO items...');
    await this.checkTodoItems(files, result);

    // Calculate total issues
    result.totalIssues = Object.values(result.issues).reduce(
      (sum, arr) => sum + arr.length,
      0
    );

    return result;
  }

  private async checkEmptyDocuments(
    files: TFile[],
    result: HealthCheckResult
  ): Promise<void> {
    for (const file of files) {
      try {
        const content = (await this.vault.cachedRead(file)).trim();

        if (content.length === 0) {
          result.issues.empty.push({ type: 'empty', file });
        } else if (content.length < 20) {
          result.issues.nearly_empty.push({
            type: 'nearly_empty',
            file,
            size: content.length,
          });
        }
      } catch (error) {
        console.error(`Error checking ${file.path}:`, error);
      }
    }
  }

  private async checkOrphanedDocuments(
    files: TFile[],
    result: HealthCheckResult
  ): Promise<void> {
    // Build link graph
    const incomingLinks = new Map<string, Set<string>>();

    for (const file of files) {
      try {
        const content = await this.vault.cachedRead(file);

        // Find all wikilinks
        const linkRegex = /\[\[([^\]|]+)/g;
        let match;

        while ((match = linkRegex.exec(content)) !== null) {
          const target = match[1].trim();
          if (!incomingLinks.has(target)) {
            incomingLinks.set(target, new Set());
          }
          incomingLinks.get(target)!.add(file.path);
        }
      } catch (error) {
        console.error(`Error checking ${file.path}:`, error);
      }
    }

    // Find documents with no incoming links
    for (const file of files) {
      const basename = file.basename;

      if (!incomingLinks.has(basename) || incomingLinks.get(basename)!.size === 0) {
        // Check if it's a special file (index, MOC, etc.)
        const isSpecial = /index|moc|readme|목차/i.test(basename);

        if (!isSpecial) {
          result.issues.orphaned.push({ type: 'orphaned', file });
        }
      }
    }
  }

  private async checkBrokenLinks(
    files: TFile[],
    result: HealthCheckResult
  ): Promise<void> {
    for (const file of files) {
      try {
        const content = await this.vault.cachedRead(file);

        // Find all wikilinks
        const linkRegex = /\[\[([^\]|]+)/g;
        let match;

        while ((match = linkRegex.exec(content)) !== null) {
          const target = match[1].trim();

          // Try to find target file
          const targetFile = this.vault.getAbstractFileByPath(`${target}.md`);

          if (!targetFile) {
            result.issues.broken_links.push({
              type: 'broken_link',
              file,
              details: target,
            });
          }
        }
      } catch (error) {
        console.error(`Error checking ${file.path}:`, error);
      }
    }
  }

  private checkDuplicateNames(files: TFile[], result: HealthCheckResult): void {
    const names = new Map<string, TFile[]>();

    for (const file of files) {
      const basename = file.basename;
      if (!names.has(basename)) {
        names.set(basename, []);
      }
      names.get(basename)!.push(file);
    }

    for (const [name, duplicateFiles] of names.entries()) {
      if (duplicateFiles.length > 1) {
        for (const file of duplicateFiles) {
          result.issues.duplicates.push({
            type: 'duplicate',
            file,
            details: `${duplicateFiles.length} files named "${name}"`,
            count: duplicateFiles.length,
          });
        }
      }
    }
  }

  private checkOldDocuments(files: TFile[], result: HealthCheckResult): void {
    const oneYearAgo = Date.now() - 365 * 24 * 60 * 60 * 1000;

    for (const file of files) {
      if (file.stat.mtime < oneYearAgo) {
        const daysOld = Math.floor((Date.now() - file.stat.mtime) / (24 * 60 * 60 * 1000));
        result.issues.old.push({
          type: 'old',
          file,
          days: daysOld,
          details: `${daysOld} days old`,
        });
      }
    }
  }

  private async checkLargeDocuments(
    files: TFile[],
    result: HealthCheckResult
  ): Promise<void> {
    const sizeThreshold = 100 * 1000; // 100KB

    for (const file of files) {
      if (file.stat.size > sizeThreshold) {
        try {
          const content = await this.vault.cachedRead(file);
          const lines = content.split('\n').length;

          result.issues.large.push({
            type: 'large',
            file,
            size: file.stat.size,
            count: lines,
            details: `${(file.stat.size / 1024).toFixed(1)}KB, ${lines} lines`,
          });
        } catch (error) {
          console.error(`Error checking ${file.path}:`, error);
        }
      }
    }
  }

  private async checkMissingTags(
    files: TFile[],
    result: HealthCheckResult
  ): Promise<void> {
    for (const file of files) {
      try {
        const content = await this.vault.cachedRead(file);

        // Find tags (#tag)
        const tagRegex = /#(\w+)/g;
        const hasTags = tagRegex.test(content);

        if (!hasTags) {
          result.issues.no_tags.push({ type: 'no_tags', file });
        }
      } catch (error) {
        console.error(`Error checking ${file.path}:`, error);
      }
    }
  }

  private async checkTodoItems(
    files: TFile[],
    result: HealthCheckResult
  ): Promise<void> {
    for (const file of files) {
      try {
        const content = await this.vault.cachedRead(file);

        // Find uncompleted TODO items
        const todoRegex = /- \[ \] /g;
        const todos = content.match(todoRegex);

        if (todos && todos.length > 0) {
          result.issues.todos.push({
            type: 'todos',
            file,
            count: todos.length,
            details: `${todos.length} uncompleted TODO${todos.length > 1 ? 's' : ''}`,
          });
        }
      } catch (error) {
        console.error(`Error checking ${file.path}:`, error);
      }
    }
  }
}
