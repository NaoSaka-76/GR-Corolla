(function () {
  "use strict";

  var ICONS = {
    doc:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
      '<path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4"/>' +
      '<line x1="9.5" y1="12" x2="16" y2="12"/><line x1="9.5" y1="15.5" x2="16" y2="15.5"/><line x1="9.5" y1="19" x2="13" y2="19"/></svg>',
    play:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">' +
      '<circle cx="12" cy="12" r="9"/><path d="M10 8.5l6 3.5-6 3.5z" fill="currentColor" stroke="none"/></svg>',
    chat:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
      '<path d="M4 5h16v11H8l-4 4z"/></svg>',
    star:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round">' +
      '<path d="M12 3.5l2.6 5.4 5.9.8-4.3 4.2 1 5.9-5.2-2.8-5.2 2.8 1-5.9-4.3-4.2 5.9-.8z"/></svg>',
    alert:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
      '<path d="M12 4l9.5 16H2.5z"/><line x1="12" y1="10" x2="12" y2="14.5"/><circle cx="12" cy="17.3" r="0.9" fill="currentColor" stroke="none"/></svg>',
    flag:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">' +
      '<path d="M5 3v18"/><path d="M5 4h14l-3 3.5 3 3.5H5z"/></svg>',
  };

  var LAYOUT = [
    { key: "toyota_news", size: "wide", icon: "doc" },
    { key: "motorsports", size: "full", icon: "flag" },
    { key: "youtube_popular", size: "narrow", icon: "play" },
    { key: "youtube_new", size: "narrow", icon: "play" },
    { key: "media_reviews", size: "wide", icon: "star" },
    { key: "social_buzz", size: "half", icon: "chat" },
    { key: "complaints", size: "half", icon: "alert" },
  ];

  var SENTIMENT_LABEL_JA = { positive: "ポジティブ", negative: "ネガティブ", neutral: "中立" };

  var board = document.getElementById("board");
  var statsEl = document.getElementById("stats");
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

  function sentimentPill(sentiment) {
    if (!sentiment || sentiment.label === "neutral") return null;
    return el(
      "span",
      "sentiment-pill sentiment-pill--" + sentiment.label,
      sentiment.label === "positive" ? "▲ " + SENTIMENT_LABEL_JA.positive : "▼ " + SENTIMENT_LABEL_JA.negative
    );
  }

  function buildItem(item) {
    var sentimentLabel = item.sentiment ? item.sentiment.label : "neutral";
    var a = el("a", "item item--" + sentimentLabel);
    a.href = item.url || "#";
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    if (!item.url) {
      a.removeAttribute("href");
      a.style.cursor = "default";
    }

    if (item.thumbnail) {
      var img = el("img", "item__thumb");
      img.src = item.thumbnail;
      img.alt = "";
      img.loading = "lazy";
      a.appendChild(img);
    }

    var body = el("div", "item__body");
    body.appendChild(el("span", "item__title", item.title || "(タイトル不明)"));

    var meta = el("div", "item__meta");
    var pill = sentimentPill(item.sentiment);
    if (pill) meta.appendChild(pill);
    if (item.source) meta.appendChild(el("span", null, item.source));
    var published = formatPublished(item.published);
    if (published) meta.appendChild(el("span", null, published));
    if (item.view_count_text) {
      meta.appendChild(el("span", "item__metric", item.view_count_text));
    }
    body.appendChild(meta);
    a.appendChild(body);

    return a;
  }

  function buildList(items) {
    var list = el("ul", "panel__list");
    items.forEach(function (item) {
      var li = el("li");
      li.appendChild(buildItem(item));
      list.appendChild(li);
    });
    return list;
  }

  function buildPanelHeader(icon, label, count) {
    var header = el("div", "panel__header");
    var iconWrap = el("div", "panel__icon");
    iconWrap.innerHTML = ICONS[icon] || "";
    header.appendChild(iconWrap);
    header.appendChild(el("h2", "panel__title", label));
    if (count !== undefined) header.appendChild(el("span", "panel__count", count + " 件"));
    return header;
  }

  function buildGenericPanel(icon, section, size) {
    var panel = el("section", "panel panel--" + size);
    var items = section.items || [];
    panel.appendChild(buildPanelHeader(icon, section.label, items.length));

    if (section.note) panel.appendChild(el("p", "panel__note", section.note));

    if (items.length === 0) {
      panel.appendChild(el("p", "panel__empty", "現在、該当する情報はありません。"));
      return panel;
    }
    panel.appendChild(buildList(items));
    return panel;
  }

  function buildSeriesGroup(title, items) {
    var group = el("div", "series-card__group");
    group.appendChild(el("div", "series-card__group-title", title));
    if (items.length === 0) {
      group.appendChild(el("p", "panel__empty", "該当情報なし"));
    } else {
      group.appendChild(buildList(items));
    }
    return group;
  }

  function buildMotorsportsPanel(icon, section) {
    var panel = el("section", "panel panel--full");
    var seriesCount = Object.values(section.series || {}).reduce(function (sum, s) {
      return sum + s.topics.length + s.results.length + s.standings.length;
    }, 0);
    panel.appendChild(buildPanelHeader(icon, section.label, seriesCount));
    if (section.note) panel.appendChild(el("p", "panel__note", section.note));

    var grid = el("div", "motorsports");
    Object.keys(section.series || {}).forEach(function (key) {
      var s = section.series[key];
      var card = el("div", "series-card series-card--" + key);
      card.appendChild(el("div", "series-card__header", s.label));
      card.appendChild(buildSeriesGroup("トピックス", s.topics));
      card.appendChild(buildSeriesGroup("最新レース結果", s.results));
      card.appendChild(buildSeriesGroup("シリーズランキング関連", s.standings));

      var link = el("a", "series-card__link", "公式ランキングを検索 ↗");
      link.href = s.standings_search_url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      card.appendChild(link);

      grid.appendChild(card);
    });
    panel.appendChild(grid);
    return panel;
  }

  function collectSentimentItems(data) {
    var all = [];
    ["youtube_popular", "youtube_new", "social_buzz", "media_reviews", "complaints"].forEach(function (key) {
      var section = data.sections[key];
      if (section && section.items) all = all.concat(section.items);
    });
    var ms = data.sections.motorsports;
    if (ms && ms.series) {
      Object.values(ms.series).forEach(function (s) {
        all = all.concat(s.topics, s.results, s.standings);
      });
    }
    return all;
  }

  function buildStats(data) {
    statsEl.innerHTML = "";

    var toyotaCount = (data.sections.toyota_news && data.sections.toyota_news.items || []).length;
    var sentimentItems = collectSentimentItems(data);
    var totalCount = toyotaCount + sentimentItems.length;

    var counts = { positive: 0, neutral: 0, negative: 0 };
    sentimentItems.forEach(function (item) {
      var label = item.sentiment ? item.sentiment.label : "neutral";
      counts[label] = (counts[label] || 0) + 1;
    });

    var youtubeCount =
      (data.sections.youtube_popular && data.sections.youtube_popular.items || []).length +
      (data.sections.youtube_new && data.sections.youtube_new.items || []).length;

    var motorsportsCount = 0;
    if (data.sections.motorsports && data.sections.motorsports.series) {
      Object.values(data.sections.motorsports.series).forEach(function (s) {
        motorsportsCount += s.topics.length + s.results.length + s.standings.length;
      });
    }

    // Tile 1: total
    var t1 = el("div", "stat-tile");
    t1.appendChild(el("div", "stat-tile__label", "本日の総情報件数"));
    var v1 = el("div", "stat-tile__value", String(totalCount));
    v1.appendChild(el("small", null, "件"));
    t1.appendChild(v1);
    statsEl.appendChild(t1);

    // Tile 2: sentiment breakdown
    var t2 = el("div", "stat-tile");
    t2.appendChild(el("div", "stat-tile__label", "評判(トヨタ公式発表を除く)"));
    var v2 = el("div", "stat-tile__value", String(counts.positive));
    v2.appendChild(el("small", null, "件ポジティブ"));
    t2.appendChild(v2);
    var total = counts.positive + counts.neutral + counts.negative || 1;
    var bar = el("div", "sentiment-bar");
    bar.appendChild(el("div", "sentiment-bar__seg sentiment-bar__seg--positive")).style.width = (100 * counts.positive / total) + "%";
    bar.appendChild(el("div", "sentiment-bar__seg sentiment-bar__seg--neutral")).style.width = (100 * counts.neutral / total) + "%";
    bar.appendChild(el("div", "sentiment-bar__seg sentiment-bar__seg--negative")).style.width = (100 * counts.negative / total) + "%";
    t2.appendChild(bar);
    var legend = el("div", "sentiment-legend");
    var lp = el("span"); lp.appendChild(el("span", "legend-dot legend-dot--positive")); lp.appendChild(document.createTextNode(counts.positive + ""));
    var ln = el("span"); ln.appendChild(el("span", "legend-dot legend-dot--neutral")); ln.appendChild(document.createTextNode(counts.neutral + ""));
    var lg = el("span"); lg.appendChild(el("span", "legend-dot legend-dot--negative")); lg.appendChild(document.createTextNode(counts.negative + ""));
    legend.appendChild(lp); legend.appendChild(ln); legend.appendChild(lg);
    t2.appendChild(legend);
    statsEl.appendChild(t2);

    // Tile 3: youtube
    var t3 = el("div", "stat-tile");
    t3.appendChild(el("div", "stat-tile__label", "YouTube動画(人気+新着)"));
    var v3 = el("div", "stat-tile__value", String(youtubeCount));
    v3.appendChild(el("small", null, "本"));
    t3.appendChild(v3);
    statsEl.appendChild(t3);

    // Tile 4: motorsports
    var t4 = el("div", "stat-tile");
    t4.appendChild(el("div", "stat-tile__label", "モータースポーツ関連話題"));
    var v4 = el("div", "stat-tile__value", String(motorsportsCount));
    v4.appendChild(el("small", null, "件"));
    t4.appendChild(v4);
    statsEl.appendChild(t4);
  }

  function render(data) {
    buildStats(data);

    board.innerHTML = "";
    LAYOUT.forEach(function (entry) {
      var section = data.sections && data.sections[entry.key];
      if (!section) return;
      var panel =
        entry.key === "motorsports"
          ? buildMotorsportsPanel(entry.icon, section)
          : buildGenericPanel(entry.icon, section, entry.size);
      board.appendChild(panel);
    });

    lastUpdatedEl.textContent = "最終更新: " + (data.generated_at_jst || "不明");

    var generatedAt = data.generated_at_utc ? new Date(data.generated_at_utc) : null;
    if (generatedAt) {
      var hoursSince = (Date.now() - generatedAt.getTime()) / 36e5;
      statusDot.classList.toggle("is-stale", hoursSince > 8);
    }
  }

  function renderError(message) {
    statsEl.innerHTML = "";
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
