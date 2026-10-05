(() => {
  "use strict";

  const el = {
    headerStatus: document.getElementById("header-status"),
    themeToggle: document.getElementById("theme-toggle"),
    form: document.getElementById("question-form"),
    input: document.getElementById("question-input"),
    submitBtn: document.getElementById("submit-btn"),
    configHint: document.getElementById("config-hint"),
    chips: document.getElementById("example-chips"),
    feed: document.getElementById("activity-feed"),
    feedEmpty: document.getElementById("activity-empty"),
    pipeline: document.getElementById("pipeline-track"),
    runStatus: document.getElementById("run-status"),
    runElapsed: document.getElementById("run-elapsed"),
    consoleLink: document.getElementById("console-link"),
    outputsCard: document.getElementById("outputs-card"),
    outputsList: document.getElementById("outputs-list"),
    overlay: document.getElementById("approval-overlay"),
    approvalTitle: document.getElementById("approval-title"),
    approvalQuestion: document.getElementById("approval-question"),
    approvalSummary: document.getElementById("approval-summary"),
    approvalDraft: document.getElementById("approval-draft"),
    approvalNotes: document.getElementById("approval-notes"),
    approvalError: document.getElementById("approval-error"),
    approveBtn: document.getElementById("approval-approve"),
    rejectBtn: document.getElementById("approval-reject"),
    similarCard: document.getElementById("similar-card"),
    similarDate: document.getElementById("similar-date"),
    similarTopic: document.getElementById("similar-topic"),
    similarStatus: document.getElementById("similar-status"),
    similarQuestion: document.getElementById("similar-question"),
    similarPosition: document.getElementById("similar-position"),
    similarUseCachedBtn: document.getElementById("similar-use-cached"),
    similarFreshBtn: document.getElementById("similar-fresh"),
    similarRefreshBtn: document.getElementById("similar-refresh"),
  };

  let historyConfigured = false;
  let pendingMatch = null; // the /api/similar match currently shown in similar-card

  // Short pipeline labels, keyed by the subagent `key` from /api/config —
  // full names are long ("Karnataka and Bengaluru Impact Agent"); the
  // pipeline strip needs something that fits in ~80px.
  const SHORT_LABELS = {
    question_framing: "Framing",
    evidence_research: "Evidence",
    stakeholder_mapping: "Stakeholders",
    karnataka_bengaluru_impact: "Karnataka/Blr",
    global_benchmark: "Benchmark",
    options_tradeoff: "Options",
    position_redteam: "Position",
    output_action: "Output",
  };

  const FEED_ICONS = {
    system: "i-check",
    message: null,
    tool: "i-tool",
    thread: "i-chevron",
    error: "i-alert",
    approval: "i-alert",
    done: "i-check",
  };

  let currentRunId = null;
  let currentSource = null;
  let pendingRequestId = null;
  let elapsedTimer = null;
  let runStartedAt = null;

  // ------------------------------------------------------------------ theme

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("policy_theme", theme);
  }

  function initTheme() {
    const saved = localStorage.getItem("policy_theme");
    if (saved === "dark" || saved === "light") {
      applyTheme(saved);
      return;
    }
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    applyTheme(prefersDark ? "dark" : "light");
  }

  el.themeToggle.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(next);
  });

  // ------------------------------------------------------------------ util

  function timeNow() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  function iconSvg(id) {
    return id ? `<svg class="icon"><use href="#${id}"/></svg>` : "";
  }

  function addFeedItem(variant, html) {
    el.feedEmpty.hidden = true;
    const item = document.createElement("div");
    item.className = `feed-item feed-item--${variant}`;
    const icon = FEED_ICONS[variant];
    item.innerHTML = `
      ${icon ? `<span class="feed-item__icon">${iconSvg(icon)}</span>` : ""}
      <span class="feed-item__body"><time>${timeNow()}</time>${html}</span>
    `;
    el.feed.appendChild(item);
    el.feed.scrollTop = el.feed.scrollHeight;
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str ?? "";
    return div.innerHTML;
  }

  // Wraps bare URLs in <a> tags. Must run AFTER escapeHtml — URL characters
  // (: / . ( )) aren't HTML-escaped, so this is safe on already-escaped text.
  function linkifyUrls(escapedHtml) {
    return escapedHtml.replace(/https?:\/\/[^\s<>"')\]]+/g, (url) => {
      let trail = "";
      while (url.length && /[.,;:!?]/.test(url[url.length - 1])) {
        trail = url[url.length - 1] + trail;
        url = url.slice(0, -1);
      }
      if (!url) return trail;
      return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>${trail}`;
    });
  }

  function setRunStatus(label) {
    el.runStatus.textContent = label;
  }

  function startElapsedTimer() {
    runStartedAt = Date.now();
    clearInterval(elapsedTimer);
    elapsedTimer = setInterval(() => {
      const secs = Math.floor((Date.now() - runStartedAt) / 1000);
      const m = Math.floor(secs / 60);
      const s = secs % 60;
      el.runElapsed.textContent = m > 0 ? `${m}m ${s}s` : `${s}s`;
    }, 1000);
  }

  function stopElapsedTimer() {
    clearInterval(elapsedTimer);
    elapsedTimer = null;
  }

  // ------------------------------------------------------------------ config / pipeline

  async function loadConfig() {
    try {
      const res = await fetch("/api/config");
      const data = await res.json();

      el.pipeline.innerHTML = "";
      data.subagents.forEach((s, i) => {
        const li = document.createElement("li");
        li.className = "pipeline__node";
        li.dataset.status = "pending";
        li.dataset.name = s.name;
        li.title = s.name;
        li.innerHTML = `
          <span class="pipeline__dot">${i + 1}</span>
          <span class="pipeline__label">${escapeHtml(SHORT_LABELS[s.key] || s.name)}</span>
        `;
        el.pipeline.appendChild(li);
      });

      historyConfigured = Boolean(data.history_configured);

      if (!data.configured) {
        el.headerStatus.textContent = "Not provisioned";
        el.headerStatus.dataset.state = "error";
        el.configHint.textContent = data.message || "Run `uv run policy-setup` first.";
        el.submitBtn.disabled = true;
      } else {
        el.headerStatus.textContent = historyConfigured ? "Ready · history enabled" : "Ready";
        el.headerStatus.dataset.state = "ok";
        el.configHint.textContent = "";
        el.submitBtn.disabled = false;
      }
    } catch (err) {
      el.headerStatus.textContent = "Could not reach backend";
      el.headerStatus.dataset.state = "error";
    }
  }

  function resetPipeline() {
    [...el.pipeline.children].forEach((li) => {
      li.dataset.status = "pending";
      const dot = li.querySelector(".pipeline__dot");
      const idx = [...el.pipeline.children].indexOf(li) + 1;
      dot.innerHTML = idx;
    });
  }

  function setPipelineStatus(agentName, status) {
    const item = [...el.pipeline.children].find((li) => li.dataset.name === agentName);
    if (!item) return;
    item.dataset.status = status;
    const dot = item.querySelector(".pipeline__dot");
    if (status === "idle") {
      dot.innerHTML = iconSvg("i-check");
    } else if (status === "running") {
      const idx = [...el.pipeline.children].indexOf(item) + 1;
      dot.innerHTML = idx;
    }
  }

  el.chips.addEventListener("click", (evt) => {
    const chip = evt.target.closest(".chip");
    if (!chip) return;
    el.input.value = chip.dataset.question;
    el.input.focus();
  });

  // ------------------------------------------------------------------ run lifecycle

  el.form.addEventListener("submit", async (evt) => {
    evt.preventDefault();
    const question = el.input.value.trim();
    if (!question) return;

    hideSimilarCard();

    if (!historyConfigured) {
      await startRun(question, null);
      return;
    }

    el.submitBtn.disabled = true;
    el.submitBtn.querySelector(".btn-label").textContent = "Checking history…";
    try {
      const res = await fetch(`/api/similar?question=${encodeURIComponent(question)}`);
      const data = await res.json();
      el.submitBtn.disabled = false;
      el.submitBtn.querySelector(".btn-label").textContent = "Start research";

      if (data.match) {
        // Automatically do research on top of the cached answer
        addFeedItem("system", `Found previous research on this topic. Automatically checking for updates...`);
        await startRun(question, data.match);
      } else {
        await startRun(question, null);
      }
    } catch (err) {
      // History lookup failing shouldn't block starting a fresh run.
      el.submitBtn.disabled = false;
      el.submitBtn.querySelector(".btn-label").textContent = "Start research";
      await startRun(question, null);
    }
  });

  function showSimilarCard(match, question) {
    pendingMatch = { ...match, _newQuestion: question };
    el.similarDate.textContent = match.created_at ? new Date(match.created_at).toLocaleDateString() : "on an earlier date";
    el.similarTopic.textContent = match.topic || "(none recorded)";
    el.similarStatus.textContent = match.approval_status;
    el.similarQuestion.textContent = `“${match.question}”`;
    el.similarPosition.innerHTML = linkifyUrls(escapeHtml(match.draft_position || "(none recorded)"));
    el.similarCard.hidden = false;
    el.similarCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function hideSimilarCard() {
    el.similarCard.hidden = true;
    pendingMatch = null;
  }

  el.similarUseCachedBtn.addEventListener("click", () => {
    if (!pendingMatch) return;
    addFeedItem(
      "done",
      `Using cached answer from ${pendingMatch.created_at ? new Date(pendingMatch.created_at).toLocaleDateString() : "an earlier run"} — no new research run.<br><strong>[${escapeHtml(pendingMatch.approval_status)}]</strong> ${linkifyUrls(escapeHtml(pendingMatch.draft_position || "(none recorded)"))}`
    );
    hideSimilarCard();
  });

  el.similarFreshBtn.addEventListener("click", async () => {
    if (!pendingMatch) return;
    const question = pendingMatch._newQuestion;
    hideSimilarCard();
    await startRun(question, null);
  });

  el.similarRefreshBtn.addEventListener("click", async () => {
    if (!pendingMatch) return;
    const { _newQuestion, ...match } = pendingMatch;
    hideSimilarCard();
    await startRun(_newQuestion, match);
  });

  async function startRun(question, refreshContext) {
    el.submitBtn.disabled = true;
    el.submitBtn.querySelector(".btn-label").textContent = "Starting…";

    try {
      const body = { question };
      if (refreshContext) body.refresh_context = refreshContext;

      const res = await fetch("/api/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const { run_id } = await res.json();
      currentRunId = run_id;

      el.feed.querySelectorAll(".feed-item").forEach((n) => n.remove());
      el.feedEmpty.hidden = true;
      el.outputsCard.hidden = true;
      el.outputsList.innerHTML = "";
      el.consoleLink.hidden = true;
      resetPipeline();
      setRunStatus("Starting…");
      startElapsedTimer();

      const label = refreshContext ? "Checking for updates on" : "Started research run";
      addFeedItem("system", `${label} <code>${run_id}</code> for: &ldquo;${escapeHtml(question)}&rdquo;`);
      openStream(run_id);
    } catch (err) {
      addFeedItem("error", `Failed to start: ${escapeHtml(err.message)}`);
      el.submitBtn.disabled = false;
      el.submitBtn.querySelector(".btn-label").textContent = "Start research";
    }
  }

  function openStream(runId) {
    if (currentSource) currentSource.close();
    const source = new EventSource(`/api/runs/${runId}/stream`);
    currentSource = source;

    source.addEventListener("session_started", (e) => {
      const data = JSON.parse(e.data);
      setRunStatus("Running");
      el.consoleLink.href = data.console_url;
      el.consoleLink.hidden = false;
      addFeedItem("system", "Session started — the pipeline above will light up as each agent runs.");
    });

    source.addEventListener("thread_created", (e) => {
      const data = JSON.parse(e.data);
      setPipelineStatus(data.agent_name, "running");
      addFeedItem("thread", `${escapeHtml(data.agent_name)} started`);
    });

    source.addEventListener("thread_running", (e) => {
      setPipelineStatus(JSON.parse(e.data).agent_name, "running");
    });

    source.addEventListener("thread_idle", (e) => {
      const data = JSON.parse(e.data);
      setPipelineStatus(data.agent_name, "idle");
      addFeedItem("thread", `${escapeHtml(data.agent_name)} finished`);
    });

    source.addEventListener("thread_message", () => {
      /* cross-thread chatter — omitted from the feed to avoid noise */
    });

    source.addEventListener("agent_message", (e) => {
      const data = JSON.parse(e.data);
      if (data.text && data.text.trim()) {
        addFeedItem("message", linkifyUrls(escapeHtml(data.text)));
      }
    });

    source.addEventListener("tool_use", (e) => {
      const data = JSON.parse(e.data);
      addFeedItem("tool", `Orchestrator used <strong>${escapeHtml(data.name)}</strong>`);
    });

    source.addEventListener("approval_requested", (e) => {
      setRunStatus("Awaiting approval");
      showApprovalModal(JSON.parse(e.data));
    });

    source.addEventListener("approval_resolved", (e) => {
      const data = JSON.parse(e.data);
      setRunStatus("Running");
      addFeedItem(
        "approval",
        data.approved ? "Draft position approved." : "Draft position rejected — sent back for revision."
      );
    });

    source.addEventListener("position_registered", (e) => {
      const data = JSON.parse(e.data);
      addFeedItem("done", `Approved position registered at <code>${escapeHtml(data.path)}</code>`);
    });

    source.addEventListener("error", (e) => {
      let message = "Connection error.";
      try {
        message = JSON.parse(e.data).message || message;
      } catch (_) { /* SSE transport-level error, no JSON payload */ }
      addFeedItem("error", escapeHtml(message));
    });

    source.addEventListener("done", (e) => {
      const data = JSON.parse(e.data);
      stopElapsedTimer();
      if (data.status === "completed") {
        setRunStatus("Completed");
        addFeedItem("done", "Run complete.");
        renderOutputs(runId, data.outputs || []);
      } else {
        setRunStatus("Error");
        addFeedItem("error", "Run ended with an error.");
      }
      source.close();
      el.submitBtn.disabled = false;
      el.submitBtn.querySelector(".btn-label").textContent = "Start research";
    });
  }

  function renderOutputs(runId, outputs) {
    if (!outputs.length) return;
    el.outputsCard.hidden = false;
    el.outputsList.innerHTML = "";
    outputs.forEach((o) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = `/api/runs/${runId}/outputs/${encodeURIComponent(o.filename)}`;
      a.innerHTML = `${iconSvg("i-download")}<span>${escapeHtml(o.filename)}</span>`;
      a.setAttribute("download", o.filename);
      li.appendChild(a);
      el.outputsList.appendChild(li);
    });
  }

  // ------------------------------------------------------------------ approval modal

  function showApprovalModal(data) {
    pendingRequestId = data.request_id;
    el.approvalTitle.textContent = data.policy_topic || "Draft position";
    el.approvalQuestion.textContent = data.policy_question || "";
    el.approvalSummary.innerHTML = linkifyUrls(escapeHtml(data.summary || ""));
    el.approvalDraft.innerHTML = linkifyUrls(escapeHtml(data.draft_position || ""));
    el.approvalNotes.value = "";
    el.approvalError.hidden = true;
    el.approveBtn.disabled = false;
    el.rejectBtn.disabled = false;
    el.overlay.hidden = false;
  }

  function hideApprovalModal() {
    el.overlay.hidden = true;
    pendingRequestId = null;
  }

  async function submitDecision(approved) {
    if (!currentRunId || !pendingRequestId) return;
    const notes = el.approvalNotes.value.trim();

    if (!approved && !notes) {
      el.approvalError.textContent = "Notes are required when rejecting a draft position.";
      el.approvalError.hidden = false;
      return;
    }

    el.approveBtn.disabled = true;
    el.rejectBtn.disabled = true;

    try {
      const res = await fetch(`/api/runs/${currentRunId}/approvals/${pendingRequestId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approved, notes: notes || null }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      hideApprovalModal();
    } catch (err) {
      el.approvalError.textContent = `Could not submit decision: ${err.message}`;
      el.approvalError.hidden = false;
      el.approveBtn.disabled = false;
      el.rejectBtn.disabled = false;
    }
  }

  el.approveBtn.addEventListener("click", () => submitDecision(true));
  el.rejectBtn.addEventListener("click", () => submitDecision(false));

  initTheme();
  loadConfig();
})();
