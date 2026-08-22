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
    calendar:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
      '<rect x="3.5" y="5" width="17" height="15" rx="2"/><line x1="3.5" y1="9.5" x2="20.5" y2="9.5"/>' +
      '<line x1="8" y1="3" x2="8" y2="6.5"/><line x1="16" y1="3" x2="16" y2="6.5"/></svg>',
  };

  var LAYOUT = [
    { key: "toyota_news", size: "full", icon: "doc" },
    { key: "motorsports", size: "full", icon: "flag" },
    { key: "events", size: "full", icon: "calendar" },
    { key: "youtube_popular", size: "half", icon: "play" },
    { key: "youtube_new", size: "half", icon: "play" },
    { key: "youtube_popular_jp", size: "half", icon: "play" },
    { key: "youtube_new_jp", size: "half", icon: "play" },
    { key: "media_reviews", size: "half", icon: "star" },
    { key: "social_buzz", size: "half", icon: "chat" },
    { key: "complaints", size: "full", icon: "alert" },
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
        year: "numeric",
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
    var pill = el(
      "span",
      "sentiment-pill sentiment-pill--" + sentiment.label,
      sentiment.label === "positive" ? "▲ " + SENTIMENT_LABEL_JA.positive : "▼ " + SENTIMENT_LABEL_JA.negative
    );
    var reasons = sentiment.reasons || [];
    if (reasons.length > 0) {
      var tip =
        "判定根拠: " +
        reasons.join(" / ") +
        (sentiment.label === "positive" ? " という語がポジティブ" : " という語がネガティブ") +
        "と判定されました";
      pill.setAttribute("data-tip", tip);
      pill.tabIndex = 0;
    }
    return pill;
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

  function buildComplaintsPanel(icon, section) {
    var panel = el("section", "panel panel--full");
    var latestItems = section.items || [];
    var buzzItems = section.items_buzz || [];
    panel.appendChild(buildPanelHeader(icon, section.label, latestItems.length));
    if (section.note) panel.appendChild(el("p", "panel__note", section.note));

    var tabs = el("div", "tab-group");
    var tabLatest = el("button", "tab-group__btn is-active", "最新順");
    var tabBuzz = el("button", "tab-group__btn", "話題順");
    tabs.appendChild(tabLatest);
    tabs.appendChild(tabBuzz);
    panel.appendChild(tabs);

    var listWrap = el("div");
    function renderList(items) {
      listWrap.innerHTML = "";
      if (items.length === 0) {
        listWrap.appendChild(el("p", "panel__empty", "現在、該当する情報はありません。"));
      } else {
        listWrap.appendChild(buildList(items));
      }
    }
    renderList(latestItems);
    panel.appendChild(listWrap);

    tabLatest.addEventListener("click", function () {
      tabLatest.classList.add("is-active");
      tabBuzz.classList.remove("is-active");
      renderList(latestItems);
    });
    tabBuzz.addEventListener("click", function () {
      tabBuzz.classList.add("is-active");
      tabLatest.classList.remove("is-active");
      renderList(buzzItems);
    });

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

  function buildStandingsChart(rows) {
    var maxPoints = rows.reduce(function (m, r) { return Math.max(m, r.points); }, 1);
    var chart = el("div", "standings-chart");
    rows.forEach(function (row) {
      var rowEl = el("div", "standings-chart__row" + (row.is_gr_corolla ? " standings-chart__row--gr" : ""));
      rowEl.appendChild(el("span", "standings-chart__pos", String(row.position)));

      var main = el("div", "standings-chart__main");
      var nameLine = el("div", "standings-chart__name-line");
      nameLine.appendChild(el("span", "standings-chart__name", row.name));
      if (row.is_gr_corolla) {
        nameLine.appendChild(el("span", "gr-tag", "GR COROLLA"));
      }
      main.appendChild(nameLine);

      if (row.team || row.car) {
        main.appendChild(
          el("span", "standings-chart__sub", [row.team, row.car].filter(Boolean).join(" · "))
        );
      }

      var track = el("div", "standings-chart__track");
      var fill = el("div", "standings-chart__fill");
      fill.style.width = Math.max(4, (100 * row.points) / maxPoints) + "%";
      track.appendChild(fill);
      main.appendChild(track);

      rowEl.appendChild(main);
      rowEl.appendChild(el("span", "standings-chart__points", String(row.points)));
      chart.appendChild(rowEl);
    });
    return chart;
  }

  function buildScheduleBlock(s) {
    var wrap = el("div", "series-card__group");
    wrap.appendChild(el("div", "series-card__group-title", "レース日程"));

    if (s.schedule_link) {
      wrap.appendChild(
        el(
          "p",
          "panel__note series-card__chart-note",
          "日程データの構造が不安定なため一覧化を見送っています。公式スケジュールは以下のリンクからご確認ください。"
        )
      );
      var link = el("a", "series-card__link", "公式スケジュールを見る ↗");
      link.href = s.schedule_link;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      wrap.appendChild(link);
      return wrap;
    }

    var rounds = s.schedule || [];
    if (rounds.length === 0) {
      wrap.appendChild(el("p", "panel__empty", "日程情報を取得できませんでした。"));
      return wrap;
    }

    var nextRace = rounds.filter(function (r) { return r.status === "upcoming"; })[0];
    if (nextRace) {
      var next = el("div", "schedule-next");
      next.appendChild(el("span", "schedule-next__label", "次戦"));
      next.appendChild(el("span", "schedule-next__date", nextRace.date_range));
      next.appendChild(
        el("span", "schedule-next__track", [nextRace.round, nextRace.name, nextRace.track].filter(Boolean).join(" · "))
      );
      wrap.appendChild(next);
    }

    var list = el("ul", "schedule-list");
    rounds.forEach(function (r) {
      var li = el("li", "schedule-list__item schedule-list__item--" + r.status);
      li.appendChild(el("span", "schedule-list__dot"));
      li.appendChild(el("span", "schedule-list__date", r.date_range));
      li.appendChild(el("span", "schedule-list__label", [r.round, r.name, r.track].filter(Boolean).join(" · ")));
      list.appendChild(li);
    });
    wrap.appendChild(list);

    return wrap;
  }

  var PODIUM_MEDALS = { First: "1", Second: "2", Third: "3" };

  function buildPodiumGroup(title, rows) {
    var group = el("div", "podium__group");
    group.appendChild(el("div", "podium__group-title", title));
    rows.forEach(function (row) {
      var line = el("div", "podium__row" + (row.is_gr_corolla ? " podium__row--gr" : ""));
      line.appendChild(el("span", "podium__pos", PODIUM_MEDALS[row.position] || "?"));
      line.appendChild(el("span", "podium__name", row.name));
      if (row.brand) line.appendChild(el("span", "podium__brand", row.brand));
      if (row.is_gr_corolla) line.appendChild(el("span", "gr-tag", "TOYOTA"));
      group.appendChild(line);
    });
    return group;
  }

  function buildPodium(podium) {
    var wrap = el("div", "podium");
    if (podium.drivers && podium.drivers.length > 0) {
      wrap.appendChild(buildPodiumGroup("ドライバー", podium.drivers));
    }
    if (podium.codrivers && podium.codrivers.length > 0) {
      wrap.appendChild(buildPodiumGroup("コ・ドライバー", podium.codrivers));
    }
    return wrap;
  }

  function buildRankingBlock(s) {
    var wrap = el("div", "series-card__group");
    wrap.appendChild(el("div", "series-card__group-title", "シリーズランキング"));
    if (s.standings_chart && s.standings_chart.length > 0) {
      wrap.appendChild(buildStandingsChart(s.standings_chart));
    } else if (s.podium && (s.podium.drivers || []).length > 0) {
      wrap.appendChild(buildPodium(s.podium));
    }
    if (s.standings_chart_note) {
      wrap.appendChild(el("p", "panel__note series-card__chart-note", s.standings_chart_note));
    }
    return wrap;
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
      card.appendChild(buildScheduleBlock(s));
      card.appendChild(buildRankingBlock(s));
      card.appendChild(buildSeriesGroup("トピックス", s.topics));
      card.appendChild(buildSeriesGroup("最新レース結果", s.results));
      card.appendChild(buildSeriesGroup("ランキング関連ニュース", s.standings));

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
    [
      "youtube_popular",
      "youtube_new",
      "youtube_popular_jp",
      "youtube_new_jp",
      "social_buzz",
      "media_reviews",
      "complaints",
      "events",
    ].forEach(function (key) {
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

    var youtubeCount = ["youtube_popular", "youtube_new", "youtube_popular_jp", "youtube_new_jp"].reduce(
      function (sum, key) {
        return sum + ((data.sections[key] && data.sections[key].items) || []).length;
      },
      0
    );

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
    t3.appendChild(el("div", "stat-tile__label", "YouTube動画(グローバル+日本語)"));
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
      var panel;
      if (entry.key === "motorsports") {
        panel = buildMotorsportsPanel(entry.icon, section);
      } else if (entry.key === "complaints") {
        panel = buildComplaintsPanel(entry.icon, section);
      } else {
        panel = buildGenericPanel(entry.icon, section, entry.size);
      }
      board.appendChild(panel);
    });

    lastUpdatedEl.textContent = "最終更新: " + (data.generated_at_jst || "不明");

    var generatedAt = data.generated_at_utc ? new Date(data.generated_at_utc) : null;
    if (generatedAt) {
      // 30分おき更新なので、90分(3サイクル分)を超えて更新が止まっていたら注意表示にする
      var minutesSince = (Date.now() - generatedAt.getTime()) / 6e4;
      statusDot.classList.toggle("is-stale", minutesSince > 90);
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
