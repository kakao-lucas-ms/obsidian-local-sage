import { requestUrl } from 'obsidian';

export interface OllamaEmbeddingResponse {
  embedding: number[];
}

export interface OllamaServiceConfig {
  baseUrl: string;
  model: string;
}

export class OllamaService {
  private baseUrl: string;
  private model: string;

  constructor(config: OllamaServiceConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, '');
    this.model = config.model;
  }

  /**
   * Generate embeddings for the given text
   */
  async getEmbedding(text: string): Promise<number[]> {
    const response = await requestUrl({
      url: `${this.baseUrl}/api/embeddings`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: this.model,
        prompt: text,
      }),
    });

    if (response.status !== 200) {
      throw new Error(`Ollama API error: ${response.status}`);
    }

    const data = response.json as OllamaEmbeddingResponse;
    return data.embedding;
  }

  /**
   * Generate embeddings for multiple texts in batch
   */
  async getEmbeddings(texts: string[]): Promise<number[][]> {
    const embeddings: number[][] = [];
    for (const text of texts) {
      const embedding = await this.getEmbedding(text);
      embeddings.push(embedding);
    }
    return embeddings;
  }

  /**
   * Check if Ollama server is reachable and the model is available
   */
  async healthCheck(): Promise<{ healthy: boolean; message: string }> {
    try {
      // Check server is running
      const tagsResponse = await requestUrl({
        url: `${this.baseUrl}/api/tags`,
        method: 'GET',
      });

      if (tagsResponse.status !== 200) {
        return {
          healthy: false,
          message: `Ollama server returned status ${tagsResponse.status}`,
        };
      }

      // Check if model is available
      const models = tagsResponse.json?.models || [];
      const modelNames = models.map((m: { name: string }) => m.name);
      const hasModel = modelNames.some(
        (name: string) =>
          name === this.model || name.startsWith(`${this.model}:`)
      );

      if (!hasModel) {
        return {
          healthy: false,
          message: `Model '${this.model}' not found. Available: ${modelNames.join(', ')}`,
        };
      }

      return {
        healthy: true,
        message: `Connected to Ollama with model '${this.model}'`,
      };
    } catch (error) {
      return {
        healthy: false,
        message: `Cannot connect to Ollama: ${error instanceof Error ? error.message : 'Unknown error'}`,
      };
    }
  }

  /**
   * Update service configuration
   */
  updateConfig(config: Partial<OllamaServiceConfig>) {
    if (config.baseUrl) {
      this.baseUrl = config.baseUrl.replace(/\/$/, '');
    }
    if (config.model) {
      this.model = config.model;
    }
  }
}
