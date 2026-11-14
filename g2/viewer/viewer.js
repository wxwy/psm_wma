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

  // A view exists only if a state owns its PNG or directly references a
  // prior state that owns it. This covers compact v1, v2 and v3 manifests.
  function ownerState(manifest, index, relative) {
    const states = manifest?.states;
    if (!Array.isArray(states) || index < 0 || index >= states.length)
      return null;
    const current = states[index];
    if (!Array.isArray(current.view_pngs)) return null;
    if (current.view_pngs.includes(relative)) return index;
    const refs = current.view_refs;
    if (!refs || Array.isArray(refs) || typeof refs !== "object") return null;
    const ref = refs[relative];
    if (!ref || typeof ref !== "object" || ref.path !== relative ||
        !Number.isInteger(ref.ref_state) ||
        ref.ref_state < 0 || ref.ref_state >= index) return null;
    const owner = states[ref.ref_state];
    if (!owner || !Array.isArray(owner.view_pngs) ||
        !owner.view_pngs.includes(relative)) return null;
    return ref.ref_state;
  }

  function availableSources(manifest, cameras = new Set()) {
    if (!manifest || !Array.isArray(manifest.states)) return [];
    const valid = relative => manifest.states.some((entry, i) =>
      ownerState(manifest, i, relative) !== null);
    const room = SOURCES.filter(([source]) =>
      !VIDEO.has(source) && valid("sixview/" + source + ".png"));
    const videos = SOURCES.filter(([source]) =>
      VIDEO.has(source) && cameras.has(source));
    const islands = islandGroups(manifest);
    return [
      {name: "全局 SixView", sources: room},
      {name: "机器人相机", sources: videos},
      ...islands.map(island => ({
        name: island.label,
        sources: island.choices.map(c => [c.value, "Island · " + c.label]),
      })),
    ].filter(group => group.sources.length);
  }

  function islandGroups(manifest) {
    if (!manifest || !Array.isArray(manifest.states)) return [];
    const byId = new Map();
    for (const [index, entry] of manifest.states.entries()) {
      for (const id of entry.islands || []) {
        if (typeof id !== "string" || !ISLAND_ID_RE.test(id)) continue;
        for (const direction of ISLAND_DIRECTIONS) {
          const relative = "islands/" + id + "/" + direction + ".png";
          if (ownerState(manifest, index, relative) === null) continue;
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
    const groups = availableSources(state.manifest, state.availableCameras);
    const options = [];
    for (const group of groups) {
      const optgroup = document.createElement("optgroup");
      optgroup.label = group.name;
      for (const [value, label] of group.sources) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = label;
        optgroup.append(option);
        options.push(value);
      }
      select.append(optgroup);
    }
    if (!options.length) {
      const placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = "当前没有可用的视角";
      select.append(placeholder);
      select.disabled = true;
      return null;
    }
    const chosen = options.includes(selected) ? selected : options[0];
    select.value = chosen;
    select.disabled = false;
    return chosen;
  }
  const CAMERA = {
    left: "observation.images.robot0_agentview_left",
    right: "observation.images.robot0_agentview_right",
    wrist: "observation.images.robot0_eye_in_hand",
  };
  const STORAGE = "psm-g2-viewer-layout-v2";
  const LEGACY_STORAGE = "psm-g2-viewer-layout-v1";
  const uuid = () => typeof crypto !== "undefined" && crypto.randomUUID ?
    crypto.randomUUID() : Date.now() + "-" + Math.random().toString(36).slice(2);
  const pad = (n, w = 6) => String(n).padStart(w, "0");
  const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi, n));
  const fmt = n => {
    const s = Number.isFinite(n) ? n : 0;
    return pad(Math.floor(s / 60), 2) + ":" + pad(Math.floor(s % 60), 2) +
      "." + pad(Math.floor((s % 1) * 100), 2);
  };

  const FALLBACK_PRIORITY = [
    "floor_top", "plus_Y", "plus_X", "minus_Y", "minus_X", "upper_up",
    "left", "right", "wrist",
  ];

  function startingLayout(manifest = null, cameras = new Set()) {
    // Provisional sources only establish the three-row structure. As soon
    // as an Episode is loaded, the auto layout chooses real available views.
    let rows;
    if (!manifest) {
      rows = [
        ["left", "right", "wrist"],
        ["floor_top", "plus_Y", "plus_X"],
        ["minus_Y", "minus_X", "upper_up", "floor_top"],
      ];
    } else {
      const available = [...new Set(availableSources(manifest, cameras)
        .flatMap(group => group.sources.map(([source]) => source)))];
      const availableSet = new Set(available);
      const fallback = [
        ...FALLBACK_PRIORITY.filter(source => availableSet.has(source)),
        ...available.filter(source => !FALLBACK_PRIORITY.includes(source)),
      ];
      const used = new Set();
      // Do not consume Island candidates in rows 1/2 if any room/camera
      // sources exist. Preserve the selected Island's four directions for
      // the third row, even when the upper rows must reuse another view.
      const nonIsland = fallback.filter(source => !parseIslandSource(source));
      const upperFallback = nonIsland.length ? nonIsland : fallback;
      const choose = (preferred, count, backup) => {
        const picked = [];
        for (const pool of [preferred, backup]) {
          for (const source of pool) {
            if (picked.length === count) break;
            if (availableSet.has(source) && !used.has(source) &&
                !picked.includes(source)) {
              picked.push(source);
              used.add(source);
            }
          }
        }
        // After all unused sources have been consumed, reuse only actual
        // available views; never invent missing geometry/camera files.
        for (const source of backup) {
          if (picked.length === count) break;
          if (!picked.includes(source)) picked.push(source);
        }
        for (let i = 0; backup.length && picked.length < count; i++)
          picked.push(backup[i % backup.length]);
        return picked;
      };
      const firstIsland = islandGroups(manifest)[0];
      const preferredIsland = firstIsland ?
        firstIsland.choices.map(choice => choice.value) : [];
      rows = [
        choose(["left", "right", "wrist"], 3, upperFallback),
        choose(["floor_top", "plus_Y", "plus_X"], 3, upperFallback),
        choose(preferredIsland, 4, fallback),
      ];
    }
    return rows.map(sources => ({
      id: uuid(),
      blocks: sources.map(source => ({id: uuid(), source})),
    }));
  }

  function validSavedLayout(rows) {
    if (!Array.isArray(rows) || !rows.length || rows.length > 30 ||
        !rows.every(row => typeof row.id === "string" &&
          Array.isArray(row.blocks) && row.blocks.length <= 5 &&
          row.blocks.every(block => typeof block.id === "string" &&
            validSource(block.source)))) return false;
    const ids = rows.flatMap(row => [row.id, ...row.blocks.map(b => b.id)]);
    return new Set(ids).size === ids.length;
  }

  function isLegacyDefault(rows) {
    return rows.length === 2 &&
      JSON.stringify(rows.map(row => row.blocks.map(block => block.source))) ===
      JSON.stringify([
        ["floor_top", "left", "wrist"],
        ["plus_X", "minus_X", "plus_Y"],
      ]);
  }

  function readLayout() {
    try {
      const modern = localStorage.getItem(STORAGE);
      if (modern === "auto") return {rows: startingLayout(), auto: true};
      if (modern != null) {
        const saved = JSON.parse(modern);
        if (validSavedLayout(saved))
          return {rows: saved, auto: false};
      }
      const legacy = localStorage.getItem(LEGACY_STORAGE);
      if (legacy != null) {
        const saved = JSON.parse(legacy);
        if (validSavedLayout(saved)) {
          if (isLegacyDefault(saved))
            return {rows: startingLayout(), auto: true};
          return {rows: saved, auto: false};
        }
      }
    } catch (_) {}
    return {rows: startingLayout(), auto: true};
  }

  const initialLayout = readLayout();
  const state = {
    catalog: null, task: null, episode: null, manifest: null, available: [],
    rows: initialLayout.rows, autoLayout: initialLayout.auto,
    media: [], time: 0, duration: 0, playing: false,
    speed: 1, lastSpatial: -1, frameHandle: null, drag: null,
    token: 0, fallbackTime: 0, fallbackStart: 0, clockFailed: false,
    toastTimer: null, preload: new Map(),
    dataRoot: null, completedByTask: new Map(), taskScanToken: 0,
    availableCameras: new Set(),
  };

  function saveLayout() {
    // Only explicit user layout edits freeze the automatic per-Episode
    // three-row arrangement. Customized rows survive Episode changes.
    state.autoLayout = false;
    try { localStorage.setItem(STORAGE, JSON.stringify(state.rows)); }
    catch (_) {}
  }

  function resetDefaultLayout() {
    state.autoLayout = true;
    state.rows = startingLayout(state.manifest, state.availableCameras);
    try { localStorage.setItem(STORAGE, "auto"); } catch (_) {}
    renderLayout();
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
    return state.dataRoot + "tasks/" +
      encodeURIComponent(state.task.name) + "/episodes/";
  }

  // A Viewer opened at /view/ may be served through an HTTP symlink; in
  // that case ../tasks/ incorrectly means /tasks/ rather than the dataset.
  // Probe the direct deployment and the fixed /data1 mount once, not per frame.
  async function resolveDataRoot() {
    const fixed = "/data1/data_v2_0617/robocasa365_v3_flat/" +
      "robocasa365-target-atomic-6views/";
    const candidates = [
      new URL("../", location.href).href,
      new URL(fixed, location.origin).href,
    ];
    for (const root of [...new Set(candidates)]) {
      try {
        const response = await fetch(root + "tasks/", {cache: "no-store"});
        if (!response.ok) continue;
        const doc = new DOMParser().parseFromString(
          await response.text(), "text/html");
        const names = new Set([...doc.querySelectorAll("a[href]")]
          .map(a => {
            const name = a.getAttribute("href") || "";
            try { const clean = decodeURIComponent(name); return clean.endsWith("/") ? clean.slice(0, -1) : clean; }
            catch (_) { return ""; }
          }));
        if (state.catalog.tasks.some(task => names.has(task.name)))
          return root;
        // Empty production data may not contain any tasks yet.
        if (!names.size) return root;
      } catch (_) { /* Try the next fixed location. */ }
    }
    throw Error("无法定位 G2 正式输出目录，请确认 18765 已映射 /data1");
  }

  async function discoverCompletedTasks(preserve = true) {
    const token = ++state.taskScanToken;
    const previousTask = preserve ? state.task?.name : null;
    const previousEpisode = preserve ? state.episode?.global_id : null;
    const taskPicker = $("task-select");
    taskPicker.disabled = true;
    showStatus("更新已完成任务", "");
    try {
      const taskNames = new Set(await listDirectory(state.dataRoot + "tasks/"));
      const candidates = state.catalog.tasks.filter(t => taskNames.has(t.name));
      const records = await Promise.all(candidates.map(async task => {
        const url = state.dataRoot + "tasks/" +
          encodeURIComponent(task.name) + "/episodes/";
        const entries = await listDirectory(url);
        const ids = new Set(entries.filter(name => /^episode_\d{6}$/.test(name))
          .map(name => Number(name.slice("episode_".length))));
        // The compact publisher exposes a final episode directory only after
        // success. A selected Episode still validates COMPLETE and manifest.
        return {task, episodes: task.episodes.filter(ep => ids.has(ep.global_id))};
      }));
      if (token !== state.taskScanToken) return;
      const available = records.filter(record => record.episodes.length > 0);
      state.completedByTask = new Map(
        available.map(record => [record.task.name, record.episodes]));
      fillSelect(taskPicker, available.map(record => [
        record.task.name, record.task.name +
          " · " + record.episodes.length + " EP",
      ]), previousTask);
      if (!available.length) {
        taskPicker.disabled = true;
        fillSelect(taskPicker, [["", "暂无已完成的任务"]], "");
        $("episode-select").disabled = true;
        fillSelect($("episode-select"), [["", "等待生成结果"]], "");
        $("available-count").textContent = "0 个已完成";
        $("instruction-text").textContent = "输出目录还没有已完成 Episode。点击刷新 Episode 重试。";
        state.task = null;
        state.episode = null;
        state.manifest = null;
        state.availableCameras.clear();
        transportEnabled(false);
        renderLayout();
        showStatus("等待生成结果", "");
        return;
      }
      const target = available.some(item => item.task.name === previousTask) ?
        previousTask : available[0].task.name;
      taskPicker.value = target;
      taskPicker.disabled = false;
      await chooseTask(target, previousEpisode);
    } catch (error) {
      if (token !== state.taskScanToken) return;
      showStatus("获取已完成任务失败", "issue");
      toast(error.message);
      taskPicker.disabled = false;
    }
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

  async function detectAvailableCameras() {
    const names = ["left", "right", "wrist"];
    const results = await Promise.all(names.map(async source => {
      const url = videoUrl(source);
      if (!url) return null;
      try {
        const response = await fetch(url, {method: "HEAD", cache: "no-store"});
        return response.ok ? source : null;
      } catch (_) {
        return null;
      }
    }));
    return new Set(results.filter(Boolean));
  }

  function viewPath(source, index) {
    const entry = state.manifest.states[index];
    const island = parseIslandSource(source);
    if (!island && (!ALL.has(source) || VIDEO.has(source))) return null;
    const relative = island
      ? "islands/" + island.island + "/" + island.direction + ".png"
      : "sixview/" + source + ".png";
    const owner = ownerState(state.manifest, index, relative);
    if (owner === null) return null;
    const ownerFrame = state.manifest.states[owner];
    return episodeDirectory() + "state_" + pad(owner) +
      "_frame_" + pad(ownerFrame.frame) + "/" + relative;
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
    const promise = new Promise((resolve, reject) => {
      const image = new Image();
      image.decoding = "async";
      image.onload = () => {
        const decoding = typeof image.decode === "function" ?
          image.decode() : Promise.resolve();
        decoding.then(() => resolve(image), reject);
      };
      image.onerror = () => reject(new Error("PNG 图片加载失败"));
      image.src = path;
    });
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
    state.episode = item;
    state.manifest = null;
    state.availableCameras.clear();
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
      const base = episodeDirectory();
      const [complete, manifest] = await Promise.all([
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
      // Keep source timestamps aligned with the exact saved spatial frames.
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
      const cameras = await detectAvailableCameras();
      if (token !== state.token) return;
      state.manifest = manifest;
      state.availableCameras = cameras;
      if (state.autoLayout)
        state.rows = startingLayout(manifest, cameras);
      state.clockFailed = !cameras.has("left");
      if (cameras.has("left")) {
        $("clock-video").src = videoUrl("left");
      } else {
        $("clock-video").removeAttribute("src");
      }
      $("clock-video").load();
      transportEnabled(true);
      renderLayout();
      seek(0, true);
      showStatus("已连接 · " + manifest.states.length + " 空间帧", "ready");
    } catch (error) {
      if (token !== state.token) return;
      state.manifest = null;
      state.availableCameras.clear();
      renderLayout();
      transportEnabled(false);
      showStatus("数据不可用", "issue");
      toast(error.message);
    }
  }

  async function refreshEpisodes(preferredEpisode = null) {
    const task = state.task;
    if (!task) return;
    const completed = state.completedByTask.get(task.name) || [];
    const picker = $("episode-select");
    $("available-count").textContent = completed.length + " 个已完成";
    if (!completed.length) {
      picker.disabled = true;
      fillSelect(picker, [["", "暂无完成的 Episode"]], "");
      state.episode = null;
      state.manifest = null;
      state.availableCameras.clear();
      transportEnabled(false);
      renderLayout();
      return;
    }
    const current = preferredEpisode != null &&
      completed.some(ep => ep.global_id === preferredEpisode) ?
      preferredEpisode : completed[0].global_id;
    fillSelect(picker, completed.map(ep => [
      ep.global_id, "EP " + pad(ep.local_id, 3) +
      " · 全局 " + pad(ep.global_id) + " · " + fmt(ep.frames / 20),
    ]), current);
    picker.disabled = false;
    await loadEpisode(Number(picker.value));
  }

  async function chooseTask(taskName, preferredEpisode = null) {
    const task = state.catalog?.tasks.find(t => t.name === taskName);
    if (!task || !state.completedByTask.has(taskName)) return;
    pause();
    state.task = task;
    state.episode = null;
    state.manifest = null;
    state.time = 0;
    state.duration = 0;
    try { localStorage.setItem("psm-g2-viewer-task", taskName); } catch (_) {}
    $("instruction-text").textContent = "正在加载已完成 Episode…";
    $("task-tag").textContent = task.name;
    $("global-tag").textContent = "—";
    await refreshEpisodes(preferredEpisode);
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
    const selected = fillSourceSelect(select, block.source);
    if (selected && selected !== block.source) {
      block.source = selected;
      saveLayout();
    }
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
      video.src = videoUrl(block.source);
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
        const options = availableSources(state.manifest, state.availableCameras)
          .flatMap(group => group.sources.map(source => source[0]));
        const next = options.find(source => !used.has(source)) ||
          options[0] || "floor_top";
        row.blocks.push({id: uuid(), source: next});
        saveLayout(); renderLayout();
      });
      const remove = document.createElement("button");
      remove.type = "button"; remove.className = "remove-row";
      remove.textContent = "×"; remove.title = "移除这一行";
      remove.addEventListener("click", () => {
        if (state.rows.length === 1) { toast("至少保留一行"); return; }
        const rowIndex = state.rows.indexOf(row);
        if (rowIndex < 0) return;
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

  async function initialize() {
    showStatus("连接数据");
    try {
      state.catalog = await fetchJson("./catalog.json");
      if (state.catalog.schema !== "g2_replay_viewer_catalog_v1" ||
          state.catalog.source_fps !== 20 || !state.catalog.tasks?.length)
        throw Error("任务索引格式不兼容");
      state.dataRoot = await resolveDataRoot();
      let preferred;
      try { preferred = localStorage.getItem("psm-g2-viewer-task"); }
      catch (_) {}
      // Remember the previously selected task only if it actually has outputs.
      if (preferred) state.task = state.catalog.tasks.find(t => t.name === preferred) || null;
      await discoverCompletedTasks(true);
    } catch (error) {
      showStatus("初始化失败", "issue");
      $("instruction-text").textContent = error.message;
      toast(error.message);
    }
  }

  $("task-select").addEventListener("change", () => chooseTask($("task-select").value));
  $("episode-select").addEventListener("change", () => loadEpisode(Number($("episode-select").value)));
  $("refresh-episodes").addEventListener("click", () => {
    void discoverCompletedTasks(true);
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
    resetDefaultLayout();
    toast("已恢复默认三行布局");
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