/* =====================================================================
   Numa — front-end logic
   Talks to POST /api/chat  ->  { answer: "..." }
   ===================================================================== */

(() => {
  "use strict";

  const app        = document.getElementById("app");
  const scroll     = document.getElementById("scroll");
  const thread     = document.getElementById("thread");
  const composer   = document.getElementById("composer");
  const slot       = document.getElementById("composerSlot");
  const dock       = document.getElementById("dock");
  const input      = document.getElementById("input");
  const sendBtn    = document.getElementById("send");
  const themeBtn   = document.getElementById("themeToggle");

  /** Conversation so far; sent to the server so follow-ups have context. */
  const history = [];
  let busy = false;

  /* ---------------------------------------------------------------- theme */

  const THEME_KEY = "numa-theme";

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    try { localStorage.setItem(THEME_KEY, theme); } catch (_) { /* private mode */ }
  }

  (function initTheme() {
    let saved = null;
    try { saved = localStorage.getItem(THEME_KEY); } catch (_) { /* ignore */ }
    if (saved === "light" || saved === "dark") return applyTheme(saved);
    const prefersLight = window.matchMedia("(prefers-color-scheme: light)").matches;
    applyTheme(prefersLight ? "light" : "dark");
  })();

  themeBtn.addEventListener("click", () => {
    const now = document.documentElement.getAttribute("data-theme");
    applyTheme(now === "dark" ? "light" : "dark");
  });

  /* ------------------------------------------------------- tiny markdown */
  // The model replies in light markdown. Everything is escaped first, so no
  // model output is ever inserted as raw HTML.

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function inline(s) {
    return escapeHtml(s)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[\s(])\*([^*\n]+)\*/g, "$1<em>$2</em>");
  }

  function renderMarkdown(text) {
    const lines = String(text).replace(/\r\n/g, "\n").split("\n");
    const out = [];
    let list = null;      // "ul" | "ol" | null
    let para = [];

    const flushPara = () => {
      if (para.length) { out.push(`<p>${inline(para.join(" "))}</p>`); para = []; }
    };
    const flushList = () => {
      if (list) { out.push(`</${list}>`); list = null; }
    };

    for (const raw of lines) {
      const line = raw.trimEnd();

      if (!line.trim()) { flushPara(); flushList(); continue; }

      const bullet = line.match(/^\s*[-*•]\s+(.*)$/);
      const number = line.match(/^\s*\d+[.)]\s+(.*)$/);

      if (bullet || number) {
        flushPara();
        const want = bullet ? "ul" : "ol";
        if (list !== want) { flushList(); out.push(`<${want}>`); list = want; }
        out.push(`<li>${inline((bullet || number)[1])}</li>`);
        continue;
      }

      flushList();
      para.push(line.trim());
    }
    flushPara();
    flushList();
    return out.join("");
  }

  /* -------------------------------------------------------- message view */

  function addMessage(role, html) {
    const el = document.createElement("div");
    el.className = `msg ${role}`;
    el.innerHTML = `<span class="avatar" aria-hidden="true"></span><div class="bubble">${html}</div>`;
    thread.appendChild(el);
    return el;
  }

  function scrollToEnd() {
    requestAnimationFrame(() => { scroll.scrollTop = scroll.scrollHeight; });
  }

  /** Move the composer from under the hero into the docked bottom bar. */
  function leaveEmptyState() {
    if (!app.classList.contains("is-empty")) return;
    app.classList.remove("is-empty");
    document.body.classList.add("chatting");
    dock.appendChild(composer);
    dock.setAttribute("aria-hidden", "false");
    slot.remove();
  }

  /* ------------------------------------------------------------ composer */

  function autosize() {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 180) + "px";
  }

  function setBusy(state) {
    busy = state;
    sendBtn.disabled = state || !input.value.trim();
    input.disabled = state;
    if (!state) input.focus();
  }

  input.addEventListener("input", () => {
    autosize();
    sendBtn.disabled = busy || !input.value.trim();
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      composer.requestSubmit();
    }
  });

  composer.addEventListener("submit", (e) => {
    e.preventDefault();
    send();
  });

  /* ------------------------------------------------------------- sending */

  async function send() {
    const question = input.value.trim();
    if (!question || busy) return;

    leaveEmptyState();

    addMessage("user", `<p>${inline(question)}</p>`);
    input.value = "";
    autosize();
    setBusy(true);
    scrollToEnd();

    const pending = addMessage(
      "assistant",
      '<span class="dots"><i></i><i></i><i></i></span>'
    );
    scrollToEnd();

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question, history }),
      });

      if (!res.ok) throw new Error(`Server returned ${res.status}`);

      const data = await res.json();
      const answer = (data.answer || "").trim() || "No answer came back.";

      pending.querySelector(".bubble").innerHTML = renderMarkdown(answer);

      history.push({ role: "user", content: question });
      history.push({ role: "assistant", content: answer });
    } catch (err) {
      pending.querySelector(".bubble").innerHTML =
        `<div class="error">Couldn’t reach the assistant. ${escapeHtml(err.message)}</div>`;
    } finally {
      setBusy(false);
      scrollToEnd();
    }
  }

  /* --------------------------------------------------------------- start */

  sendBtn.disabled = true;
  input.focus();
})();