import { TFile, Vault } from 'obsidian';
import { OllamaService } from './ollama';
import { QdrantService, QdrantSearchResult } from './qdrant';

interface SimilarDocument {
  file: TFile;
  score: number;
  snippets: string[];
  wikilink: string;
}

export class LinkSuggestionService {
  constructor(
    private vault: Vault,
    private ollama: OllamaService,
    private qdrant: QdrantService
  ) {}

  /**
   * Extract key phrases from document for embedding
   */
  private async extractKeyPhrases(file: TFile): Promise<string> {
    const content = await this.vault.cachedRead(file);

    // Extract first paragraph (skip headings)
    const lines = content
      .split('\n')
      .map(line => line.trim())
      .filter(line => line && !line.startsWith('#'));

    const firstPara = lines[0] || '';

    // Extract headings
    const headings = content
      .split('\n')
      .filter(line => line.startsWith('##'))
      .map(line => line.replace(/^#+\s*/, ''))
      .slice(0, 3);

    // Combine for context
    const context = `${firstPara} ${headings.join(' ')}`;
    return context.slice(0, 500);
  }

  /**
   * Group search results by document
   */
  private groupByDocument(results: QdrantSearchResult[]): Map<string, { score: number; chunks: string[] }> {
    const docs = new Map<string, { score: number; chunks: string[] }>();

    for (const result of results) {
      // Indexer stores as 'path', not 'file_path'
      const filePath = result.payload.path as string;
      // Indexer stores 'excerpt', not 'chunk'
      const excerpt = result.payload.excerpt as string;
      const score = result.score;

      console.log('[LinkSuggestion] Processing result:', { filePath, score, hasExcerpt: !!excerpt });

      if (!filePath) {
        console.warn('[LinkSuggestion] No path in payload:', result.payload);
        continue;
      }

      if (!docs.has(filePath)) {
        docs.set(filePath, { score: 0, chunks: [] });
      }

      const doc = docs.get(filePath)!;
      doc.score = Math.max(doc.score, score);
      if (excerpt) {
        doc.chunks.push(excerpt);
      }
    }

    return docs;
  }

  /**
   * Generate Obsidian wikilink for a file
   */
  private generateWikilink(file: TFile): string {
    const path = file.path.replace(/\.md$/, '');
    const title = file.basename;
    return `[[${path}|${title}]]`;
  }

  /**
   * Find similar documents to the given file
   */
  async findSimilarDocuments(
    currentFile: TFile,
    limit: number = 8
  ): Promise<SimilarDocument[]> {
    try {
      console.log('[LinkSuggestion] Finding similar documents for:', currentFile.path);

      // Extract key phrases for embedding
      const context = await this.extractKeyPhrases(currentFile);
      console.log('[LinkSuggestion] Extracted context:', context.slice(0, 100) + '...');

      if (!context) {
        console.warn('[LinkSuggestion] No context extracted');
        return [];
      }

      // Get embedding from Ollama
      console.log('[LinkSuggestion] Getting embedding from Ollama...');
      const embedding = await this.ollama.getEmbedding(context);
      console.log('[LinkSuggestion] Embedding received, length:', embedding.length);

      // Search Qdrant (get extra to filter out current doc)
      console.log('[LinkSuggestion] Searching Qdrant...');
      const searchResults = await this.qdrant.search(embedding, limit + 5);
      console.log('[LinkSuggestion] Search results count:', searchResults.length);

      if (searchResults.length === 0) {
        console.warn('[LinkSuggestion] No search results from Qdrant');
        return [];
      }

      // Group by document
      const grouped = this.groupByDocument(searchResults);
      console.log('[LinkSuggestion] Grouped documents:', grouped.size);

      // Filter out current document and convert to SimilarDocument
      const suggestions: SimilarDocument[] = [];
      const currentPath = currentFile.path;

      for (const [filePath, data] of grouped.entries()) {
        console.log('[LinkSuggestion] Processing:', filePath, 'score:', data.score);

        if (filePath === currentPath) {
          console.log('[LinkSuggestion] Skipping current file');
          continue;
        }

        const file = this.vault.getAbstractFileByPath(filePath);
        if (!(file instanceof TFile)) {
          console.warn('[LinkSuggestion] File not found:', filePath);
          continue;
        }

        suggestions.push({
          file,
          score: data.score,
          snippets: data.chunks,
          wikilink: this.generateWikilink(file),
        });

        if (suggestions.length >= limit) break;
      }

      // Sort by score descending
      suggestions.sort((a, b) => b.score - a.score);

      console.log('[LinkSuggestion] Final suggestions count:', suggestions.length);
      return suggestions;
    } catch (error) {
      console.error('[LinkSuggestion] Error finding similar documents:', error);
      throw error;
    }
  }
}
