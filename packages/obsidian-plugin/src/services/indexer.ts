import { App, TFile, Notice, normalizePath } from 'obsidian';
import { OllamaService } from './ollama';
import { QdrantService } from './qdrant';
import { DocumentMetadata, IndexStats } from '../types';

// BGE-M3 produces 1024-dimensional embeddings
const VECTOR_SIZE = 1024;

export interface IndexerConfig {
  ollama: OllamaService;
  qdrant: QdrantService;
  app: App;
}

export class DocumentIndexer {
  private ollama: OllamaService;
  private qdrant: QdrantService;
  private app: App;
  private isIndexing: boolean = false;

  constructor(config: IndexerConfig) {
    this.ollama = config.ollama;
    this.qdrant = config.qdrant;
    this.app = config.app;
  }

  /**
   * Index all markdown files in the vault
   */
  async indexVault(
    onProgress?: (current: number, total: number, file: string) => void
  ): Promise<IndexStats> {
    if (this.isIndexing) {
      throw new Error('Indexing already in progress');
    }

    this.isIndexing = true;
    let indexed = 0;

    try {
      // Ensure collection exists
      await this.qdrant.ensureCollection(VECTOR_SIZE);

      // Get all markdown files
      const files = this.app.vault.getMarkdownFiles();
      const total = files.length;

      for (const file of files) {
        try {
          await this.indexFile(file);
          indexed++;
          onProgress?.(indexed, total, file.path);
        } catch (error) {
          console.error(`Failed to index ${file.path}:`, error);
        }
      }

      return {
        totalDocuments: indexed,
        lastIndexed: Date.now(),
      };
    } finally {
      this.isIndexing = false;
    }
  }

  /**
   * Index a single file
   */
  async indexFile(file: TFile): Promise<void> {
    // Read file content
    const content = await this.app.vault.cachedRead(file);
    if (!content.trim()) {
      return; // Skip empty files
    }

    // Prepare text for embedding (title + content)
    const title = file.basename;
    const textToEmbed = `${title}\n\n${content}`;

    // Truncate if too long (most models have token limits)
    const maxChars = 8000;
    const truncatedText =
      textToEmbed.length > maxChars
        ? textToEmbed.substring(0, maxChars)
        : textToEmbed;

    // Generate embedding
    const embedding = await this.ollama.getEmbedding(truncatedText);

    // Extract metadata from frontmatter
    const metadata = this.extractMetadata(file, content);

    // Generate stable ID from path
    const id = this.pathToId(file.path);

    // Upsert to Qdrant
    await this.qdrant.upsert([
      {
        id,
        vector: embedding,
        payload: {
          path: file.path,
          title: metadata.title,
          mtime: metadata.mtime,
          size: metadata.size,
          tags: metadata.tags,
          aliases: metadata.aliases,
          excerpt: content.substring(0, 500),
        },
      },
    ]);
  }

  /**
   * Remove a file from the index
   */
  async removeFile(path: string): Promise<void> {
    const id = this.pathToId(path);
    await this.qdrant.delete([id]);
  }

  /**
   * Search for similar documents
   */
  async search(
    query: string,
    limit: number = 10,
    minScore: number = 0.3
  ): Promise<
    Array<{
      path: string;
      title: string;
      score: number;
      excerpt: string;
    }>
  > {
    // Generate embedding for query
    const queryEmbedding = await this.ollama.getEmbedding(query);

    // Search in Qdrant
    const results = await this.qdrant.search(queryEmbedding, limit, minScore);

    return results.map((r) => ({
      path: r.payload.path as string,
      title: r.payload.title as string,
      score: r.score,
      excerpt: (r.payload.excerpt as string) || '',
    }));
  }

  /**
   * Check if services are healthy
   */
  async healthCheck(): Promise<{
    ollama: { healthy: boolean; message: string };
    qdrant: { healthy: boolean; message: string };
  }> {
    const [ollamaHealth, qdrantHealth] = await Promise.all([
      this.ollama.healthCheck(),
      this.qdrant.healthCheck(),
    ]);

    return {
      ollama: ollamaHealth,
      qdrant: qdrantHealth,
    };
  }

  /**
   * Get index statistics
   */
  async getStats(): Promise<IndexStats | null> {
    const info = await this.qdrant.getCollectionInfo();
    if (!info) {
      return null;
    }

    return {
      totalDocuments: (info as { points_count?: number }).points_count || 0,
      lastIndexed: null, // Qdrant doesn't track this
    };
  }

  /**
   * Extract metadata from file
   */
  private extractMetadata(file: TFile, content: string): DocumentMetadata {
    const cache = this.app.metadataCache.getFileCache(file);

    // Extract tags
    const tags: string[] = [];
    if (cache?.tags) {
      tags.push(...cache.tags.map((t) => t.tag));
    }
    if (cache?.frontmatter?.tags) {
      const fmTags = cache.frontmatter.tags;
      if (Array.isArray(fmTags)) {
        tags.push(...fmTags.map((t) => (t.startsWith('#') ? t : `#${t}`)));
      } else if (typeof fmTags === 'string') {
        tags.push(fmTags.startsWith('#') ? fmTags : `#${fmTags}`);
      }
    }

    // Extract aliases
    const aliases: string[] = [];
    if (cache?.frontmatter?.aliases) {
      const fmAliases = cache.frontmatter.aliases;
      if (Array.isArray(fmAliases)) {
        aliases.push(...fmAliases);
      } else if (typeof fmAliases === 'string') {
        aliases.push(fmAliases);
      }
    }

    // Get title from frontmatter or filename
    const title = cache?.frontmatter?.title || file.basename;

    return {
      path: file.path,
      title,
      mtime: file.stat.mtime,
      size: file.stat.size,
      tags: [...new Set(tags)],
      aliases,
    };
  }

  /**
   * Convert file path to a numeric ID for Qdrant
   */
  private pathToId(path: string): number {
    // Simple hash function to convert path to number
    let hash = 0;
    for (let i = 0; i < path.length; i++) {
      const char = path.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }
}
