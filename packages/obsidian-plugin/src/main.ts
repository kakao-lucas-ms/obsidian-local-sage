import { Plugin, PluginSettingTab, App, Setting, Notice, TFile } from 'obsidian';
import { OllamaService } from './services/ollama';
import { QdrantService } from './services/qdrant';
import { DocumentIndexer } from './services/indexer';
import { LinkSuggestionService } from './services/linkSuggestion';
import { HealthCheckService } from './services/healthCheck';
import { SearchModal } from './ui/SearchModal';
import { JumpModal } from './ui/JumpModal';
import { IndexModal } from './ui/IndexModal';
import { LinkSuggestionModal } from './ui/LinkSuggestionModal';
import { HealthCheckModal } from './ui/HealthCheckModal';

interface SageAISettings {
  ollamaUrl: string;
  ollamaModel: string;
  qdrantUrl: string;
  qdrantCollection: string;
  maxResults: number;
  minScore: number;
}

const DEFAULT_SETTINGS: SageAISettings = {
  ollamaUrl: 'http://127.0.0.1:11434',
  ollamaModel: 'bge-m3',
  qdrantUrl: 'http://127.0.0.1:6333',
  qdrantCollection: 'obsidian_docs',
  maxResults: 8,
  minScore: 0.3,
};

export default class SageAIPlugin extends Plugin {
  settings: SageAISettings;
  private ollama: OllamaService;
  private qdrant: QdrantService;
  private indexer: DocumentIndexer;
  private linkSuggestion: LinkSuggestionService;
  private healthCheck: HealthCheckService;

  async onload() {
    await this.loadSettings();
    this.initializeServices();

    // Add ribbon icon
    this.addRibbonIcon('search', 'Sage AI Search', () => {
      this.openSearchModal();
    });

    // Add command: Semantic Search
    this.addCommand({
      id: 'sage-ai-search',
      name: 'Semantic Search',
      callback: () => {
        this.openSearchModal();
      },
    });

    // Add command: Jump to Document
    this.addCommand({
      id: 'sage-ai-jump',
      name: 'Jump to Document',
      callback: () => {
        new JumpModal(this.app).open();
      },
    });

    // Add command: Rebuild Index
    this.addCommand({
      id: 'sage-ai-reindex',
      name: 'Rebuild Index',
      callback: () => {
        new IndexModal(this.app, this.indexer).open();
      },
    });

    // Add command: Suggest Links
    this.addCommand({
      id: 'sage-ai-suggest-links',
      name: 'Suggest Links for Current Note',
      editorCallback: () => {
        this.openLinkSuggestionModal();
      },
    });

    // Add command: Vault Health Check
    this.addCommand({
      id: 'sage-ai-health-check',
      name: 'Vault Health Check',
      callback: () => {
        new HealthCheckModal(this.app, this.healthCheck).open();
      },
    });

    // Add command: Check Status
    this.addCommand({
      id: 'sage-ai-status',
      name: 'Check Connection Status',
      callback: async () => {
        await this.checkStatus();
      },
    });

    // Add settings tab
    this.addSettingTab(new SageAISettingTab(this.app, this));

  }

  private initializeServices() {
    this.ollama = new OllamaService({
      baseUrl: this.settings.ollamaUrl,
      model: this.settings.ollamaModel,
    });

    this.qdrant = new QdrantService({
      baseUrl: this.settings.qdrantUrl,
      collection: this.settings.qdrantCollection,
    });

    this.indexer = new DocumentIndexer({
      ollama: this.ollama,
      qdrant: this.qdrant,
      app: this.app,
    });

    this.linkSuggestion = new LinkSuggestionService(
      this.app.vault,
      this.ollama,
      this.qdrant
    );

    this.healthCheck = new HealthCheckService(this.app.vault);
  }

  private async openSearchModal() {
    // Quick health check before opening
    const health = await this.indexer.healthCheck();

    if (!health.ollama.healthy) {
      new Notice(`Sage AI: ${health.ollama.message}`);
      return;
    }

    if (!health.qdrant.healthy) {
      new Notice(`Sage AI: ${health.qdrant.message}. Run "Rebuild Index" first.`);
      return;
    }

    new SearchModal(
      this.app,
      this.indexer,
      this.settings.maxResults,
      this.settings.minScore
    ).open();
  }

  private async openLinkSuggestionModal() {
    console.log('[SageAI] Opening Link Suggestion Modal');

    const activeFile = this.app.workspace.getActiveFile();
    console.log('[SageAI] Active file:', activeFile?.path);

    if (!activeFile) {
      console.warn('[SageAI] No active file');
      new Notice('No active file');
      return;
    }

    // Quick health check
    console.log('[SageAI] Performing health check...');
    const health = await this.indexer.healthCheck();
    console.log('[SageAI] Health check result:', health);

    if (!health.ollama.healthy) {
      console.warn('[SageAI] Ollama not healthy:', health.ollama.message);
      new Notice(`Sage AI: ${health.ollama.message}`);
      return;
    }

    if (!health.qdrant.healthy) {
      console.warn('[SageAI] Qdrant not healthy:', health.qdrant.message);
      new Notice(`Sage AI: ${health.qdrant.message}. Run "Rebuild Index" first.`);
      return;
    }

    console.log('[SageAI] Opening modal...');
    new LinkSuggestionModal(
      this.app,
      activeFile,
      this.linkSuggestion
    ).open();
  }

  private async checkStatus() {
    new Notice('Sage AI: Checking connections...');

    try {
      const health = await this.indexer.healthCheck();
      const stats = await this.indexer.getStats();

      let message = 'Sage AI Status:\n';
      message += `\nOllama: ${health.ollama.healthy ? '✓' : '✗'} ${health.ollama.message}`;
      message += `\nQdrant: ${health.qdrant.healthy ? '✓' : '✗'} ${health.qdrant.message}`;

      if (stats) {
        message += `\n\nIndexed documents: ${stats.totalDocuments}`;
      }

      new Notice(message, 10000);
    } catch (error) {
      new Notice(
        `Sage AI: Error checking status - ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  onunload() {
    // Clean up resources if needed
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);

    // Update service configurations
    if (this.ollama) {
      this.ollama.updateConfig({
        baseUrl: this.settings.ollamaUrl,
        model: this.settings.ollamaModel,
      });
    }

    if (this.qdrant) {
      this.qdrant.updateConfig({
        baseUrl: this.settings.qdrantUrl,
        collection: this.settings.qdrantCollection,
      });
    }
  }
}

class SageAISettingTab extends PluginSettingTab {
  plugin: SageAIPlugin;

  constructor(app: App, plugin: SageAIPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;

    containerEl.empty();

    containerEl.createEl('h2', { text: 'Sage AI Settings' });

    // Ollama Settings
    containerEl.createEl('h3', { text: 'Ollama Configuration' });

    new Setting(containerEl)
      .setName('Ollama URL')
      .setDesc('URL of your Ollama server')
      .addText((text) =>
        text
          .setPlaceholder('http://127.0.0.1:11434')
          .setValue(this.plugin.settings.ollamaUrl)
          .onChange(async (value) => {
            this.plugin.settings.ollamaUrl = value;
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName('Embedding Model')
      .setDesc('Ollama model for generating embeddings (bge-m3 recommended)')
      .addText((text) =>
        text
          .setPlaceholder('bge-m3')
          .setValue(this.plugin.settings.ollamaModel)
          .onChange(async (value) => {
            this.plugin.settings.ollamaModel = value;
            await this.plugin.saveSettings();
          })
      );

    // Qdrant Settings
    containerEl.createEl('h3', { text: 'Qdrant Configuration' });

    new Setting(containerEl)
      .setName('Qdrant URL')
      .setDesc('URL of your Qdrant server')
      .addText((text) =>
        text
          .setPlaceholder('http://127.0.0.1:6333')
          .setValue(this.plugin.settings.qdrantUrl)
          .onChange(async (value) => {
            this.plugin.settings.qdrantUrl = value;
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName('Collection Name')
      .setDesc('Qdrant collection name for storing vectors')
      .addText((text) =>
        text
          .setPlaceholder('obsidian_docs')
          .setValue(this.plugin.settings.qdrantCollection)
          .onChange(async (value) => {
            this.plugin.settings.qdrantCollection = value;
            await this.plugin.saveSettings();
          })
      );

    // Search Settings
    containerEl.createEl('h3', { text: 'Search Configuration' });

    new Setting(containerEl)
      .setName('Max Results')
      .setDesc('Maximum number of search results to return')
      .addSlider((slider) =>
        slider
          .setLimits(1, 20, 1)
          .setValue(this.plugin.settings.maxResults)
          .setDynamicTooltip()
          .onChange(async (value) => {
            this.plugin.settings.maxResults = value;
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName('Minimum Score')
      .setDesc('Minimum similarity score for results (0-1)')
      .addSlider((slider) =>
        slider
          .setLimits(0, 1, 0.05)
          .setValue(this.plugin.settings.minScore)
          .setDynamicTooltip()
          .onChange(async (value) => {
            this.plugin.settings.minScore = value;
            await this.plugin.saveSettings();
          })
      );

    // Connection Test
    containerEl.createEl('h3', { text: 'Connection Test' });

    new Setting(containerEl)
      .setName('Test Connections')
      .setDesc('Test connection to Ollama and Qdrant servers')
      .addButton((button) =>
        button.setButtonText('Test').onClick(async () => {
          button.setButtonText('Testing...');
          button.setDisabled(true);

          try {
            const ollama = new OllamaService({
              baseUrl: this.plugin.settings.ollamaUrl,
              model: this.plugin.settings.ollamaModel,
            });
            const qdrant = new QdrantService({
              baseUrl: this.plugin.settings.qdrantUrl,
              collection: this.plugin.settings.qdrantCollection,
            });

            const [ollamaHealth, qdrantHealth] = await Promise.all([
              ollama.healthCheck(),
              qdrant.healthCheck(),
            ]);

            let message = '';
            message += `Ollama: ${ollamaHealth.healthy ? '✓' : '✗'} ${ollamaHealth.message}\n`;
            message += `Qdrant: ${qdrantHealth.healthy ? '✓' : '✗'} ${qdrantHealth.message}`;

            new Notice(message, 8000);
          } catch (error) {
            new Notice(
              `Error: ${error instanceof Error ? error.message : 'Test failed'}`
            );
          } finally {
            button.setButtonText('Test');
            button.setDisabled(false);
          }
        })
      );
  }
}
