import { Plugin, PluginSettingTab, App, Setting, Notice } from 'obsidian';

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

  async onload() {
    await this.loadSettings();

    // Add ribbon icon
    this.addRibbonIcon('search', 'Sage AI Search', () => {
      new Notice('Sage AI: Search coming soon!');
    });

    // Add command: Semantic Search
    this.addCommand({
      id: 'sage-ai-search',
      name: 'Semantic Search',
      callback: () => {
        new Notice('Sage AI: Semantic Search - Coming Soon!');
      },
    });

    // Add command: Jump to Document
    this.addCommand({
      id: 'sage-ai-jump',
      name: 'Jump to Document',
      callback: () => {
        new Notice('Sage AI: Jump to Document - Coming Soon!');
      },
    });

    // Add command: Rebuild Index
    this.addCommand({
      id: 'sage-ai-reindex',
      name: 'Rebuild Index',
      callback: () => {
        new Notice('Sage AI: Rebuild Index - Coming Soon!');
      },
    });

    // Add settings tab
    this.addSettingTab(new SageAISettingTab(this.app, this));

    console.log('Sage AI plugin loaded');
  }

  onunload() {
    console.log('Sage AI plugin unloaded');
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
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
      .setDesc('Ollama model for generating embeddings')
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

    // Test Connection Button
    containerEl.createEl('h3', { text: 'Connection Test' });

    new Setting(containerEl)
      .setName('Test Connections')
      .setDesc('Test connection to Ollama and Qdrant servers')
      .addButton((button) =>
        button.setButtonText('Test').onClick(async () => {
          new Notice('Testing connections... (Coming Soon)');
        })
      );
  }
}
