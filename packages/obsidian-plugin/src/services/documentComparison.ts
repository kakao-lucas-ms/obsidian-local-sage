import { TFile, Vault } from 'obsidian';
import { OllamaService } from './ollama';

export interface DocumentMetadata {
  title: string;
  headings: string[];
  tags: string[];
  links: string[];
  wordCount: number;
  lines: number;
}

export interface ContentComparison {
  similarityRatio: number;
  commonLines: number;
  totalLines: number;
}

export interface ComparisonResult {
  file1: TFile;
  file2: TFile;
  meta1: DocumentMetadata;
  meta2: DocumentMetadata;
  semanticSimilarity: number;
  contentComparison: ContentComparison;
  commonTags: string[];
  commonLinks: string[];
  commonKeywords: string[];
  uniqueKeywords1: string[];
  uniqueKeywords2: string[];
  suggestions: string[];
}

export class DocumentComparisonService {
  constructor(
    private vault: Vault,
    private ollama: OllamaService
  ) {}

  /**
   * Extract metadata from document content
   */
  private extractMetadata(content: string): DocumentMetadata {
    const lines = content.split('\n');

    // Title (first h1)
    let title = 'Untitled';
    for (const line of lines) {
      if (line.startsWith('# ')) {
        title = line.substring(2).trim();
        break;
      }
    }

    // Headings (h2+)
    const headings: string[] = [];
    for (const line of lines) {
      if (line.startsWith('##')) {
        const h = line.replace(/^#+\s*/, '').trim();
        if (h) {
          headings.push(h);
        }
      }
    }

    // Tags
    const tagMatches = content.matchAll(/#(\w+)/g);
    const tags = Array.from(new Set(Array.from(tagMatches, m => m[1])));

    // Links
    const linkMatches = content.matchAll(/\[\[([^\]]+)\]\]/g);
    const links = Array.from(new Set(Array.from(linkMatches, m => m[1])));

    // Word count
    const wordCount = content.split(/\s+/).filter(w => w.length > 0).length;

    return {
      title,
      headings,
      tags,
      links,
      wordCount,
      lines: lines.length,
    };
  }

  /**
   * Calculate cosine similarity between two vectors
   */
  private cosineSimilarity(vec1: number[], vec2: number[]): number {
    if (!vec1 || !vec2 || vec1.length === 0 || vec2.length === 0) {
      return 0.0;
    }

    let dotProduct = 0;
    let magnitude1 = 0;
    let magnitude2 = 0;

    for (let i = 0; i < vec1.length; i++) {
      dotProduct += vec1[i] * vec2[i];
      magnitude1 += vec1[i] * vec1[i];
      magnitude2 += vec2[i] * vec2[i];
    }

    magnitude1 = Math.sqrt(magnitude1);
    magnitude2 = Math.sqrt(magnitude2);

    if (magnitude1 === 0 || magnitude2 === 0) {
      return 0.0;
    }

    return dotProduct / (magnitude1 * magnitude2);
  }

  /**
   * Extract key phrases from content
   */
  private extractKeyPhrases(content: string): [string, number][] {
    // Remove markdown syntax
    const text = content.replace(/[#*`\[\]()]/g, '');
    const words = text.toLowerCase().split(/\s+/);

    // Stop words
    const stopWords = new Set([
      'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
      'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
      'been', 'being', 'this', 'that', 'these', 'those', 'it', 'its',
      '이', '그', '저', '것', '수', '등', '및', '를', '을', '가', '이',
    ]);

    // Filter and count
    const filtered = words.filter(w => w.length > 2 && !stopWords.has(w));
    const counter = new Map<string, number>();

    for (const word of filtered) {
      counter.set(word, (counter.get(word) || 0) + 1);
    }

    // Sort by frequency
    const sorted = Array.from(counter.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 15);

    return sorted;
  }

  /**
   * Compare content using sequence matching
   */
  private compareContent(content1: string, content2: string): ContentComparison {
    const lines1 = content1.split('\n');
    const lines2 = content2.split('\n');

    // Simple line-based comparison
    const set1 = new Set(lines1.map(l => l.trim()).filter(l => l.length > 0));
    const set2 = new Set(lines2.map(l => l.trim()).filter(l => l.length > 0));

    const commonLines = Array.from(set1).filter(line => set2.has(line)).length;
    const totalLines = Math.max(set1.size, set2.size);
    const similarityRatio = totalLines > 0 ? commonLines / totalLines : 0;

    return {
      similarityRatio,
      commonLines,
      totalLines,
    };
  }

  /**
   * Generate suggestions based on comparison results
   */
  private generateSuggestions(
    similarity: number,
    commonTags: string[],
    file1: TFile,
    file2: TFile
  ): string[] {
    const suggestions: string[] = [];

    if (similarity > 0.7) {
      suggestions.push('문서가 매우 유사합니다. 하나로 합치는 것을 고려하세요');
      suggestions.push('또는 하나를 다른 하나의 하위 문서로 재구성하세요');
    } else if (similarity > 0.4) {
      suggestions.push('관련된 내용이 있습니다. 상호 참조 링크를 추가하세요');
      suggestions.push(`예: [[${file1.basename}]], [[${file2.basename}]]`);
    } else {
      suggestions.push('서로 다른 주제를 다루고 있습니다');
      suggestions.push('하나의 MOC(Map of Content)로 연결할 수 있습니다');
    }

    if (commonTags.length > 0) {
      suggestions.push(`공통 태그 ${commonTags.length}개로 연결되어 있습니다`);
    }

    return suggestions;
  }

  /**
   * Compare two documents
   */
  async compareDocuments(file1: TFile, file2: TFile): Promise<ComparisonResult> {
    try {
      console.log('[DocumentComparison] Comparing:', file1.path, 'vs', file2.path);

      // Read documents
      const content1 = await this.vault.cachedRead(file1);
      const content2 = await this.vault.cachedRead(file2);

      // Extract metadata
      const meta1 = this.extractMetadata(content1);
      const meta2 = this.extractMetadata(content2);

      console.log('[DocumentComparison] Metadata extracted');

      // Semantic similarity
      let semanticSimilarity = 0;
      try {
        console.log('[DocumentComparison] Getting embeddings...');
        const emb1 = await this.ollama.getEmbedding(content1.substring(0, 2000));
        const emb2 = await this.ollama.getEmbedding(content2.substring(0, 2000));
        semanticSimilarity = this.cosineSimilarity(emb1, emb2);
        console.log('[DocumentComparison] Semantic similarity:', semanticSimilarity);
      } catch (error) {
        console.error('[DocumentComparison] Error calculating similarity:', error);
        // Continue without semantic similarity
      }

      // Content comparison
      const contentComparison = this.compareContent(content1, content2);

      // Common elements
      const commonTags = meta1.tags.filter(t => meta2.tags.includes(t));
      const commonLinks = meta1.links.filter(l => meta2.links.includes(l));

      // Key phrases
      const phrases1 = this.extractKeyPhrases(content1);
      const phrases2 = this.extractKeyPhrases(content2);

      const words1 = new Set(phrases1.map(p => p[0]));
      const words2 = new Set(phrases2.map(p => p[0]));

      const commonKeywords = Array.from(words1).filter(w => words2.has(w)).slice(0, 10);
      const uniqueKeywords1 = phrases1
        .filter(p => !words2.has(p[0]))
        .slice(0, 5)
        .map(p => p[0]);
      const uniqueKeywords2 = phrases2
        .filter(p => !words1.has(p[0]))
        .slice(0, 5)
        .map(p => p[0]);

      // Generate suggestions
      const suggestions = this.generateSuggestions(
        semanticSimilarity,
        commonTags,
        file1,
        file2
      );

      console.log('[DocumentComparison] Comparison complete');

      return {
        file1,
        file2,
        meta1,
        meta2,
        semanticSimilarity,
        contentComparison,
        commonTags,
        commonLinks,
        commonKeywords,
        uniqueKeywords1,
        uniqueKeywords2,
        suggestions,
      };
    } catch (error) {
      console.error('[DocumentComparison] Error comparing documents:', error);
      throw error;
    }
  }
}
