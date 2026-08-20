(function () {
  "use strict";

  var LAYOUT = [
    { key: "toyota_news", size: "wide" },
    { key: "youtube_popular", size: "narrow" },
    { key: "youtube_new", size: "narrow" },
    { key: "media_reviews", size: "wide" },
    { key: "social_buzz", size: "half" },
    { key: "complaints", size: "half" },
  ];

  var board = document.getElementById("board");
  var loading = document.getElementById("loading");
  var lastUpdatedEl = document.getElementById("last-updated");
  var statusDot = document.getElementById("status-dot");

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function formatPublished(raw) {
    if (!raw) return "";
    // RSS dates parse cleanly; YouTube's relative text ("3 hours ago") does not.
    var parsed = new Date(raw);
    if (!isNaN(parsed.getTime()) && /\d{4}/.test(raw)) {
      return parsed.toLocaleString("ja-JP", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    }
    return raw;
  }

  function buildItem(item) {
    var a = el("a", "item");
    a.href = item.url || "#";
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    if (!item.url) {
      a.removeAttribute("href");
      a.style.cursor = "default";
    }

    var title = el("span", "item__title", item.title || "(タイトル不明)");
    a.appendChild(title);

    var meta = el("div", "item__meta");
    if (item.source) meta.appendChild(el("span", null, item.source));
    var published = formatPublished(item.published);
    if (item.source && published) meta.appendChild(el("span", "dot", "・"));
    if (published) meta.appendChild(el("span", null, published));
    if (item.view_count_text) {
      meta.appendChild(el("span", "item__metric", item.view_count_text));
    }
    a.appendChild(meta);

    return a;
  }

  function buildPanel(sectionKey, section, size) {
    var panel = el("section", "panel panel--" + size);

    var header = el("div", "panel__header");
    header.appendChild(el("h2", "panel__title", section.label || sectionKey));
    var items = section.items || [];
    header.appendChild(el("span", "panel__count", items.length + " 件"));
    panel.appendChild(header);

    if (section.note) {
      panel.appendChild(el("p", "panel__note", section.note));
    }

    if (items.length === 0) {
      panel.appendChild(el("p", "panel__empty", "現在、該当する情報はありません。"));
      return panel;
    }

    var list = el("ul", "panel__list");
    items.forEach(function (item) {
      var li = el("li");
      li.appendChild(buildItem(item));
      list.appendChild(li);
    });
    panel.appendChild(list);

    return panel;
  }

  function render(data) {
    board.innerHTML = "";
    LAYOUT.forEach(function (entry) {
      var section = data.sections && data.sections[entry.key];
      if (!section) return;
      board.appendChild(buildPanel(entry.key, section, entry.size));
    });

    lastUpdatedEl.textContent = "最終更新: " + (data.generated_at_jst || "不明");

    var generatedAt = data.generated_at_utc ? new Date(data.generated_at_utc) : null;
    if (generatedAt) {
      var hoursSince = (Date.now() - generatedAt.getTime()) / 36e5;
      statusDot.classList.toggle("is-stale", hoursSince > 8);
    }
  }

  function renderError(message) {
    board.innerHTML = "";
    board.appendChild(el("p", "board__error", message));
    lastUpdatedEl.textContent = "更新情報を取得できませんでした";
    statusDot.classList.add("is-error");
  }

  fetch("data/latest.json", { cache: "no-store" })
    .then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    })
    .then(render)
    .catch(function (err) {
      renderError("ダッシュボードデータの読み込みに失敗しました(" + err.message + ")。");
    });
})();
