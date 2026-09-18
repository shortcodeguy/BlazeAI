/**
 * BlazeAI v5 - Frontend Application Logic
 * Created by ShortCodeGuy Studio
 *
 * Real-time SSE streaming client, markdown parser, model & telemetry manager.
 */

// Dynamically determine backend base URL.
// If the user opens index.html directly from file explorer (file://), fallback to http://127.0.0.1:8000
const API_BASE =
  window.location.protocol === "file:" || !window.location.origin.startsWith("http")
    ? "http://127.0.0.1:8000"
    : "";

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const chatContainer = document.getElementById("chatContainer");
  const messagesList = document.getElementById("messagesList");
  const welcomeScreen = document.getElementById("welcomeScreen");
  const userInput = document.getElementById("userInput");
  const btnSend = document.getElementById("btnSend");
  const sendIcon = document.getElementById("sendIcon");
  const loadingSpinner = document.getElementById("loadingSpinner");
  const modelSelector = document.getElementById("modelSelector");
  const currentModelDisplay = document.getElementById("currentModelDisplay");
  const statusDot = document.querySelector(".status-dot");

  // Modals & Buttons
  const btnClear = document.getElementById("btnClear");
  const btnStats = document.getElementById("btnStats");
  const btnSettings = document.getElementById("btnSettings");
  const btnTranscripts = document.getElementById("btnTranscripts");

  const settingsModal = document.getElementById("settingsModal");
  const statsModal = document.getElementById("statsModal");
  const transcriptsModal = document.getElementById("transcriptsModal");

  // Settings inputs
  const settingTemp = document.getElementById("settingTemp");
  const tempValue = document.getElementById("tempValue");
  const settingTopP = document.getElementById("settingTopP");
  const topPValue = document.getElementById("topPValue");
  const settingMaxTokens = document.getElementById("settingMaxTokens");
  const maxTokensValue = document.getElementById("maxTokensValue");
  const settingRepPenalty = document.getElementById("settingRepPenalty");
  const repPenaltyValue = document.getElementById("repPenaltyValue");
  const btnSaveSettings = document.getElementById("btnSaveSettings");

  // Stats elements
  const statTurns = document.getElementById("statTurns");
  const statTokens = document.getElementById("statTokens");
  const statAvgSpeed = document.getElementById("statAvgSpeed");
  const statAvgTTFT = document.getElementById("statAvgTTFT");
  const statProcRam = document.getElementById("statProcRam");
  const statSysRam = document.getElementById("statSysRam");
  const statRamBar = document.getElementById("statRamBar");

  // Transcripts elements
  const saveFilenameInput = document.getElementById("saveFilenameInput");
  const btnSaveTranscript = document.getElementById("btnSaveTranscript");
  const transcriptsList = document.getElementById("transcriptsList");

  let isGenerating = false;

  // Auto-resize textarea
  userInput.addEventListener("input", () => {
    userInput.style.height = "auto";
    userInput.style.height = Math.min(userInput.scrollHeight, 160) + "px";
  });

  // Prompt suggestions
  document.querySelectorAll(".suggestion-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      userInput.value = btn.getAttribute("data-prompt");
      userInput.focus();
      sendMessage();
    });
  });

  // Modal helpers
  function openModal(modal) {
    modal.classList.remove("hidden");
  }

  function closeModal(modal) {
    modal.classList.add("hidden");
  }

  document.querySelectorAll(".close-modal-btn, [data-target]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-target");
      const target = document.getElementById(targetId);
      if (target) closeModal(target);
    });
  });

  // Check Backend Health on load
  async function checkBackendHealth() {
    try {
      const res = await fetch(`${API_BASE}/api/health`);
      if (res.ok) {
        const data = await res.json();
        statusDot.className = "status-dot online";
        statusDot.title = "Connected to BlazeAI backend";
        if (data.active_model) {
          currentModelDisplay.textContent = data.active_model.split("/").pop();
          if (modelSelector) modelSelector.value = data.active_model;
        }
      } else {
        throw new Error(`HTTP ${res.status}`);
      }
    } catch (e) {
      statusDot.className = "status-dot loading";
      statusDot.title = "Cannot reach BlazeAI backend";
      showOfflineBanner();
    }
  }

  function showOfflineBanner() {
    if (document.getElementById("offlineBanner")) return;
    const banner = document.createElement("div");
    banner.id = "offlineBanner";
    banner.style.cssText =
      "background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; color: #fca5a5; padding: 10px 16px; border-radius: 8px; margin: 12px 24px; font-size: 13px; text-align: center;";
    banner.innerHTML =
      "⚠️ <strong>BlazeAI backend server is not reachable.</strong> Please start the backend by running <code>run_web.bat</code> or <code>python server.py</code> in the <code>BlazeAI v5</code> folder.";
    const header = document.querySelector(".app-header");
    header.insertAdjacentElement("afterend", banner);
  }

  // Load Settings
  async function loadSettings() {
    try {
      const res = await fetch(`${API_BASE}/api/settings`);
      if (!res.ok) return;
      const data = await res.json();
      settingTemp.value = data.temperature;
      tempValue.textContent = data.temperature;
      settingTopP.value = data.top_p;
      topPValue.textContent = data.top_p;
      settingMaxTokens.value = data.max_new_tokens;
      maxTokensValue.textContent = data.max_new_tokens;
      settingRepPenalty.value = data.repetition_penalty;
      repPenaltyValue.textContent = data.repetition_penalty;
    } catch (e) {
      console.warn("Could not load settings:", e);
    }
  }

  // Update slider text
  settingTemp.addEventListener("input", () => (tempValue.textContent = settingTemp.value));
  settingTopP.addEventListener("input", () => (topPValue.textContent = settingTopP.value));
  settingMaxTokens.addEventListener("input", () => (maxTokensValue.textContent = settingMaxTokens.value));
  settingRepPenalty.addEventListener("input", () => (repPenaltyValue.textContent = settingRepPenalty.value));

  btnSaveSettings.addEventListener("click", async () => {
    const payload = {
      temperature: parseFloat(settingTemp.value),
      top_p: parseFloat(settingTopP.value),
      max_new_tokens: parseInt(settingMaxTokens.value, 10),
      repetition_penalty: parseFloat(settingRepPenalty.value),
    };
    try {
      await fetch(`${API_BASE}/api/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      closeModal(settingsModal);
    } catch (e) {
      alert("Failed to save settings: " + e.message);
    }
  });

  btnSettings.addEventListener("click", () => {
    loadSettings();
    openModal(settingsModal);
  });

  // Load Stats
  async function loadStats() {
    try {
      const res = await fetch(`${API_BASE}/api/stats`);
      if (!res.ok) return;
      const data = await res.json();
      statTurns.textContent = data.total_turns;
      statTokens.textContent = data.total_tokens_produced;
      statAvgSpeed.textContent = data.avg_speed_tok_s;
      statAvgTTFT.textContent = data.avg_ttft_ms;
      statProcRam.textContent = `${data.process_ram_mb} MB`;
      statSysRam.textContent = `${Math.round(data.system_ram_used_mb)} / ${Math.round(data.system_ram_total_mb)} MB (${data.system_ram_percent}%)`;
      statRamBar.style.width = `${data.system_ram_percent}%`;
    } catch (e) {
      console.warn("Could not load stats:", e);
    }
  }

  btnStats.addEventListener("click", () => {
    loadStats();
    openModal(statsModal);
  });

  // Clear Conversation
  btnClear.addEventListener("click", async () => {
    if (confirm("Clear current conversation history?")) {
      try {
        await fetch(`${API_BASE}/api/clear`, { method: "POST" });
        messagesList.innerHTML = "";
        welcomeScreen.classList.remove("hidden");
      } catch (e) {
        alert("Failed to clear chat: " + e.message);
      }
    }
  });

  // Model switching
  modelSelector.addEventListener("change", async () => {
    const newModel = modelSelector.value;
    statusDot.className = "status-dot loading";
    currentModelDisplay.textContent = newModel.split("/").pop();

    try {
      const res = await fetch(`${API_BASE}/api/model/switch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_id: newModel }),
      });
      if (!res.ok) throw new Error("Switch failed");
      const data = await res.json();
      statusDot.className = "status-dot online";
      alert(`Successfully loaded ${newModel} in ${data.load_time_sec}s`);
    } catch (e) {
      alert("Failed to switch model: " + e.message);
      statusDot.className = "status-dot online";
    }
  });

  // Transcripts
  async function loadTranscriptsList() {
    try {
      const res = await fetch(`${API_BASE}/api/transcripts`);
      if (!res.ok) return;
      const data = await res.json();
      transcriptsList.innerHTML = "";
      if (data.transcripts.length === 0) {
        transcriptsList.innerHTML = '<div class="empty-list">No saved transcripts found.</div>';
        return;
      }
      data.transcripts.forEach((file) => {
        const item = document.createElement("div");
        item.className = "transcript-item";
        item.innerHTML = `
          <span class="transcript-name">${file}</span>
          <button class="transcript-load-btn" data-filename="${file}">Restore</button>
        `;
        transcriptsList.appendChild(item);
      });

      document.querySelectorAll(".transcript-load-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const fn = btn.getAttribute("data-filename");
          await restoreTranscript(fn);
        });
      });
    } catch (e) {
      console.warn("Could not list transcripts:", e);
    }
  }

  async function restoreTranscript(filename) {
    try {
      const res = await fetch(`${API_BASE}/api/load`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename }),
      });
      if (!res.ok) throw new Error("Could not load transcript");
      const data = await res.json();

      messagesList.innerHTML = "";
      welcomeScreen.classList.add("hidden");
      data.history.forEach((turn) => {
        renderMessageBubble(turn.role, turn.content);
      });
      closeModal(transcriptsModal);
      scrollToBottom();
    } catch (e) {
      alert("Error restoring transcript: " + e.message);
    }
  }

  btnSaveTranscript.addEventListener("click", async () => {
    const filename = saveFilenameInput.value.trim();
    try {
      const res = await fetch(`${API_BASE}/api/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: filename || null }),
      });
      if (!res.ok) throw new Error("Failed to save transcript");
      const data = await res.json();
      alert(`Transcript saved: ${data.filename}`);
      saveFilenameInput.value = "";
      loadTranscriptsList();
    } catch (e) {
      alert("Error saving: " + e.message);
    }
  });

  btnTranscripts.addEventListener("click", () => {
    loadTranscriptsList();
    openModal(transcriptsModal);
  });

  // Markdown formatter
  function formatMarkdown(text) {
    if (!text) return "";
    let raw = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Code blocks ```code```
    raw = raw.replace(/```([\s\S]*?)```/g, (match, code) => {
      return `<pre><code>${code.trim()}</code></pre>`;
    });

    // Inline code `code`
    raw = raw.replace(/`([^`]+)`/g, "<code>$1</code>");

    // Bold **text**
    raw = raw.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

    // Italic *text*
    raw = raw.replace(/\*([^*]+)\*/g, "<em>$1</em>");

    // Bullet points
    raw = raw.replace(/^\s*[-*]\s+(.+)$/gm, "<li>$1</li>");
    raw = raw.replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>");

    // Paragraphs
    const paragraphs = raw.split(/\n\n+/);
    return paragraphs
      .map((p) => {
        if (p.startsWith("<pre>") || p.startsWith("<ul>")) return p;
        return `<p>${p.replace(/\n/g, "<br/>")}</p>`;
      })
      .join("");
  }

  function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  function renderMessageBubble(role, content, metrics = null) {
    const row = document.createElement("div");
    row.className = `message-row ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.innerHTML = role === "user" ? "👤" : "🔥";

    const wrapper = document.createElement("div");
    wrapper.className = "message-content-wrapper";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.innerHTML = role === "user" ? escapeHtml(content) : formatMarkdown(content);

    wrapper.appendChild(bubble);

    if (metrics && role === "assistant") {
      const badge = document.createElement("div");
      badge.className = "telemetry-badge";
      badge.innerHTML = `
        <span class="telemetry-item">⏱️ TTFT: <strong>${metrics.ttft_ms}ms</strong></span>
        <span class="telemetry-item">⚡ Speed: <strong>${metrics.speed_tok_s} tok/s</strong></span>
        <span class="telemetry-item">📊 Tokens: <strong>${metrics.generated_tokens}</strong></span>
        <span class="telemetry-item">💾 RAM: <strong>${metrics.process_ram_mb} MB</strong></span>
      `;
      wrapper.appendChild(badge);
    }

    row.appendChild(avatar);
    row.appendChild(wrapper);
    messagesList.appendChild(row);
    scrollToBottom();
    return bubble;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\n/g, "<br/>");
  }

  // Send message with streaming SSE
  async function sendMessage() {
    const text = userInput.value.trim();
    if (!text || isGenerating) return;

    isGenerating = true;
    welcomeScreen.classList.add("hidden");
    userInput.value = "";
    userInput.style.height = "auto";

    // Disable send button and show spinner
    btnSend.disabled = true;
    sendIcon.classList.add("hidden");
    loadingSpinner.classList.remove("hidden");

    // Render user message bubble
    renderMessageBubble("user", text);

    // Prepare assistant message bubble with thinking status
    const row = document.createElement("div");
    row.className = "message-row assistant";

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.innerHTML = "🔥";

    const wrapper = document.createElement("div");
    wrapper.className = "message-content-wrapper";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble streaming-cursor";
    bubble.innerHTML = `<span style="color: var(--text-muted); font-style: italic;">Thinking & generating response on CPU...</span>`;

    wrapper.appendChild(bubble);
    row.appendChild(avatar);
    row.appendChild(wrapper);
    messagesList.appendChild(row);
    scrollToBottom();

    let fullGeneratedText = "";
    let metricsData = null;
    let hadError = false;
    let firstTokenReceived = false;

    try {
      const response = await fetch(`${API_BASE}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      if (!response.ok) {
        throw new Error(`Server responded with HTTP status ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // keep partial line

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data: ")) continue;
          const jsonStr = trimmed.slice(6);
          try {
            const event = JSON.parse(jsonStr);
            if (event.type === "token") {
              if (!firstTokenReceived) {
                firstTokenReceived = true;
                bubble.innerHTML = "";
              }
              fullGeneratedText += event.content;
              bubble.innerHTML = formatMarkdown(fullGeneratedText);
              scrollToBottom();
            } else if (event.type === "metrics") {
              metricsData = event.data;
            } else if (event.type === "error") {
              hadError = true;
              bubble.innerHTML += `<br/><span style="color:#ef4444; font-weight:600;">[Model Error: ${escapeHtml(event.message)}]</span>`;
            }
          } catch (err) {
            console.error("SSE parse error:", err);
          }
        }
      }
    } catch (err) {
      hadError = true;
      bubble.innerHTML = `
        <div style="color: #ef4444; padding: 4px 0;">
          <strong>⚠️ Unable to reach BlazeAI backend server.</strong><br/>
          <span style="font-size: 13px; color: var(--text-secondary);">
            Please make sure the backend server is running.<br/>
            Run <code>run_web.bat</code> or execute <code>python server.py</code> in your terminal.<br/>
            <em>Details: ${escapeHtml(err.message)}</em>
          </span>
        </div>`;
    } finally {
      bubble.classList.remove("streaming-cursor");

      if (!hadError && fullGeneratedText) {
        bubble.innerHTML = formatMarkdown(fullGeneratedText);
      } else if (!hadError && !fullGeneratedText) {
        bubble.innerHTML = `<span style="color: var(--text-muted); font-style: italic;">No tokens generated by the model.</span>`;
      }

      // Add metrics badge if available
      if (metricsData) {
        const badge = document.createElement("div");
        badge.className = "telemetry-badge";
        badge.innerHTML = `
          <span class="telemetry-item">⏱️ TTFT: <strong>${metricsData.ttft_ms}ms</strong></span>
          <span class="telemetry-item">⚡ Speed: <strong>${metricsData.speed_tok_s} tok/s</strong></span>
          <span class="telemetry-item">📊 Tokens: <strong>${metricsData.generated_tokens}</strong></span>
          <span class="telemetry-item">💾 RAM: <strong>${metricsData.process_ram_mb} MB</strong></span>
        `;
        wrapper.appendChild(badge);
      }

      isGenerating = false;
      btnSend.disabled = false;
      sendIcon.classList.remove("hidden");
      loadingSpinner.classList.add("hidden");
      userInput.focus();
      scrollToBottom();
    }
  }

  // Event Listeners
  btnSend.addEventListener("click", sendMessage);

  userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Initial startup checks
  checkBackendHealth();
  loadSettings();
});
