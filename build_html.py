"""
BlazeAI v5 - Self-Contained Web UI Builder
Embeds CSS and JS directly into index.html so the UI works seamlessly whether
opened via http://localhost:8000 or directly double-clicked from File Explorer!
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"

css_file = WEB_DIR / "style.css"
js_file = WEB_DIR / "app.js"

with open(css_file, "r", encoding="utf-8") as f:
    css_content = f.read()

with open(js_file, "r", encoding="utf-8") as f:
    js_content = f.read()

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BlazeAI v5 — ShortCodeGuy Studio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
{css_content}
  </style>
</head>
<body>
  <div class="app-layout">
    <!-- Header -->
    <header class="app-header">
      <div class="brand">
        <div class="logo-icon">🔥</div>
        <div class="brand-text">
          <div class="brand-title">
            <span class="brand-name">BlazeAI</span>
            <span class="version-badge">v5</span>
          </div>
          <div class="brand-subtitle">Created by ShortCodeGuy Studio</div>
        </div>
      </div>

      <div class="header-center">
        <div class="model-badge-container">
          <span class="status-dot online"></span>
          <span class="model-badge-label">Model:</span>
          <select id="modelSelector" class="model-select">
            <option value="Qwen/Qwen2.5-0.5B-Instruct" selected>Qwen2.5-0.5B-Instruct (Fast CPU)</option>
            <option value="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B">DeepSeek-R1-Distill-1.5B (Reasoning)</option>
            <option value="HuggingFaceTB/SmolLM2-1.7B-Instruct">SmolLM2-1.7B-Instruct</option>
            <option value="HuggingFaceTB/SmolLM2-360M-Instruct">SmolLM2-360M-Instruct</option>
          </select>
        </div>
      </div>

      <div class="header-actions">
        <button id="btnStats" class="header-btn" title="View System and Session Stats">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 20V10M12 20V4M6 20v-6"/></svg>
          <span>Stats</span>
        </button>
        <button id="btnSettings" class="header-btn" title="Generation Settings">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          <span>Settings</span>
        </button>
        <button id="btnTranscripts" class="header-btn" title="Save or Load Transcripts">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
          <span>Transcripts</span>
        </button>
        <button id="btnClear" class="header-btn danger" title="Clear Conversation">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          <span>Clear</span>
        </button>
      </div>
    </header>

    <!-- Main Chat Window -->
    <main class="chat-main" id="chatContainer">
      <div class="welcome-screen" id="welcomeScreen">
        <div class="welcome-badge">CPU INFERENCE • 100% LOCAL</div>
        <h1 class="welcome-title">BlazeAI <span>v5</span></h1>
        <p class="welcome-subtitle">
          A genuine local AI chatbot powered entirely by language model inference.
          <br />Zero hardcoded answers. Zero canned intelligence.
        </p>

        <div class="specs-grid">
          <div class="spec-card">
            <div class="spec-icon">⚡</div>
            <div class="spec-info">
              <div class="spec-label">Engine</div>
              <div class="spec-value">KV Cache + Streaming</div>
            </div>
          </div>
          <div class="spec-card">
            <div class="spec-icon">🧠</div>
            <div class="spec-info">
              <div class="spec-label">Language Model</div>
              <div class="spec-value" id="currentModelDisplay">Qwen2.5-0.5B-Instruct</div>
            </div>
          </div>
          <div class="spec-card">
            <div class="spec-icon">💻</div>
            <div class="spec-info">
              <div class="spec-label">Hardware Profile</div>
              <div class="spec-value">Intel i3-1215U • 8GB RAM</div>
            </div>
          </div>
        </div>

        <div class="prompt-suggestions">
          <div class="suggestion-title">Try asking an unanticipated question:</div>
          <div class="suggestions-list">
            <button class="suggestion-btn" data-prompt="Why do stars twinkle in the night sky?">
              "Why do stars twinkle in the night sky?"
            </button>
            <button class="suggestion-btn" data-prompt="Explain how noise-canceling headphones work in simple terms.">
              "Explain how noise-canceling headphones work."
            </button>
            <button class="suggestion-btn" data-prompt="Write a concise Python function to check if a string is a palindrome.">
              "Write a concise Python function for palindromes."
            </button>
          </div>
        </div>
      </div>

      <!-- Messages list -->
      <div class="messages-list" id="messagesList"></div>
    </main>

    <!-- Input Footer -->
    <footer class="app-footer">
      <div class="input-container">
        <textarea
          id="userInput"
          rows="1"
          placeholder="Ask BlazeAI anything... (Press Enter to send, Shift+Enter for newline)"
          autocomplete="off"
        ></textarea>
        <button id="btnSend" class="send-btn" title="Send Message">
          <svg id="sendIcon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
          <div id="loadingSpinner" class="spinner hidden"></div>
        </button>
      </div>
      <div class="footer-note">
        BlazeAI v5 runs locally on CPU with zero cloud APIs. Created by <strong>ShortCodeGuy Studio</strong>.
      </div>
    </footer>
  </div>

  <!-- Settings Modal -->
  <div class="modal-backdrop hidden" id="settingsModal">
    <div class="modal-card">
      <div class="modal-header">
        <h3>Generation Settings</h3>
        <button class="close-modal-btn" data-target="settingsModal">&times;</button>
      </div>
      <div class="modal-body">
        <div class="setting-item">
          <div class="setting-label-row">
            <label for="settingTemp">Temperature</label>
            <span id="tempValue" class="slider-val">0.7</span>
          </div>
          <input type="range" id="settingTemp" min="0.1" max="1.5" step="0.05" value="0.7">
          <div class="setting-desc">Controls randomness. Lower values are more deterministic.</div>
        </div>

        <div class="setting-item">
          <div class="setting-label-row">
            <label for="settingTopP">Top-P (Nucleus)</label>
            <span id="topPValue" class="slider-val">0.9</span>
          </div>
          <input type="range" id="settingTopP" min="0.1" max="1.0" step="0.05" value="0.9">
          <div class="setting-desc">Cumulative probability cutoff for token sampling.</div>
        </div>

        <div class="setting-item">
          <div class="setting-label-row">
            <label for="settingMaxTokens">Max New Tokens</label>
            <span id="maxTokensValue" class="slider-val">512</span>
          </div>
          <input type="range" id="settingMaxTokens" min="64" max="1024" step="32" value="512">
          <div class="setting-desc">Maximum output length per model generation.</div>
        </div>

        <div class="setting-item">
          <div class="setting-label-row">
            <label for="settingRepPenalty">Repetition Penalty</label>
            <span id="repPenaltyValue" class="slider-val">1.1</span>
          </div>
          <input type="range" id="settingRepPenalty" min="1.0" max="1.5" step="0.05" value="1.1">
          <div class="setting-desc">Penalizes token repetition to encourage varied vocabulary.</div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn secondary" data-target="settingsModal">Close</button>
        <button id="btnSaveSettings" class="btn primary">Apply Settings</button>
      </div>
    </div>
  </div>

  <!-- Stats Modal -->
  <div class="modal-backdrop hidden" id="statsModal">
    <div class="modal-card">
      <div class="modal-header">
        <h3>Session Diagnostics & RAM</h3>
        <button class="close-modal-btn" data-target="statsModal">&times;</button>
      </div>
      <div class="modal-body">
        <div class="stats-grid">
          <div class="stat-box">
            <div class="stat-number" id="statTurns">0</div>
            <div class="stat-name">Conversation Turns</div>
          </div>
          <div class="stat-box">
            <div class="stat-number" id="statTokens">0</div>
            <div class="stat-name">Tokens Produced</div>
          </div>
          <div class="stat-box">
            <div class="stat-number" id="statAvgSpeed">0.0</div>
            <div class="stat-name">Avg Speed (tok/s)</div>
          </div>
          <div class="stat-box">
            <div class="stat-number" id="statAvgTTFT">0</div>
            <div class="stat-name">Avg TTFT (ms)</div>
          </div>
        </div>

        <div class="memory-section">
          <div class="memory-title">Memory Allocation</div>
          <div class="memory-row">
            <span>Process RAM (RSS):</span>
            <strong id="statProcRam">-- MB</strong>
          </div>
          <div class="memory-row">
            <span>System RAM Used:</span>
            <strong id="statSysRam">-- / -- MB</strong>
          </div>
          <div class="progress-bar-container">
            <div class="progress-bar-fill" id="statRamBar" style="width: 0%"></div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn primary" data-target="statsModal">Done</button>
      </div>
    </div>
  </div>

  <!-- Transcripts Modal -->
  <div class="modal-backdrop hidden" id="transcriptsModal">
    <div class="modal-card">
      <div class="modal-header">
        <h3>Saved Transcripts</h3>
        <button class="close-modal-btn" data-target="transcriptsModal">&times;</button>
      </div>
      <div class="modal-body">
        <div class="save-box">
          <input type="text" id="saveFilenameInput" placeholder="Enter filename (e.g. research_chat)" />
          <button id="btnSaveTranscript" class="btn primary">Save Current Chat</button>
        </div>
        <div class="transcripts-list-title">Saved Sessions in data/:</div>
        <div class="transcripts-list" id="transcriptsList">
          <div class="empty-list">No saved transcripts found.</div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn secondary" data-target="transcriptsModal">Close</button>
      </div>
    </div>
  </div>

  <script>
{js_content}
  </script>
</body>
</html>
"""

# Write to web/index.html
index_file = WEB_DIR / "index.html"
with open(index_file, "w", encoding="utf-8") as f:
    f.write(html_content)

# Also write to root BlazeAI_Web.html for easy double-clicking
root_html = BASE_DIR / "BlazeAI_Web.html"
with open(root_html, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Generated {index_file} ({len(html_content)} bytes)")
print(f"Generated {root_html} ({len(html_content)} bytes)")
