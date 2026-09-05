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
    clock:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
      '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l3 2"/><path d="M9 2h6"/></svg>',
    timer:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
      '<circle cx="12" cy="13.5" r="7.5"/><path d="M12 13.5V9.2"/><path d="M10 2.5h4"/><path d="M18.5 6l1.3-1.3"/></svg>',
  };

  var CAR_SPEC_LABELS = {
    engine: "エンジン",
    power: "最高出力",
    torque: "最大トルク",
    weight: "車両重量",
    drivetrain: "駆動方式",
    transmission: "トランスミッション",
    brakes: "ブレーキ",
    suspension: "サスペンション",
    safety: "安全装備",
    tire_front: "タイヤ(前)",
    tire_rear: "タイヤ(後)",
  };

  var LAYOUT = [
    { key: "toyota_news", size: "full", icon: "doc" },
    { key: "motorsports", size: "full", icon: "flag" },
    { key: "events", size: "full", icon: "calendar" },
    { key: "youtube", size: "full", icon: "play" },
    { key: "media_reviews", size: "half", icon: "star" },
    { key: "social_buzz", size: "half", icon: "chat" },
    { key: "complaints", size: "full", icon: "alert" },
    { key: "nurburgring", size: "full", icon: "timer" },
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

  function isWithin24h(item) {
    // YouTube動画はrecency_seconds(取得時点からの経過秒数)、ニュース記事は
    // publishedのRSS日時文字列から判定する。
    if (typeof item.recency_seconds === "number") {
      return item.recency_seconds <= 86400;
    }
    if (item.published) {
      var parsed = Date.parse(item.published);
      if (!isNaN(parsed)) {
        return Date.now() - parsed <= 86400000;
      }
    }
    return false;
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
    var recent = isWithin24h(item);
    var a = el("a", "item item--" + sentimentLabel + (recent ? " item--recent" : ""));
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
    if (recent) meta.appendChild(el("span", "new-badge", "24時間以内"));
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

  function buildGenericPanel(icon, section, size, key) {
    var panel = el("section", "panel panel--" + size);
    panel.id = "section-" + key;
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
    panel.id = "section-complaints";
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

  function youtubeItemKey(item) {
    return item.video_id || item.url || item.title;
  }

  function mergeDedupItems(listA, listB) {
    var seen = {};
    var out = [];
    listA.concat(listB).forEach(function (item) {
      var k = youtubeItemKey(item);
      if (seen[k]) return;
      seen[k] = true;
      out.push(item);
    });
    return out;
  }

  function buildYoutubePanel(icon, data) {
    var sections = data.sections;
    var globalPopular = (sections.youtube_popular && sections.youtube_popular.items) || [];
    var globalNew = (sections.youtube_new && sections.youtube_new.items) || [];
    var jpPopular = (sections.youtube_popular_jp && sections.youtube_popular_jp.items) || [];
    var jpNew = (sections.youtube_new_jp && sections.youtube_new_jp.items) || [];

    var pools = {
      global: { popular: globalPopular, new: globalNew },
      jp: { popular: jpPopular, new: jpNew },
      all: {
        popular: mergeDedupItems(globalPopular, jpPopular).sort(function (a, b) {
          return (b.view_count || 0) - (a.view_count || 0);
        }),
        new: mergeDedupItems(globalNew, jpNew).sort(function (a, b) {
          var aSec = a.recency_seconds === undefined || a.recency_seconds === null ? Infinity : a.recency_seconds;
          var bSec = b.recency_seconds === undefined || b.recency_seconds === null ? Infinity : b.recency_seconds;
          return aSec - bSec;
        }),
      },
    };

    var totalCount = mergeDedupItems(mergeDedupItems(globalPopular, globalNew), mergeDedupItems(jpPopular, jpNew)).length;

    var panel = el("section", "panel panel--full");
    panel.id = "section-youtube";
    panel.appendChild(buildPanelHeader(icon, "YouTube動画(グローバル・日本語)", totalCount));

    var controls = el("div", "youtube-controls");
    var regionTabs = el("div", "tab-group");
    var regionAll = el("button", "tab-group__btn is-active", "すべて");
    var regionGlobal = el("button", "tab-group__btn", "グローバル");
    var regionJp = el("button", "tab-group__btn", "日本");
    [regionAll, regionGlobal, regionJp].forEach(function (b) { regionTabs.appendChild(b); });

    var orderTabs = el("div", "tab-group");
    var orderNew = el("button", "tab-group__btn is-active", "新着順");
    var orderPopular = el("button", "tab-group__btn", "話題順");
    [orderNew, orderPopular].forEach(function (b) { orderTabs.appendChild(b); });

    controls.appendChild(regionTabs);
    controls.appendChild(orderTabs);
    panel.appendChild(controls);

    var listWrap = el("div");
    panel.appendChild(listWrap);

    var state = { region: "all", order: "new" };

    function renderList() {
      var items = (pools[state.region] && pools[state.region][state.order]) || [];
      listWrap.innerHTML = "";
      if (items.length === 0) {
        listWrap.appendChild(el("p", "panel__empty", "現在、該当する情報はありません。"));
      } else {
        listWrap.appendChild(buildList(items));
      }
    }
    renderList();

    function setActive(buttons, activeBtn) {
      buttons.forEach(function (b) { b.classList.toggle("is-active", b === activeBtn); });
    }

    regionAll.addEventListener("click", function () {
      state.region = "all";
      setActive([regionAll, regionGlobal, regionJp], regionAll);
      renderList();
    });
    regionGlobal.addEventListener("click", function () {
      state.region = "global";
      setActive([regionAll, regionGlobal, regionJp], regionGlobal);
      renderList();
    });
    regionJp.addEventListener("click", function () {
      state.region = "jp";
      setActive([regionAll, regionGlobal, regionJp], regionJp);
      renderList();
    });
    orderNew.addEventListener("click", function () {
      state.order = "new";
      setActive([orderNew, orderPopular], orderNew);
      renderList();
    });
    orderPopular.addEventListener("click", function () {
      state.order = "popular";
      setActive([orderNew, orderPopular], orderPopular);
      renderList();
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
      var nameEl = el("span", "standings-chart__name", row.name);
      // 表示幅の都合で省略記号(...)表示になった場合でも、hoverで全文を確認できるようにする。
      if (row.name) nameEl.title = row.name;
      nameLine.appendChild(nameEl);
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

  function buildScheduleNextRow(label, race, modifierClass) {
    if (!race) return null;
    var row = el("div", "schedule-next" + (modifierClass ? " " + modifierClass : ""));
    row.appendChild(el("span", "schedule-next__label", label));
    row.appendChild(el("span", "schedule-next__date", race.date_range));
    row.appendChild(
      el("span", "schedule-next__track", [race.round, race.name, race.track].filter(Boolean).join(" · "))
    );
    return row;
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
      var nameEl = el("span", "podium__name", row.name);
      if (row.name) nameEl.title = row.name;
      line.appendChild(nameEl);
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

  function buildToggleBar() {
    return el("div", "series-card__toggle-bar");
  }

  function addToggleSection(toggleBar, card, label, contentEl) {
    contentEl.classList.add("series-card__group--collapsible");
    var btn = el("button", "series-card__toggle-btn", label);
    toggleBar.appendChild(btn);
    card.appendChild(contentEl);
    btn.addEventListener("click", function () {
      var visible = contentEl.classList.toggle("is-visible");
      btn.classList.toggle("is-active", visible);
    });
  }

  function buildRegulationBlock(reg) {
    var wrap = el("div", "series-card__group");
    wrap.appendChild(el("div", "series-card__group-title", "車両規定: " + reg.class_name));
    wrap.appendChild(el("p", "panel__note series-card__chart-note", reg.description));
    return wrap;
  }

  function buildVehicleCard(v, featured) {
    var card = el("div", "vehicle-card" + (featured ? " vehicle-card--gr" : ""));
    if (v.photo && v.photo.src) {
      var figure = el("div", "vehicle-card__photo");
      var img = el("img");
      img.src = v.photo.src;
      img.alt = v.manufacturer + " " + v.model;
      img.loading = "lazy";
      figure.appendChild(img);
      card.appendChild(figure);
    }

    var body = el("div", "vehicle-card__body");
    var titleLine = el("div", "vehicle-card__title-line");
    titleLine.appendChild(el("h4", "vehicle-card__title", v.manufacturer + " " + v.model));
    if (featured) titleLine.appendChild(el("span", "gr-tag", "GR COROLLA"));
    body.appendChild(titleLine);
    if (v.description) body.appendChild(el("p", "vehicle-card__desc", v.description));
    if (v.team) body.appendChild(el("p", "vehicle-card__meta", "開発/運用: " + v.team));
    if (v.debut) body.appendChild(el("p", "vehicle-card__meta", "参戦開始: " + v.debut));

    if (v.specs && v.specs.length > 0) {
      var specList = el("dl", "spec-list");
      v.specs.forEach(function (spec) {
        specList.appendChild(el("dt", null, CAR_SPEC_LABELS[spec.key] || spec.key));
        specList.appendChild(el("dd", null, spec.value));
      });
      body.appendChild(specList);
    }

    if (v.source_url) {
      var link = el("a", "series-card__link", "出典/公式ページを見る ↗");
      link.href = v.source_url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      body.appendChild(link);
    }

    if (v.photo && v.photo.src) {
      var credit = el("p", "vehicle-card__credit");
      credit.appendChild(document.createTextNode("写真" + (v.photo.note ? "(" + v.photo.note + ")" : "") + ": "));
      var creditLink = el("a", null, v.photo.credit + " (" + v.photo.license + ")");
      creditLink.href = v.photo.source_url;
      creditLink.target = "_blank";
      creditLink.rel = "noopener noreferrer";
      credit.appendChild(creditLink);
      credit.appendChild(document.createTextNode("、Wikimedia Commonsより"));
      body.appendChild(credit);
    }

    card.appendChild(body);
    return card;
  }

  function buildVehicleSection(vehicleInfo) {
    var wrap = el("div", "series-card__group");
    wrap.appendChild(el("div", "series-card__group-title", "参戦車両"));
    wrap.appendChild(buildVehicleCard(vehicleInfo.vehicle, true));
    if (vehicleInfo.rivals && vehicleInfo.rivals.length > 0) {
      wrap.appendChild(el("div", "vehicle-card__rivals-label", "主なライバル車"));
      vehicleInfo.rivals.forEach(function (rival) {
        wrap.appendChild(buildVehicleCard(rival, false));
      });
    }
    return wrap;
  }

  function buildMotorsportsPanel(icon, section) {
    var panel = el("section", "panel panel--full");
    panel.id = "section-motorsports";
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

      var rounds = s.schedule || [];
      var nextRace = rounds.filter(function (r) { return r.status === "upcoming"; })[0];
      var lastRace = rounds.filter(function (r) { return r.status === "completed"; }).slice(-1)[0];
      var nextRow = buildScheduleNextRow("次戦", nextRace);
      if (nextRow) card.appendChild(nextRow);

      var toggleBar = buildToggleBar();
      card.appendChild(toggleBar);
      addToggleSection(toggleBar, card, "レース日程", buildScheduleBlock(s));
      addToggleSection(toggleBar, card, "ランキング", buildRankingBlock(s));

      var lastRow = buildScheduleNextRow("直近", lastRace, "schedule-next--recent");
      if (lastRow) card.appendChild(lastRow);

      if (s.vehicle_info) {
        addToggleSection(toggleBar, card, "車両規定", buildRegulationBlock(s.vehicle_info.regulation));
        addToggleSection(toggleBar, card, "参戦車両", buildVehicleSection(s.vehicle_info));
      }

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

  function buildNurburgringRow(entry) {
    // 順位・タイム・車名・概要/Spec/動画/出典ボタンを1行に並べた省スペースレイアウト。
    // 概要とスペックは既定非表示で、ボタンで行の下に個別展開される。
    var row = el("div", "nurburgring-row" + (entry.is_gr_corolla ? " nurburgring-row--gr" : ""));

    row.appendChild(el("span", "nurburgring-row__rank", String(entry.rank)));
    row.appendChild(el("span", "nurburgring-row__time", entry.lap_time));
    var nameParts = [entry.manufacturer, entry.model].filter(Boolean).join(" ");
    row.appendChild(el("span", "nurburgring-row__name", nameParts));
    if (entry.is_gr_corolla) row.appendChild(el("span", "gr-tag", "GR COROLLA"));

    var actions = el("div", "nurburgring-row__actions");
    row.appendChild(actions);

    var overviewParts = [];
    if (entry.year) overviewParts.push(String(entry.year));
    if (entry.note) overviewParts.push(entry.note);
    var hasOverview = overviewParts.length > 0;
    var overviewBtn, overviewWrap;
    if (hasOverview) {
      overviewBtn = el("button", "tab-group__btn nurburgring-row__toggle-btn", "概要");
      actions.appendChild(overviewBtn);
    }

    var hasSpecs = entry.specs && entry.specs.length > 0;
    var specBtn, specWrap;
    if (hasSpecs) {
      specBtn = el("button", "tab-group__btn nurburgring-row__toggle-btn", "Spec");
      actions.appendChild(specBtn);
    }

    if (entry.youtube_url) {
      var ytLink = el("a", "series-card__link nurburgring-row__toggle-btn", "オンボード動画を見る ↗");
      ytLink.href = entry.youtube_url;
      ytLink.target = "_blank";
      ytLink.rel = "noopener noreferrer";
      actions.appendChild(ytLink);
    }
    if (entry.source_url) {
      var srcLink = el("a", "series-card__link nurburgring-row__toggle-btn", "出典を見る ↗");
      srcLink.href = entry.source_url;
      srcLink.target = "_blank";
      srcLink.rel = "noopener noreferrer";
      actions.appendChild(srcLink);
    }

    if (hasOverview) {
      overviewWrap = el("div", "nurburgring-row__overview");
      overviewWrap.appendChild(el("p", null, overviewParts.join(" · ")));
      row.appendChild(overviewWrap);
      overviewBtn.addEventListener("click", function () {
        var visible = overviewWrap.classList.toggle("is-visible");
        overviewBtn.classList.toggle("is-active", visible);
      });
    }

    if (hasSpecs) {
      specWrap = el("div", "nurburgring-row__specs");
      var specList = el("dl", "spec-list");
      entry.specs.forEach(function (spec) {
        specList.appendChild(el("dt", null, CAR_SPEC_LABELS[spec.key] || spec.key));
        specList.appendChild(el("dd", null, spec.value));
      });
      specWrap.appendChild(specList);
      row.appendChild(specWrap);
      specBtn.addEventListener("click", function () {
        var visible = specWrap.classList.toggle("is-visible");
        specBtn.classList.toggle("is-active", visible);
      });
    }

    return row;
  }

  function buildNurburgringPanel(icon, nurData) {
    var panel = el("section", "panel panel--full");
    panel.id = "section-nurburgring";
    var cars = nurData.cars || [];
    panel.appendChild(buildPanelHeader(icon, "ニュルブルクリンク ラップタイムランキング", cars.length));
    panel.appendChild(
      el(
        "p",
        "panel__note",
        "ニュルブルクリンク・ノルドシュライフェでの公道走行可能な市販車(限定生産モデル含む)の" +
          "ラップタイムを速い順にまとめた、手動収集の静的リファレンスです。30分毎の自動収集対象では" +
          "なく、不定期に更新します。純レーシングカー・プロトタイプ・ワンメイクレーサー等、公道登録" +
          "できない車両は対象外としています。タイムは年式・タイヤ・オプション装備・計測区間により" +
          "条件が異なるため、単純比較にはご注意ください。"
      )
    );
    if (nurData.note) panel.appendChild(el("p", "panel__note", nurData.note));

    if (cars.length === 0) {
      panel.appendChild(el("p", "panel__empty", "現在、該当する情報はありません。"));
      return panel;
    }

    var list = el("div", "nurburgring-list");
    cars.forEach(function (entry) {
      list.appendChild(buildNurburgringRow(entry));
    });
    panel.appendChild(list);
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

  function countRecent(items) {
    return (items || []).filter(isWithin24h).length;
  }

  function buildDigestPanel(data) {
    var sections = (data && data.sections) || {};
    var rows = [];

    if (sections.toyota_news) {
      rows.push({ key: "toyota_news", label: sections.toyota_news.label, count: countRecent(sections.toyota_news.items) });
    }
    if (sections.motorsports && sections.motorsports.series) {
      var msCount = 0;
      Object.values(sections.motorsports.series).forEach(function (s) {
        msCount += countRecent(s.topics) + countRecent(s.results) + countRecent(s.standings);
      });
      rows.push({ key: "motorsports", label: sections.motorsports.label, count: msCount });
    }
    if (sections.events) {
      rows.push({ key: "events", label: sections.events.label, count: countRecent(sections.events.items) });
    }
    if (sections.youtube_popular || sections.youtube_new || sections.youtube_popular_jp || sections.youtube_new_jp) {
      var ytAll = mergeDedupItems(
        mergeDedupItems((sections.youtube_popular && sections.youtube_popular.items) || [], (sections.youtube_new && sections.youtube_new.items) || []),
        mergeDedupItems((sections.youtube_popular_jp && sections.youtube_popular_jp.items) || [], (sections.youtube_new_jp && sections.youtube_new_jp.items) || [])
      );
      rows.push({ key: "youtube", label: "YouTube動画", count: countRecent(ytAll) });
    }
    if (sections.media_reviews) {
      rows.push({ key: "media_reviews", label: sections.media_reviews.label, count: countRecent(sections.media_reviews.items) });
    }
    if (sections.social_buzz) {
      rows.push({ key: "social_buzz", label: sections.social_buzz.label, count: countRecent(sections.social_buzz.items) });
    }
    if (sections.complaints) {
      rows.push({ key: "complaints", label: sections.complaints.label, count: countRecent(sections.complaints.items) });
    }

    var totalCount = rows.reduce(function (sum, r) { return sum + r.count; }, 0);
    var panel = el("section", "panel panel--full digest-panel");
    panel.appendChild(buildPanelHeader("clock", "直近24時間ダイジェスト", totalCount));
    panel.appendChild(
      el("p", "panel__note", "各セクションで過去24時間以内に更新された件数です(記事・動画・レース関連ニュース等の合計)。クリックで該当セクションへ移動します。")
    );

    var list = el("div", "digest-list");
    rows.forEach(function (r) {
      var row = el("a", "digest-row" + (r.count > 0 ? " digest-row--active" : ""));
      row.href = "#section-" + r.key;
      row.addEventListener("click", function (evt) {
        var target = document.getElementById("section-" + r.key);
        if (target) {
          evt.preventDefault();
          target.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
      row.appendChild(el("span", "digest-row__label", r.label));
      row.appendChild(el("span", "digest-row__count", String(r.count)));
      list.appendChild(row);
    });
    panel.appendChild(list);
    return panel;
  }

  function render(data, nurData) {
    buildStats(data);

    board.innerHTML = "";
    board.appendChild(buildDigestPanel(data));
    LAYOUT.forEach(function (entry) {
      if (entry.key === "youtube") {
        var hasYoutubeData =
          data.sections &&
          (data.sections.youtube_popular ||
            data.sections.youtube_new ||
            data.sections.youtube_popular_jp ||
            data.sections.youtube_new_jp);
        if (!hasYoutubeData) return;
        board.appendChild(buildYoutubePanel(entry.icon, data));
        return;
      }
      if (entry.key === "nurburgring") {
        // data/nurburgring.jsonという別ファイルの手動更新の静的データで、
        // 30分毎の自動収集対象(data.sections)には含まれないため専用に扱う。
        if (nurData) board.appendChild(buildNurburgringPanel(entry.icon, nurData));
        return;
      }
      var section = data.sections && data.sections[entry.key];
      if (!section) return;
      var panel;
      if (entry.key === "motorsports") {
        panel = buildMotorsportsPanel(entry.icon, section);
      } else if (entry.key === "complaints") {
        panel = buildComplaintsPanel(entry.icon, section);
      } else {
        panel = buildGenericPanel(entry.icon, section, entry.size, entry.key);
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

  function fetchJson(path) {
    return fetch(path, { cache: "no-store" }).then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    });
  }

  fetchJson("data/latest.json")
    .then(function (data) {
      fetchJson("data/nurburgring.json")
        .catch(function () { return null; })
        .then(function (nurData) {
          render(data, nurData);
        });
    })
    .catch(function (err) {
      renderError("ダッシュボードデータの読み込みに失敗しました(" + err.message + ")。");
    });
})();
