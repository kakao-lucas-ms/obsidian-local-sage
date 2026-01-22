import { requestUrl } from 'obsidian';

export interface QdrantPoint {
  id: string | number;
  vector: number[];
  payload: Record<string, unknown>;
}

export interface QdrantSearchResult {
  id: string | number;
  score: number;
  payload: Record<string, unknown>;
}

export interface QdrantServiceConfig {
  baseUrl: string;
  collection: string;
}

export class QdrantService {
  private baseUrl: string;
  private collection: string;

  constructor(config: QdrantServiceConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, '');
    this.collection = config.collection;
  }

  /**
   * Search for similar vectors
   */
  async search(
    vector: number[],
    limit: number = 10,
    scoreThreshold: number = 0.0
  ): Promise<QdrantSearchResult[]> {
    const response = await requestUrl({
      url: `${this.baseUrl}/collections/${this.collection}/points/search`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        vector,
        limit,
        score_threshold: scoreThreshold,
        with_payload: true,
      }),
    });

    if (response.status !== 200) {
      throw new Error(`Qdrant search error: ${response.status}`);
    }

    return response.json.result || [];
  }

  /**
   * Upsert points (insert or update)
   */
  async upsert(points: QdrantPoint[]): Promise<void> {
    const response = await requestUrl({
      url: `${this.baseUrl}/collections/${this.collection}/points`,
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        points: points.map((p) => ({
          id: p.id,
          vector: p.vector,
          payload: p.payload,
        })),
      }),
    });

    if (response.status !== 200) {
      throw new Error(`Qdrant upsert error: ${response.status}`);
    }
  }

  /**
   * Delete points by IDs
   */
  async delete(ids: (string | number)[]): Promise<void> {
    const response = await requestUrl({
      url: `${this.baseUrl}/collections/${this.collection}/points/delete`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        points: ids,
      }),
    });

    if (response.status !== 200) {
      throw new Error(`Qdrant delete error: ${response.status}`);
    }
  }

  /**
   * Delete points by filter (e.g., by file path)
   */
  async deleteByFilter(filter: Record<string, unknown>): Promise<void> {
    const response = await requestUrl({
      url: `${this.baseUrl}/collections/${this.collection}/points/delete`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        filter,
      }),
    });

    if (response.status !== 200) {
      throw new Error(`Qdrant delete by filter error: ${response.status}`);
    }
  }

  /**
   * Get collection info
   */
  async getCollectionInfo(): Promise<Record<string, unknown> | null> {
    try {
      const response = await requestUrl({
        url: `${this.baseUrl}/collections/${this.collection}`,
        method: 'GET',
      });

      if (response.status !== 200) {
        return null;
      }

      return response.json.result;
    } catch {
      return null;
    }
  }

  /**
   * Create collection if it doesn't exist
   */
  async ensureCollection(vectorSize: number): Promise<void> {
    const info = await this.getCollectionInfo();
    if (info) {
      return; // Collection exists
    }

    const response = await requestUrl({
      url: `${this.baseUrl}/collections/${this.collection}`,
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        vectors: {
          size: vectorSize,
          distance: 'Cosine',
        },
      }),
    });

    if (response.status !== 200) {
      throw new Error(`Failed to create collection: ${response.status}`);
    }
  }

  /**
   * Check if Qdrant server is reachable and collection exists
   */
  async healthCheck(): Promise<{ healthy: boolean; message: string }> {
    try {
      // Check server is running
      const response = await requestUrl({
        url: `${this.baseUrl}/collections`,
        method: 'GET',
      });

      if (response.status !== 200) {
        return {
          healthy: false,
          message: `Qdrant server returned status ${response.status}`,
        };
      }

      // Check if collection exists
      const collections = response.json?.result?.collections || [];
      const hasCollection = collections.some(
        (c: { name: string }) => c.name === this.collection
      );

      if (!hasCollection) {
        return {
          healthy: false,
          message: `Collection '${this.collection}' not found. Run index first.`,
        };
      }

      return {
        healthy: true,
        message: `Connected to Qdrant with collection '${this.collection}'`,
      };
    } catch (error) {
      return {
        healthy: false,
        message: `Cannot connect to Qdrant: ${error instanceof Error ? error.message : 'Unknown error'}`,
      };
    }
  }

  /**
   * Get all point IDs in the collection
   */
  async getAllPointIds(): Promise<(string | number)[]> {
    const ids: (string | number)[] = [];
    let offset: string | number | null = null;
    const limit = 100;

    while (true) {
      const body: Record<string, unknown> = {
        limit,
        with_payload: false,
        with_vector: false,
      };

      if (offset !== null) {
        body.offset = offset;
      }

      const response = await requestUrl({
        url: `${this.baseUrl}/collections/${this.collection}/points/scroll`,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (response.status !== 200) {
        break;
      }

      const points = response.json?.result?.points || [];
      for (const point of points) {
        ids.push(point.id);
      }

      offset = response.json?.result?.next_page_offset;
      if (!offset) {
        break;
      }
    }

    return ids;
  }

  /**
   * Update service configuration
   */
  updateConfig(config: Partial<QdrantServiceConfig>) {
    if (config.baseUrl) {
      this.baseUrl = config.baseUrl.replace(/\/$/, '');
    }
    if (config.collection) {
      this.collection = config.collection;
    }
  }
}
