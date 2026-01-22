export interface DocumentMetadata {
  path: string;
  title: string;
  mtime: number;
  size: number;
  tags?: string[];
  aliases?: string[];
}

export interface SearchResult {
  path: string;
  title: string;
  score: number;
  excerpt?: string;
}

export interface IndexStats {
  totalDocuments: number;
  lastIndexed: number | null;
}
