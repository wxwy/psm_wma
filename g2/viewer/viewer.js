(() => {
  "use strict";

  // The compact output is served by ordinary Python http.server. Completed
  // Episode directories are discovered live, without a separate API server.
  const $ = id => document.getElementById(id);
  const SOURCES = [
    ["floor_top", "俯视 · Floor top", "2 Hz · GLOBAL"],
    ["upper_up", "仰视 · Upper up", "2 Hz · GLOBAL"],
    ["plus_X", "+X · 侧视", "2 Hz · GLOBAL"],
    ["minus_X", "−X · 侧视", "2 Hz · GLOBAL"],
    ["plus_Y", "+Y · 侧视", "2 Hz · GLOBAL"],
    ["minus_Y", "−Y · 侧视", "2 Hz · GLOBAL"],
    ["left", "Left · 主相机", "20 Hz · CAMERA"],
    ["right", "Right · 主相机", "20 Hz · CAMERA"],
    ["wrist", "Wrist · 腕部相机", "20 Hz · CAMERA"],
  ];
  const VIDEO = new Set(["left", "right", "wrist"]);
  const ALL = new Set(SOURCES.map(v => v[0]));
  const ISLAND_DIRECTIONS = ["plus_X", "minus_X", "plus_Y", "minus_Y"];
  // Strict source tokens keep saved layouts and URL paths traversal-safe.
  const ISLAND_SOURCE_RE = /^island:(island_[0-9]+_entity_[0-9]+):(plus_X|minus_X|plus_Y|minus_Y)$/;
  const ISLAND_ID_RE = /^island_[0-9]+_entity_[0-9]+$/;
  const parseIslandSource = source => {
    const match = typeof source === "string" ? source.match(ISLAND_SOURCE_RE) : null;
    return match ? {island: match[1], direction: match[2]} : null;
  };
  const validSource = source => ALL.has(source) || parseIslandSource(source) !== null;

  function islandGroups(manifest) {
    if (!manifest || !Array.isArray(manifest.states)) return [];
    const byId = new Map();
    for (const entry of manifest.states) {
      if (!Array.isArray(entry.view_pngs)) continue;
      const refs = entry.view_refs && typeof entry.view_refs === "object" &&
        !Array.isArray(entry.view_refs) ? Object.keys(entry.view_refs) : [];
      const views = new Set([...entry.view_pngs, ...refs]);
      for (const id of entry.islands || []) {
        if (typeof id !== "string" || !ISLAND_ID_RE.test(id)) continue;
        for (const direction of ISLAND_DIRECTIONS) {
          if (!views.has("islands/" + id + "/" + direction + ".png")) continue;
          if (!byId.has(id)) byId.set(id, new Set());
          byId.get(id).add(direction);
        }
      }
    }
    return [...byId.keys()].sort((a,b) => a.localeCompare(b,undefined,{numeric:true}))
      .map((id,index) => ({
        id,
        label: "Island " + (index + 1) + " · " + id,
        choices: ISLAND_DIRECTIONS.filter(direction => byId.get(id).has(direction))
          .map(direction => ({
            value: "island:" + id + ":" + direction,
            label: direction.replace("plus_","+").replace("minus_","−"),
          })),
      }));
  }

  function sourceMetadata(source) {
    const known = SOURCES.find(x => x[0] === source);
    if (known) return known;
    const island = parseIslandSource(source);
    if (!island) throw Error("不支持的展示视角");
    return [source, island.island + " · " + island.direction, "2 Hz · ISLAND"];
  }

  function fillSourceSelect(select, selected) {
    select.replaceChildren();
    const group = (name, values) => {
      const optgroup = document.createElement("optgroup");
      optgroup.label = name;
      for (const [value,label] of values) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = label;
        optgroup.append(option);
      }
      select.append(optgroup);
    };
    group("全局 SixView", SOURCES.filter(x => !VIDEO.has(x[0])));
    group("机器人相机", SOURCES.filter(x => VIDEO.has(x[0])));
    const islands = islandGroups(state.manifest);
    for (const island of islands) {
      group(island.label, island.choices.map(c => [c.value, "Island · " + c.label]));
    }
    const options = [...select.querySelectorAll("option")];
    if (!options.some(opt => opt.value === selected)) {
      // Preserve a saved layout across Episodes with different Island IDs,
      // but never advertise obsolete Island views as playable choices.
      const missing = document.createElement("option");
      missing.value = selected;
      missing.textContent = sourceMetadata(selected)[1] + "（当前 Episode 无此视角）";
      missing.disabled = true;
      select.append(missing);
    }
    select.value = selected;
  }
  const CAMERA = {
    left: "observation.images.robot0_agentview_left",
    right: "observation.images.robot0_agentview_right",
    wrist: "observation.images.robot0_eye_in_hand",
  };
  const STORAGE = "psm-g2-viewer-layout-v1";
  const uuid = () => typeof crypto !== "undefined" && crypto.randomUUID ?
    crypto.randomUUID() : Date.now() + "-" + Math.random().toString(36).slice(2);
  const pad = (n, w = 6) => String(n).padStart(w, "0");
  const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi, n));
  const fmt = n => {
    const s = Number.isFinite(n) ? n : 0;
    return pad(Math.floor(s / 60), 2) + ":" + pad(Math.floor(s % 60), 2) +
      "." + pad(Math.floor((s % 1) * 100), 2);
  };

  function startingLayout() {
    return [
      {id: uuid(), blocks: [
        {id: uuid(), source: "floor_top"}, {id: uuid(), source: "left"},
        {id: uuid(), source: "wrist"}]},
      {id: uuid(), blocks: [
        {id: uuid(), source: "plus_X"}, {id: uuid(), source: "minus_X"},
        {id: uuid(), source: "plus_Y"}]},
    ];
  }

  function readLayout() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE));
      if (Array.isArray(saved) && saved.length > 0 && saved.length <= 30 &&
          saved.every(r => typeof r.id === "string" &&
            Array.isArray(r.blocks) && r.blocks.length <= 5 &&
            r.blocks.every(b => typeof b.id === "string" && validSource(b.source)))) {
        const ids = saved.flatMap(r => [r.id, ...r.blocks.map(b => b.id)]);
        if (new Set(ids).size === ids.length) return saved;
      }
    } catch (_) {}
    return startingLayout();
  }

  const state = {
    catalog: null, task: null, episode: null, manifest: null, available: [],
    rows: readLayout(), media: [], time: 0, duration: 0, playing: false,
    speed: 1, lastSpatial: -1, frameHandle: null, drag: null,
    token: 0, fallbackTime: 0, fallbackStart: 0, clockFailed: false,
    toastTimer: null, preload: new Map(),
    mode: "server", baseCatalog: null, localSource: null,
    localVideoRoot: null, localVideoUrls: new Map(),
    sourceRootUrl: "../",
    serverBrowseToken: 0, serverBrowseEntries: [],
  };

  function saveLayout() {
    try { localStorage.setItem(STORAGE, JSON.stringify(state.rows)); }
    catch (_) {}
  }

  function toast(message) {
    const el = $("toast");
    el.textContent = message; el.hidden = false;
    clearTimeout(state.toastTimer);
    state.toastTimer = setTimeout(() => { el.hidden = true; }, 3500);
  }

  function showStatus(message, kind = "") {
    const el = $("system-status");
    el.className = "system-pill " + kind;
    el.lastElementChild.textContent = message;
  }

  async function fetchJson(path) {
    const res = await fetch(path, {cache: "no-store"});
    if (!res.ok) throw Error("HTTP " + res.status + "：" + path);
    return res.json();
  }

  async function listDirectory(path) {
    const res = await fetch(path, {cache: "no-store"});
    if (res.status === 404) return [];
    if (!res.ok) throw Error("无法读取目录：" + res.status);
    const doc = new DOMParser().parseFromString(await res.text(), "text/html");
    return [...doc.querySelectorAll("a[href]")].map(a => {
      const href = a.getAttribute("href");
      try { return decodeURIComponent(href.split("?")[0]).replace(/\/$/, ""); }
      catch (_) { return ""; }
    });
  }

  function taskDirectory() {
    const base = state.task.rootUrl || "../";
    return base + "tasks/" + encodeURIComponent(state.task.name) + "/episodes/";
  }

  function episodeDirectory() {
    return taskDirectory() + "episode_" + pad(state.episode.global_id) + "/";
  }

  function videoUrl(source) {
    if (!state.episode || !state.task || !CAMERA[source] ||
        !state.task.video_path || !state.task.source_dir) return "";
    const task = state.task, local = state.episode.local_id;
    const chunk = pad(Math.floor(local / task.chunks_size), 3);
    const path = task.video_path
      .replace("{episode_chunk:03d}", chunk)
      .replace("{video_key}", CAMERA[source])
      .replace("{episode_index:06d}", pad(local));
    const folder = task.source_dir.split("/").map(encodeURIComponent).join("/");
    return "./source_videos/" + folder + "/" + path;
  }

  async function resolveCameraUrl(source) {
    if (!state.episode || !state.task) return "";
    if (state.mode === "local" && state.localVideoRoot) {
      const ep = state.episode, task = state.task;
      const key = task.id + "/" + ep.global_id + "/" + source;
      if (state.localVideoUrls.has(key)) return state.localVideoUrls.get(key);
      const file = await G2DirectorySource.videoFile(
        state.localVideoRoot, task, ep, CAMERA[source]);
      if (file) {
        const blobUrl = URL.createObjectURL(file);
        state.localVideoUrls.set(key, blobUrl);
        return blobUrl;
      }
    }
    // Preserve the existing same-origin LeRobot camera source if available.
    return videoUrl(source);
  }

  function clearVideoObjectUrls() {
    for (const blobUrl of state.localVideoUrls.values())
      URL.revokeObjectURL(blobUrl);
    state.localVideoUrls.clear();
  }

  function viewPath(source, index) {
    const entry = state.manifest.states[index];
    const island = parseIslandSource(source);
    if (!island && !ALL.has(source)) return null;
    const relative = island
      ? "islands/" + island.island + "/" + island.direction + ".png"
      : "sixview/" + source + ".png";
    // Both remote and local dataset access must use the SAME direct owner
    // state for v2 refs. v1 files continue to resolve to the current frame.
    let owner=index;
    if (!entry.view_pngs.includes(relative)) {
      const refs=entry.view_refs;
      if (!refs || Array.isArray(refs) || typeof refs !== "object") return null;
      const ref=refs[relative];
      if (!ref || typeof ref !== "object" || ref.path !== relative ||
          !Number.isInteger(ref.ref_state) ||
          ref.ref_state < 0 || ref.ref_state >= index) return null;
      owner=ref.ref_state;
      const original=state.manifest.states[owner];
      if (!original || !Array.isArray(original.view_pngs) ||
          !original.view_pngs.includes(relative)) return null;
    }
    const stateRow=state.manifest.states[owner];
    const statePath = "state_" + pad(owner) +
      "_frame_" + pad(stateRow.frame) + "/" + relative;
    return state.mode === "local" ? "g2local:" + statePath :
      episodeDirectory() + statePath;
  }

  function spatialAt(time) {
    if (!state.manifest) return -1;
    const frames = state.manifest.states;
    const n = time * state.catalog.source_fps;
    let lo = 0, hi = frames.length;
    while (lo < hi) {
      const mid = Math.floor((lo + hi) / 2);
      if (frames[mid].frame <= n + 0.00001) lo = mid + 1;
      else hi = mid;
    }
    return Math.max(0, lo - 1);
  }

  function fillSelect(el, options, desired) {
    el.replaceChildren(...options.map(pair => {
      const opt = document.createElement("option");
      opt.value = String(pair[0]); opt.textContent = pair[1];
      return opt;
    }));
    if (options.some(pair => String(pair[0]) === String(desired)))
      el.value = String(desired);
  }

  function transportEnabled(enabled) {
    for (const id of ["scrub", "play", "prev-frame", "next-frame"])
      $(id).disabled = !enabled;
    $("playback-status").textContent = enabled ? "已同步" : "待选择";
  }

  function videos() {
    return state.media.filter(m => m.video).map(m => m.video);
  }

  function updatePlayLabel() {
    $("play").innerHTML = state.playing ? "Ⅱ <span>暂停</span>" : "▶ <span>播放</span>";
    $("play").setAttribute("aria-label", state.playing ? "暂停" : "播放");
  }

  function pause() {
    state.playing = false;
    if (state.frameHandle !== null) {
      cancelAnimationFrame(state.frameHandle);
      state.frameHandle = null;
    }
    $("clock-video").pause();
    for (const v of videos()) v.pause();
    updatePlayLabel();
  }

  function syncVideos(force = false) {
    const videoNodes = [$("clock-video"), ...videos()];
    for (const v of videoNodes) {
      v.playbackRate = state.speed;
      if (v.readyState >= 1 &&
          (force || Math.abs(v.currentTime - state.time) > 0.2)) {
        try { v.currentTime = state.time; } catch (_) {}
      }
    }
  }

  function seek(time, force = false) {
    if (!state.manifest) return;
    state.time = clamp(time, 0, state.duration);
    state.fallbackTime = state.time;
    state.fallbackStart = performance.now();
    syncVideos(force);
    updateTimeline();
  }

  function step(delta) {
    if (!state.manifest) return;
    pause();
    const index = spatialAt(state.time);
    const frames = state.manifest.states;
    const originalFrame = state.time * state.catalog.source_fps;
    let dest = delta > 0 ?
      (frames[index].frame <= originalFrame + 0.00001 ? index + 1 : index) :
      (frames[index].frame < originalFrame - 0.00001 ? index : index - 1);
    dest = clamp(dest, 0, frames.length - 1);
    seek(frames[dest].frame / state.catalog.source_fps, true);
  }

  function clockTick(now) {
    if (!state.playing || !state.manifest) return;
    const clock = $("clock-video");
    const useVideo = !state.clockFailed && clock.readyState >= 1 && !clock.paused;
    const elapsed = (now - state.fallbackStart) / 1000 * state.speed;
    state.time = clamp(useVideo ? clock.currentTime : state.fallbackTime + elapsed,
      0, state.duration);
    updateTimeline();
    if (Math.floor(now / 600) !== Math.floor((now - 16) / 600))
      syncVideos(false);
    if (state.time >= state.duration - 0.02) {
      seek(state.duration, true); pause(); return;
    }
    state.frameHandle = requestAnimationFrame(clockTick);
  }

  async function play() {
    if (!state.manifest) return;
    if (state.playing) { pause(); return; }
    if (state.time >= state.duration - 0.03) seek(0, true);
    state.playing = true;
    state.fallbackTime = state.time;
    state.fallbackStart = performance.now();
    syncVideos(true);
    updatePlayLabel();
    try { await $("clock-video").play(); }
    catch (_) { state.clockFailed = true; }
    if (!state.playing) return;
    for (const v of videos()) v.play().catch(() => {});
    state.frameHandle = requestAnimationFrame(clockTick);
  }

  function decodedImage(path) {
    // Return a shared decoded image. Awaiting a preloaded image alone is not
    // enough if the visible <img>.src is changed before paint. The final swap
    // occurs by drawing synchronously into a persistent visible canvas.
    const known = state.preload.get(path);
    if (known) return known;
    const local = path.startsWith("g2local:");
    const episode = state.episode;
    const decode = url => new Promise((resolve, reject) => {
      const image = new Image();
      image.decoding = "async";
      image.onload = () => {
        const decoding = typeof image.decode === "function" ?
          image.decode() : Promise.resolve();
        decoding.then(() => resolve(image), reject);
      };
      image.onerror = () => reject(new Error("PNG 图片加载失败"));
      image.src = url;
    });
    // Do not defer existing HTTP image loads by an extra microtask; the local
    // FileSystem handle has an inherently asynchronous File -> blob URL step.
    const promise = local ?
      state.localSource.getUrl(episode, path.slice("g2local:".length)).then(decode) :
      decode(path);
    state.preload.set(path, promise);
    // Preloading is opportunistic; a failure should not cause an unhandled rejection.
    promise.catch(() => {
      if (state.preload.get(path) === promise) state.preload.delete(path);
    });
    while (state.preload.size > 64)
      state.preload.delete(state.preload.keys().next().value);
    return promise;
  }

  function preloadNext(index) {
    if (index + 1 >= state.manifest.states.length) return;
    const sources = [...new Set(state.media.filter(x => !x.video).map(x => x.source))];
    // Prime the next two 2 Hz spatial frames, including the large floor_top PNG.
    for (let next = index + 1; next <= Math.min(index + 2,
         state.manifest.states.length - 1); next++) {
      for (const source of sources) {
        const path = viewPath(source, next);
        if (path) void decodedImage(path);
      }
    }
  }

  function displayFrame(index) {
    if (!state.manifest) return;
    const frame = state.manifest.states[index].frame;
    for (const tile of state.media) {
      if (tile.video) continue;
      // Generation tokens cancel stale async results during fast scrubbing.
      const generation = ++tile.generation;
      const path = viewPath(tile.source, index);
      if (!path) {
        tile.displayedPath = null;
        tile.canvas.hidden = true;
        tile.fallback.hidden = false;
        tile.fallbackText.textContent =
          parseIslandSource(tile.source) ? "该时刻未生成这个 Island 的方向视图" :
          tile.source === "upper_up" ? "该时刻没有仰视图" : "该视角未生成";
        tile.status.textContent = "NOT GENERATED";
        continue;
      }
      if (tile.displayedPath === path) {
        tile.status.textContent = "F " + pad(frame);
        continue;
      }
      // Retain the fully drawn previous frame while fetching / decoding.
      tile.status.textContent = "加载 F " + pad(frame);
      void decodedImage(path).then(image => {
        if (tile.disposed || tile.generation !== generation) return;
        const canvas = tile.canvas;
        const context = canvas.getContext("2d", {alpha: false});
        if (!context) throw Error("浏览器不支持 Canvas 2D");
        // JS runs to completion before painting: canvas reset + draw are atomic.
        canvas.width = image.naturalWidth;
        canvas.height = image.naturalHeight;
        context.drawImage(image, 0, 0);
        canvas.hidden = false;
        tile.fallback.hidden = true;
        tile.displayedPath = path;
        tile.status.textContent = "F " + pad(frame);
      }).catch(() => {
        if (tile.disposed || tile.generation !== generation) return;
        // Never flash the placeholder over a previously rendered valid frame.
        tile.status.textContent = "加载失败 · 保留上一帧";
        if (tile.canvas.hidden) {
          tile.fallback.hidden = false;
          tile.fallbackText.textContent = "图片读取失败";
        }
      });
    }
    preloadNext(index);
  }

  function updateTimeline() {
    if (!state.manifest) {
      $("time-current").textContent = fmt(0);
      $("time-total").textContent = fmt(state.duration);
      $("frame-label").textContent = "空间帧 — / —";
      $("source-frame-label").textContent = "原始帧 —";
      $("scrub").value = "0";
      $("scrub").style.setProperty("--progress", "0%");
      return;
    }
    const idx = spatialAt(state.time);
    const entry = state.manifest.states[idx];
    $("time-current").textContent = fmt(state.time);
    $("time-total").textContent = fmt(state.duration);
    $("scrub").value = String(Math.round(1000 * state.time / state.duration));
    $("scrub").style.setProperty("--progress", 100 * state.time / state.duration + "%");
    $("frame-label").textContent = "空间帧 " + (idx + 1) +
      " / " + state.manifest.states.length;
    $("source-frame-label").textContent =
      "原始帧 " + entry.frame + " / " + (state.episode.frames - 1);
    $("playback-status").textContent = state.playing ? "播放中" : "已同步";
    if (idx !== state.lastSpatial) {
      state.lastSpatial = idx;
      displayFrame(idx);
    }
  }

  async function loadEpisode(globalId) {
    const item = state.task?.episodes.find(ep => ep.global_id === globalId);
    if (!item) return;
    const token = ++state.token;
    pause();
    clearVideoObjectUrls();
    if (state.mode === "local") state.localSource.release();
    state.episode = item;
    state.manifest = null;
    state.time = 0;
    state.duration = item.frames / state.catalog.source_fps;
    state.lastSpatial = -1;
    state.preload.clear();
    $("instruction-text").textContent = item.instruction || "未提供任务指令";
    $("task-tag").textContent = state.task.name;
    $("global-tag").textContent = "#" + pad(item.global_id);
    $("time-total").textContent = fmt(state.duration);
    transportEnabled(false);
    showStatus("校验数据", "");
    try {
      const base = state.mode === "local" ? "" : episodeDirectory();
      const [complete, manifest] = state.mode === "local" ?
        [item.complete, item.manifest] : await Promise.all([
          fetchJson(base + "COMPLETE.json"),
          fetchJson(base + "episode_manifest.json"),
        ]);
      if (token !== state.token) return;
      if (complete.complete !== true ||
          Number(complete.episode_id) !== item.global_id ||
          complete.state_count !== manifest.states?.length ||
          manifest.state_count !== manifest.states.length ||
          !manifest.states.length) {
        throw Error("Episode 尚未完整生成");
      }
      // A custom HTTP source may contain Episodes outside the original catalog.
      // Their exact final frame is derived from the selected manifest.
      item.frames = Math.max(item.frames || 0,
        manifest.states.at(-1).frame + 1);
      state.duration = item.frames / state.catalog.source_fps;
      $("time-total").textContent = fmt(state.duration);
      let previous = -1;
      for (const entry of manifest.states) {
        if (!Number.isInteger(entry.frame) || entry.frame <= previous ||
            entry.frame >= item.frames || !Array.isArray(entry.view_pngs))
          throw Error("空间帧索引与原始数据不一致");
        previous = entry.frame;
      }
      state.manifest = manifest;
      state.clockFailed = false;
      $("clock-video").pause();
      $("clock-video").removeAttribute("src");
      $("clock-video").load();
      const cameraToken = token;
      void resolveCameraUrl("left").then(url => {
        if (cameraToken !== state.token) return;
        if (!url) { state.clockFailed = true; return; }
        $("clock-video").src = url;
        $("clock-video").load();
      }).catch(() => {
        if (cameraToken !== state.token) return;
        state.clockFailed = true;
      });
      transportEnabled(true);
      renderLayout();
      seek(0, true);
      showStatus("已连接 · " + manifest.states.length + " 空间帧", "ready");
    } catch (error) {
      if (token !== state.token) return;
      state.manifest = null;
      renderLayout();
      transportEnabled(false);
      showStatus("数据不可用", "issue");
      toast(error.message);
    }
  }

  async function refreshEpisodes(preserve = true) {
    if (!state.task) return;
    const task = state.task;
    const token = ++state.token;
    pause();
    const picker = $("episode-select");
    picker.disabled = true;
    fillSelect(picker, [["", "正在扫描已完成的 Episode…"]], "");
    showStatus("刷新任务目录", "");
    try {
      const entries = state.mode === "local" ? null :
        await listDirectory(taskDirectory());
      if (token !== state.token || task !== state.task) return;
      const globalIds = entries ?
        new Set(entries.filter(n => /^episode_\d{6}$/.test(n))
          .map(n => Number(n.slice(8)))) : null;
      const completed = state.mode === "local" ? task.episodes :
        task.episodes.filter(ep => globalIds.has(ep.global_id));
      $("available-count").textContent = completed.length + " / " +
        task.count + " 已生成";
      if (!completed.length) {
        state.episode = null; state.manifest = null;
        state.time = 0; state.duration = 0;
        $("instruction-text").textContent = "此任务尚无完成的 Episode，稍后可刷新列表。";
        fillSelect(picker, [["", "暂无完成的 Episode"]], "");
        transportEnabled(false);
        renderLayout();
        showStatus("等待已完成数据");
        return;
      }
      const old = preserve ? state.episode?.global_id : undefined;
      const preferred = completed.some(ep => ep.global_id === old) ?
        old : completed[0].global_id;
      fillSelect(picker, completed.map(ep =>
        [ep.global_id, "EP " + pad(ep.local_id, 3) + " · 全局 " +
          pad(ep.global_id) + " · " + fmt(ep.frames / 20)]), preferred);
      picker.disabled = false;
      state.available = completed;
      await loadEpisode(Number(picker.value));
    } catch (error) {
      if (token !== state.token) return;
      fillSelect(picker, [["", "列表不可用，请重试"]], "");
      showStatus("读取失败", "issue");
      toast(error.message);
    }
  }

  async function chooseTask(taskName) {
    const task = state.catalog?.tasks.find(t => (t.id || t.name) === taskName);
    if (!task) return;
    pause();
    state.task = task; state.episode = null; state.manifest = null;
    state.time = 0; state.duration = 0;
    if (state.mode === "server") {
      try { localStorage.setItem("psm-g2-viewer-task", taskName); } catch (_) {}
    }
    $("instruction-text").textContent = "正在读取已完成 Episode…";
    $("task-tag").textContent = task.name;
    $("global-tag").textContent = "—";
    await refreshEpisodes(false);
  }

  function newTile(block, row, index) {
    const card = document.createElement("article");
    card.className = "tile"; card.dataset.block = block.id;
    const toolbar = document.createElement("div");
    toolbar.className = "tile-toolbar";
    const handle = document.createElement("span");
    handle.className = "drag-handle"; handle.textContent = "⠿";
    handle.title = "拖动到其他行或列";
    handle.draggable = true; handle.tabIndex = 0;
    handle.setAttribute("aria-label", "拖动展示块");
    handle.addEventListener("dragstart", event => {
      state.drag = block.id;
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", block.id);
      requestAnimationFrame(() => card.classList.add("dragging"));
    });
    handle.addEventListener("dragend", clearDrag);
    const select = document.createElement("select");
    select.className = "tile-select"; select.title = "切换展示来源";
    select.setAttribute("aria-label", "展示块 " + (index + 1) + " 视角");
    fillSourceSelect(select, block.source);
    select.addEventListener("change", () => {
      block.source = select.value; saveLayout(); renderLayout();
    });
    const remove = document.createElement("button");
    remove.type = "button"; remove.className = "tile-remove";
    remove.title = "移除展示块"; remove.textContent = "×";
    remove.addEventListener("click", () => {
      row.blocks.splice(index, 1); saveLayout(); renderLayout();
    });
    toolbar.append(handle, select, remove);
    const visual = document.createElement("div"); visual.className = "tile-visual";
    const fallback = document.createElement("div"); fallback.className = "tile-placeholder";
    const placeholderIcon = document.createElement("span");
    placeholderIcon.className = "placeholder-icon"; placeholderIcon.textContent = "▦";
    const fallbackText = document.createElement("span");
    fallbackText.textContent = "选择 Episode 后显示";
    fallback.append(placeholderIcon, fallbackText);
    visual.append(fallback);
    const foot = document.createElement("div"); foot.className = "tile-foot";
    const source = document.createElement("span"); source.className = "tile-source";
    const status = document.createElement("span"); status.className = "tile-state";
    const meta = sourceMetadata(block.source);
    source.textContent = meta[2];
    status.textContent = "—";
    foot.append(source, status);
    const tile = {id: block.id, source: block.source, status, fallback,
                  fallbackText, canvas: null, video: null, generation: 0,
                  disposed: false, displayedPath: null};
    if (state.manifest && VIDEO.has(block.source)) {
      const video = document.createElement("video");
      video.muted = true; video.playsInline = true;
      video.preload = "metadata";
      video.setAttribute("aria-label", meta[1]);
      const mediaToken = state.token;
      void resolveCameraUrl(block.source).then(url => {
        if (tile.disposed || mediaToken !== state.token) return;
        if (!url) {
          fallback.hidden = false;
          fallbackText.textContent = "未找到该相机的原始视频";
          status.textContent = "VIDEO NOT FOUND";
          return;
        }
        video.src = url;
        video.load();
      }).catch(() => {
        if (tile.disposed) return;
        fallback.hidden = false;
        fallbackText.textContent = "原始相机视频不可访问";
      });
      video.addEventListener("loadedmetadata", () => {
        if (state.manifest) {
          try { video.currentTime = state.time; } catch (_) {}
        }
        fallback.hidden = true;
        if (state.playing) video.play().catch(() => {});
      });
      video.addEventListener("error", () => {
        video.hidden = true; fallback.hidden = false;
        fallbackText.textContent = "无法读取原始相机视频";
      });
      visual.prepend(video);
      tile.video = video;
      status.textContent = "20 Hz";
    } else {
      const canvas = document.createElement("canvas");
      canvas.hidden = true;
      canvas.setAttribute("aria-label", meta[1]);
      canvas.setAttribute("role", "img");
      visual.prepend(canvas);
      tile.canvas = canvas;
    }
    state.media.push(tile);
    card.append(toolbar, visual, foot);
    card.addEventListener("dragover", event => {
      if (!state.drag || state.drag === block.id) return;
      event.preventDefault(); event.stopPropagation();
      const rect = card.getBoundingClientRect();
      const left = event.clientX < rect.left + rect.width / 2;
      card.classList.toggle("drop-left", left);
      card.classList.toggle("drop-right", !left);
    });
    card.addEventListener("dragleave", () =>
      card.classList.remove("drop-left", "drop-right"));
    card.addEventListener("drop", event => {
      if (!state.drag) return;
      event.preventDefault(); event.stopPropagation();
      const rect = card.getBoundingClientRect();
      const insertion = index + (event.clientX < rect.left + rect.width / 2 ? 0 : 1);
      moveTile(state.drag, row.id, insertion);
    });
    return card;
  }

  function clearDrag() {
    state.drag = null;
    document.querySelectorAll(".tile").forEach(tile =>
      tile.classList.remove("dragging", "drop-left", "drop-right"));
    document.querySelectorAll(".display-row").forEach(row =>
      row.classList.remove("drop-into"));
  }

  function moveTile(sourceId, targetRowId, insertion) {
    const sourceRow = state.rows.find(r => r.blocks.some(b => b.id === sourceId));
    const targetRow = state.rows.find(r => r.id === targetRowId);
    if (!sourceRow || !targetRow) return;
    const old = sourceRow.blocks.findIndex(b => b.id === sourceId);
    const tile = sourceRow.blocks[old];
    if (sourceRow === targetRow) {
      sourceRow.blocks.splice(old, 1);
      sourceRow.blocks.splice(clamp(insertion > old ? insertion - 1 : insertion,
        0, sourceRow.blocks.length), 0, tile);
    } else if (targetRow.blocks.length >= 5) {
      // Swapping preserves the 1–5 tile constraint of a full destination row.
      const target = clamp(insertion, 0, targetRow.blocks.length - 1);
      sourceRow.blocks[old] = targetRow.blocks[target];
      targetRow.blocks[target] = tile;
      toast("目标行已满：已交换两个展示块");
    } else {
      sourceRow.blocks.splice(old, 1);
      targetRow.blocks.splice(clamp(insertion, 0, targetRow.blocks.length), 0, tile);
    }
    clearDrag(); saveLayout(); renderLayout();
  }

  function renderLayout() {
    // Invalidate detached tiles so late image loads cannot replace a new layout.
    for (const tile of state.media) {
      tile.disposed = true;
      tile.generation++;
      if (tile.video) tile.video.pause();
    }
    state.media = [];
    state.lastSpatial = -1;
    const container = $("display-rows");
    container.replaceChildren();
    state.rows.forEach(row => {
      const shell = document.createElement("section"); shell.className = "row-shell";
      const head = document.createElement("div"); head.className = "row-heading";
      const actions = document.createElement("div"); actions.className = "row-actions";
      const add = document.createElement("button");
      add.type = "button"; add.textContent = "＋ 添加展示块";
      add.disabled = row.blocks.length >= 5;
      add.addEventListener("click", () => {
        if (row.blocks.length >= 5) { toast("每行最多 5 个展示块"); return; }
        const used = new Set(row.blocks.map(b => b.source));
        const next = SOURCES.find(x => !used.has(x[0]))?.[0] || "floor_top";
        row.blocks.push({id: uuid(), source: next});
        saveLayout(); renderLayout();
      });
      const remove = document.createElement("button");
      remove.type = "button"; remove.className = "remove-row";
      remove.textContent = "×"; remove.title = "移除这一行";
      remove.addEventListener("click", () => {
        if (state.rows.length === 1) { toast("至少保留一行"); return; }
        state.rows.splice(rowIndex, 1); saveLayout(); renderLayout();
      });
      actions.append(add, remove); head.append(actions);
      const grid = document.createElement("div");
      grid.className = "display-row";
      grid.dataset.count = String(row.blocks.length);
      grid.style.setProperty("--count", row.blocks.length);
      grid.addEventListener("dragover", event => {
        if (!state.drag || event.target.closest(".tile")) return;
        event.preventDefault();
        grid.classList.add("drop-into");
      });
      grid.addEventListener("dragleave", event => {
        if (!grid.contains(event.relatedTarget)) grid.classList.remove("drop-into");
      });
      grid.addEventListener("drop", event => {
        if (!state.drag || event.target.closest(".tile")) return;
        event.preventDefault(); event.stopPropagation();
        moveTile(state.drag, row.id, row.blocks.length);
      });
      if (!row.blocks.length) {
        const empty = document.createElement("div"); empty.className = "row-empty";
        const main = document.createElement("strong");
        main.textContent = "这一行还没有展示块";
        const help = document.createElement("span");
        help.textContent = "点击添加，或从其他行拖进来";
        empty.append(main, help); grid.append(empty);
      }
      row.blocks.forEach((block, index) => grid.append(newTile(block, row, index)));
      shell.append(head, grid); container.append(shell);
    });
    updateTimeline();
    if (state.playing) for (const v of videos()) v.play().catch(() => {});
  }

  function setDirectoryProgress(message, kind = "") {
    const element = $("directory-scan-status");
    element.className = "directory-scan-status " + kind;
    element.textContent = message;
  }

  function installTaskCatalog(tasks, mode, locationText, preferred) {
    if (!tasks.length) throw Error("所选目录中没有符合 G2 格式的 Episode");
    pause();
    clearVideoObjectUrls();
    state.preload.clear();
    state.mode = mode;
    state.catalog = {...state.baseCatalog, tasks};
    state.task = null;
    state.episode = null;
    state.manifest = null;
    state.available = [];
    state.time = 0;
    state.duration = 0;
    const picker = $("task-select");
    fillSelect(picker, tasks.map(task => [
      task.id || task.name,
      (task.label || task.name) + " · " + task.episodes.length + " EP",
    ]), preferred);
    picker.disabled = false;
    $("source-location").textContent = locationText;
    setDirectoryProgress(
      "已发现 " + tasks.length + " 个任务目录、" +
      tasks.reduce((n, task) => n + task.episodes.length, 0) +
      " 个 Episode。所有内容只读，不上传原始数据。",
      "ready");
    void chooseTask(picker.value);
  }

  async function activateLocalSource(provider, label) {
    $("pick-local-folder").disabled = true;
    setDirectoryProgress("正在扫描 " + label + "，只检查完整 Episode，不展开逐帧图片…");
    showStatus("扫描本地目录");
    try {
      const tasks = await provider.scan(message => setDirectoryProgress(message));
      if (!tasks.length) throw Error("未找到 COMPLETE.json + episode_manifest.json 均有效的 Episode");
      if (state.localSource && state.localSource !== provider)
        state.localSource.release();
      state.localSource = provider;
      installTaskCatalog(tasks, "local", "本机 · " + label);
    } catch (error) {
      provider.release();
      setDirectoryProgress(error.message, "issue");
      showStatus("目录扫描失败", "issue");
      toast(error.message);
    } finally {
      $("pick-local-folder").disabled = false;
    }
  }

  async function chooseLocalDirectory() {
    if (!state.baseCatalog) {
      toast("正在加载任务元数据，请稍后选择文件夹"); return;
    }
    // Must run from a real user click; the native picker is owned by the browser.
    if (typeof window.showDirectoryPicker === "function") {
      try {
        const handle = await window.showDirectoryPicker({
          id: "g2-spatial-replay-dataset", mode: "read",
        });
        const provider = G2DirectorySource.createHandleProvider(
          handle, state.baseCatalog);
        await activateLocalSource(provider, handle.name);
        return;
      } catch (error) {
        if (error.name === "AbortError") return;
        // Some mobile/embedded browsers expose the API without allowing it.
        if (!["SecurityError", "NotAllowedError", "TypeError"].includes(error.name)) {
          setDirectoryProgress(error.message, "issue");
          toast(error.message);
          return;
        }
      }
    }
    setDirectoryProgress(
      "当前浏览器使用兼容文件夹选择方式；大数据集建议桌面 Chrome/Edge 浏览器。");
    $("local-folder-fallback").click();
  }

  async function chooseLocalVideos() {
    if (typeof window.showDirectoryPicker !== "function") {
      toast("此浏览器不支持独立选择视频文件夹；可以继续使用服务器原始视频链接");
      return;
    }
    try {
      const handle = await window.showDirectoryPicker({
        id: "g2-spatial-replay-original-video", mode: "read",
      });
      state.localVideoRoot = handle;
      clearVideoObjectUrls();
      if (state.manifest && state.episode)
        await loadEpisode(state.episode.global_id);
      setDirectoryProgress("原始视频目录已选择：" + handle.name +
        "。如未找到 MP4，仍可使用服务器视频。", "ready");
    } catch (error) {
      if (error.name !== "AbortError") toast(error.message);
    }
  }

  async function remoteDirectoryEntries(url) {
    const response = await fetch(url, {cache: "no-store"});
    if (!response.ok) throw Error("HTTP " + response.status + ": " + url);
    const doc = new DOMParser().parseFromString(await response.text(), "text/html");
    const root = new URL(url, location.href);
    return [...doc.querySelectorAll("a[href]")].flatMap(anchor => {
      const href = anchor.getAttribute("href");
      if (!href || !href.endsWith("/") || href === "../" ||
          href.startsWith("/") || href.includes("?") || href.includes("#"))
        return [];
      const parts = href.split("/");
      if (parts.filter(Boolean).length !== 1) return [];
      let name;
      try { name = decodeURIComponent(parts[0]); }
      catch (_) { return []; }
      if (!/^[A-Za-z0-9_.-]+$/.test(name) || name === ".." || name === ".")
        return [];
      const child = new URL(href, root);
      if (child.origin !== root.origin || !child.href.startsWith(root.href)) return [];
      return [{name, url: child.href}];
    });
  }

  async function listServerDirectoryChoices() {
    const select = $("server-directory-select");
    const status = $("server-browse-status");
    const token = ++state.serverBrowseToken;
    select.disabled = true;
    fillSelect(select, [["", "读取当前目录中的文件夹…"]], "");
    status.textContent = "正在读取服务器目录…";
    try {
      const root = canonicalServerRoot($("remote-path").value.trim());
      const children = await remoteDirectoryEntries(root);
      if (token !== state.serverBrowseToken) return;
      state.serverBrowseEntries = children;
      const options = [
        ["", children.length ? "选择下级目录…" : "当前目录没有下级文件夹"],
        ...children.map(child => [child.url, "📁 " + child.name]),
      ];
      fillSelect(select, options, "");
      select.disabled = children.length === 0;
      status.textContent = children.length + " 个子目录 · 可逐级选择";
    } catch (error) {
      if (token !== state.serverBrowseToken) return;
      state.serverBrowseEntries = [];
      fillSelect(select, [["", "目录无法浏览，可手动输入路径"]], "");
      select.disabled = true;
      status.textContent = "未列出子目录 · " + error.message;
    }
  }

  function navigateServerParent() {
    try {
      const current = canonicalServerRoot($("remote-path").value.trim());
      const parent = new URL("../", current);
      if (parent.origin !== location.origin || parent.href === current) return;
      $("remote-path").value = parent.pathname;
      void listServerDirectoryChoices();
    } catch (error) {
      toast(error.message);
    }
  }

  function canonicalServerRoot(raw) {
    if (!raw) throw Error("请输入 HTTP 数据目录");
    // Convenience for the existing 18765 server's /mnt/data1 soft link.
    const path = raw.startsWith("/mnt/data1/") ?
      "/data1/" + raw.slice("/mnt/data1/".length) : raw;
    const url = new URL(path, location.href);
    if (!["http:", "https:"].includes(url.protocol) ||
        url.origin !== location.origin)
      throw Error("HTTP 数据目录必须与当前网页同源，请使用该服务器暴露的 URL 路径");
    if (!url.pathname.endsWith("/")) url.pathname += "/";
    if (url.search || url.hash) throw Error("HTTP 数据目录不能包含查询参数");
    return url.href;
  }

  async function discoverHttpFolders(initialUrl) {
    let scanned = 0;
    const roots = [];
    const queue = [{url: initialUrl, depth: 0}];
    const skip = new Set(["view", "source_videos", "videos", ".git",
      "node_modules", "episodes", "__pycache__", "lost+found"]);
    while (queue.length) {
      const {url, depth} = queue.shift();
      if (++scanned > 180)
        throw Error("目录层级过大，请指定更靠近 G2 输出的 HTTP 父目录");
      const entries = await remoteDirectoryEntries(url);
      if (entries.some(child => child.name === "tasks")) {
        roots.push(url);
        continue;
      }
      if (depth >= 7) continue;
      for (const child of entries) {
        if (!skip.has(child.name) && !child.name.startsWith(".") &&
            !child.name.startsWith("state_") &&
            !/^episode_\d+$/.test(child.name))
          queue.push({url: child.url, depth: depth + 1});
      }
    }
    return roots;
  }

  async function scanRemoteRoot() {
    if (!state.baseCatalog) {
      toast("任务索引尚未加载完成"); return;
    }
    $("scan-remote").disabled = true;
    let preferred = null;
    try {
      const url = canonicalServerRoot($("remote-path").value.trim());
      setDirectoryProgress("正在递归发现 HTTP 数据目录：" + url);
      showStatus("扫描服务器目录");
      const roots = await discoverHttpFolders(url);
      if (!roots.length) throw Error("未找到包含 tasks/ 的有效 G2 输出目录");
      const tasks = [];
      for (const root of roots) {
        const taskDirs = await remoteDirectoryEntries(root + "tasks/");
        for (const dir of taskDirs) {
          const name = dir.name;
          if (!/^[A-Za-z][A-Za-z0-9_]*$/.test(name)) continue;
          let episodeDirs;
          try { episodeDirs = await remoteDirectoryEntries(
            root + "tasks/" + encodeURIComponent(name) + "/episodes/");
          } catch (_) { continue; }
          const meta = state.baseCatalog.tasks.find(item => item.name === name);
          const byId = new Map((meta?.episodes || []).map(ep => [ep.global_id, ep]));
          const episodes = [];
          for (const entry of episodeDirs) {
            if (!/^episode_\d{6,}$/.test(entry.name)) continue;
            const gid = Number(entry.name.slice(8));
            const original = byId.get(gid);
            episodes.push(original || {
              global_id: gid, local_id: gid, frames: 0, instruction: "",
            });
          }
          if (!episodes.length) continue;
          episodes.sort((a,b) => a.global_id - b.global_id);
          tasks.push({
            id: root + "::" + name, name,
            label: name, rootUrl: root, episodes,
            count: episodes.length,
            source_dir: meta?.source_dir || "",
            chunks_size: meta?.chunks_size || 1000,
            video_path: meta?.video_path || "",
          });
        }
      }
      const counts = new Map();
      for (const task of tasks)
        counts.set(task.name, (counts.get(task.name) || 0) + 1);
      for (const task of tasks) {
        if (counts.get(task.name) > 1)
          task.label = task.name + " · " + task.rootUrl;
      }
      state.sourceRootUrl = url;
      if (state.localSource) state.localSource.release();
      state.localSource = null;
      installTaskCatalog(tasks, "server", "服务器 · " + url, preferred);
    } catch (error) {
      showStatus("服务器扫描失败", "issue");
      setDirectoryProgress(error.message, "issue");
      toast(error.message);
    } finally {
      $("scan-remote").disabled = false;
    }
  }

  async function restoreDefaultServer() {
    if (!state.baseCatalog) throw Error("任务索引尚未加载完成");
    if (state.localSource) state.localSource.release();
    state.localSource = null;
    state.sourceRootUrl = "../";
    state.localVideoRoot = null;
    clearVideoObjectUrls();
    $("remote-path").value = "../";
    void listServerDirectoryChoices();
    const tasks = state.baseCatalog.tasks;
    const available = new Set(await listDirectory("../tasks/"));
    const preferred = tasks.find(task => available.has(task.name))?.name ||
      tasks[0]?.name;
    installTaskCatalog(tasks, "server", "服务器 · 默认 G2 数据目录", preferred);
  }

  $("pick-local-folder").addEventListener("click", chooseLocalDirectory);
  $("pick-local-videos").addEventListener("click", chooseLocalVideos);
  $("local-folder-fallback").addEventListener("change", event => {
    const files = [...event.target.files];
    event.target.value = "";
    if (!files.length) return;
    const provider = G2DirectorySource.createFileListProvider(
      files, state.baseCatalog);
    void activateLocalSource(provider, files[0].webkitRelativePath.split("/")[0]);
  });
  $("restore-server").addEventListener("click", () =>
    void restoreDefaultServer().catch(error => toast(error.message)));
  $("scan-remote").addEventListener("click", scanRemoteRoot);
  $("server-refresh").addEventListener("click", () =>
    void listServerDirectoryChoices());
  $("server-parent").addEventListener("click", navigateServerParent);
  $("server-directory-select").addEventListener("change", event => {
    const selected = state.serverBrowseEntries.find(
      entry => entry.url === event.target.value);
    if (!selected) return;
    $("remote-path").value = new URL(selected.url).pathname;
    void listServerDirectoryChoices();
  });
  $("remote-path").addEventListener("change", () =>
    void listServerDirectoryChoices());
  $("remote-path").addEventListener("keydown", event => {
    if (event.key === "Enter") {
      event.preventDefault();
      void scanRemoteRoot();
    }
  });
  async function initialize() {
    showStatus("连接数据");
    try {
      state.catalog = await fetchJson("./catalog.json");
      state.baseCatalog = state.catalog;
      if (state.catalog.schema !== "g2_replay_viewer_catalog_v1" ||
          state.catalog.source_fps !== 20 || !state.catalog.tasks?.length)
        throw Error("任务索引格式不兼容");
      const existing = new Set(await listDirectory("../tasks/"));
      const select = $("task-select");
      fillSelect(select, state.catalog.tasks.map(t => [
        t.name, t.name + "  ·  " + t.count + " EP"
      ]));
      select.disabled = false;
      let previous;
      try { previous = localStorage.getItem("psm-g2-viewer-task"); } catch (_) {}
      const first = state.catalog.tasks.find(t => existing.has(t.name));
      const selected = previous && existing.has(previous) ?
        previous : first?.name || state.catalog.tasks[0].name;
      select.value = selected;
      await chooseTask(selected);
      void listServerDirectoryChoices();
    } catch (error) {
      showStatus("初始化失败", "issue");
      $("instruction-text").textContent = error.message;
      toast(error.message);
    }
  }

  $("task-select").addEventListener("change", () => chooseTask($("task-select").value));
  $("episode-select").addEventListener("change", () => loadEpisode(Number($("episode-select").value)));
  $("refresh-episodes").addEventListener("click", () => {
    if (state.mode === "local" && state.localSource) {
      void activateLocalSource(state.localSource,
        state.localSource.root?.name || "本地 G2 数据");
    } else if (state.sourceRootUrl !== "../") {
      void scanRemoteRoot();
    } else {
      void refreshEpisodes(true);
    }
  });
  $("play").addEventListener("click", play);
  $("prev-frame").addEventListener("click", () => step(-1));
  $("next-frame").addEventListener("click", () => step(1));
  $("scrub").addEventListener("input", () => {
    if (state.manifest) seek(state.duration * Number($("scrub").value) / 1000, true);
  });
  $("speed").addEventListener("change", () => {
    state.speed = Number($("speed").value);
    state.fallbackTime = state.time;
    state.fallbackStart = performance.now();
    syncVideos();
  });
  $("add-row").addEventListener("click", () => {
    if (state.rows.length >= 30) { toast("最多允许 30 行"); return; }
    state.rows.push({id: uuid(), blocks: []});
    saveLayout(); renderLayout();
  });
  $("reset-layout").addEventListener("click", () => {
    state.rows = startingLayout(); saveLayout(); renderLayout();
    toast("已恢复默认双行布局");
  });
  $("clock-video").addEventListener("error", () => { state.clockFailed = true; });
  $("clock-video").addEventListener("ended", () => {
    if (state.manifest) seek(state.duration, true);
    pause();
  });
  window.addEventListener("keydown", event => {
    const target = event.target;
    if (target instanceof HTMLElement &&
        (["INPUT", "SELECT", "TEXTAREA", "BUTTON"].includes(target.tagName) ||
         target.isContentEditable)) return;
    if (event.key === "ArrowLeft") { event.preventDefault(); step(-1); }
    if (event.key === "ArrowRight") { event.preventDefault(); step(1); }
    if (event.code === "Space") { event.preventDefault(); play(); }
  });

  renderLayout();
  initialize();
})();