(function (host) {
  "use strict";
  // Read-only native browser folder scans. No files are uploaded or edited.
  const EPISODE = /^episode_(\d{6,})$/;
  const SAFE = /^[A-Za-z0-9_.-]+$/;
  const SKIP = new Set(["view", "source_videos", "videos", ".git", "node_modules",
    "__pycache__", "lost+found", ".g2_runtime_deps_py313"]);
  const MAX_DEPTH = 11;
  const MAX_DIRS = 25000;
  const MAX_EPISODES = 20000;

  function mappingIndex(catalog) {
    const lookup = new Map();
    for (const task of catalog?.tasks || [])
      for (const ep of task.episodes || [])
        lookup.set(task.name + ":" + ep.global_id, {task, ep});
    return lookup;
  }

  function validManifest(receipt, manifest, dirname) {
    if (!receipt || receipt.complete !== true || !manifest ||
        !Array.isArray(manifest.states) || !manifest.states.length ||
        !Number.isSafeInteger(Number(receipt.episode_id))) return false;
    const m = dirname.match(EPISODE);
    if (!m || Number(m[1]) !== Number(receipt.episode_id) ||
        (manifest.episode_id != null &&
          Number(manifest.episode_id) !== Number(receipt.episode_id)) ||
        manifest.states.length !== receipt.state_count ||
        manifest.state_count !== receipt.state_count) return false;
    let last = -1;
    for (const state of manifest.states) {
      if (!Number.isInteger(state.frame) || state.frame <= last ||
          !Array.isArray(state.view_pngs)) return false;
      last = state.frame;
    }
    return true;
  }

  function resolveTask(parts, manifest) {
    const tasksIndex = parts.lastIndexOf("tasks");
    if (tasksIndex >= 0 && parts[tasksIndex + 2] === "episodes" &&
        SAFE.test(parts[tasksIndex + 1]))
      return {name: parts[tasksIndex + 1], dataset: parts.slice(0, tasksIndex).join("/")};
    const task = manifest.task_class;
    if (typeof task === "string" && SAFE.test(task))
      return {name: task, dataset: parts.slice(0, -1).join("/")};
    return null;
  }

  function assemble(entries, catalog) {
    const index = mappingIndex(catalog);
    const groups = new Map();
    for (const entry of entries) {
      const info = resolveTask(entry.parts, entry.manifest);
      if (!info) continue;
      const id = Number(entry.receipt.episode_id);
      const matched = index.get(info.name + ":" + id);
      const last = entry.manifest.states.at(-1).frame;
      const frames = matched?.ep.frames >= last + 1 ?
        matched.ep.frames : last + 1;
      const instruction = matched?.ep.instruction ||
        entry.manifest.task_instruction || entry.manifest.instruction || "";
      const key = info.dataset + "::" + info.name;
      if (!groups.has(key)) groups.set(key, {
        id: key, name: info.name, label: info.name,
        dataset: info.dataset, episodes: [],
        source_dir: matched?.task.source_dir || "",
        chunks_size: matched?.task.chunks_size || 1000,
        video_path: matched?.task.video_path || "",
      });
      const group = groups.get(key);
      group.episodes.push({
        global_id: id, local_id: matched?.ep.local_id ?? id,
        frames, instruction, complete: entry.receipt,
        manifest: entry.manifest, entry,
      });
    }
    const tasks = [...groups.values()];
    const duplicates = new Map();
    for (const task of tasks)
      duplicates.set(task.name, (duplicates.get(task.name) || 0) + 1);
    for (const task of tasks) {
      task.episodes.sort((a, b) => a.global_id - b.global_id);
      task.count = task.episodes.length;
      if (duplicates.get(task.name) > 1)
        task.label = task.name + " · " + task.dataset;
    }
    tasks.sort((a, b) => a.label.localeCompare(b.label, "zh-CN", {numeric: true}));
    return tasks;
  }

  async function fileAt(handle, parts) {
    if (!parts.length || parts.some(p => !SAFE.test(p) || p === ".."))
      throw new Error("无效的相对路径");
    let directory = handle;
    for (const part of parts.slice(0, -1))
      directory = await directory.getDirectoryHandle(part);
    const file = await directory.getFileHandle(parts.at(-1));
    return file.getFile();
  }

  async function jsonFile(handle, filename) {
    try {
      const file = await handle.getFileHandle(filename);
      return JSON.parse(await (await file.getFile()).text());
    } catch (error) {
      if (error.name === "NotFoundError" || error instanceof SyntaxError)
        return null;
      throw error;
    }
  }

  function createHandleProvider(root, catalog) {
    const urls = new Map();
    return {
      root, type: "handle",
      async scan(onProgress = () => {}) {
        const result = [];
        let directories = 0;
        const visit = async (directory, parts, depth) => {
          if (++directories > MAX_DIRS)
            throw new Error("扫描超过 " + MAX_DIRS + " 个目录，请选择更具体的父目录");
          if (depth > MAX_DEPTH) return;
          const match = directory.name.match(EPISODE);
          if (match) {
            const [complete, manifest] = await Promise.all([
              jsonFile(directory, "COMPLETE.json"),
              jsonFile(directory, "episode_manifest.json"),
            ]);
            if (validManifest(complete, manifest, directory.name)) {
              result.push({parts, receipt: complete, manifest, handle: directory});
              if (result.length % 40 === 0)
                onProgress("已发现 " + result.length + " 个完整 Episode");
              if (result.length > MAX_EPISODES)
                throw new Error("超过 " + MAX_EPISODES + " 个 Episode，请缩小目录范围");
            }
            // Never descend into frame or PNG directories within an Episode.
            return;
          }
          for await (const [name, child] of directory.entries()) {
            if (child.kind !== "directory" || SKIP.has(name) ||
                name.startsWith("state_") || name.startsWith(".") ||
                !SAFE.test(name)) continue;
            await visit(child, [...parts, name], depth + 1);
          }
        };
        await visit(root, [root.name], 0);
        const tasks = assemble(result, catalog);
        onProgress("扫描完成 · " + result.length + " 个 Episode · " +
          tasks.length + " 个任务目录");
        return tasks;
      },
      async getFile(ep, relative) {
        return fileAt(ep.entry.handle, relative.split("/"));
      },
      async getUrl(ep, relative) {
        const key = ep.entry.parts.join("/") + "/" + relative;
        if (urls.has(key)) return urls.get(key);
        const file = await this.getFile(ep, relative);
        const url = URL.createObjectURL(file);
        urls.set(key, url);
        return url;
      },
      release() {
        for (const url of urls.values()) URL.revokeObjectURL(url);
        urls.clear();
      },
    };
  }

  function createFileListProvider(files, catalog) {
    const map = new Map(), urls = new Map();
    for (const file of files) {
      const full = file.webkitRelativePath || file.name;
      const parts = full.split("/");
      if (!parts.length || parts.some(part => !SAFE.test(part))) continue;
      map.set(parts.join("/"), file);
    }
    return {
      type: "filelist",
      async scan(onProgress = () => {}) {
        const result = [];
        for (const [path, file] of map) {
          if (!path.endsWith("/COMPLETE.json")) continue;
          const parts = path.split("/");
          const dirname = parts.at(-2);
          if (!EPISODE.test(dirname)) continue;
          const manifestFile = map.get(parts.slice(0, -1).join("/") +
            "/episode_manifest.json");
          if (!manifestFile) continue;
          let complete, manifest;
          try {
            [complete, manifest] = await Promise.all([
              file.text().then(JSON.parse), manifestFile.text().then(JSON.parse),
            ]);
          } catch (error) {
            if (error instanceof SyntaxError) continue;
            throw error;
          }
          if (validManifest(complete, manifest, dirname)) {
            result.push({parts: parts.slice(0, -1), receipt: complete,
              manifest, prefix: parts.slice(0, -1).join("/")});
            if (result.length % 40 === 0)
              onProgress("已发现 " + result.length + " 个完整 Episode");
            if (result.length > MAX_EPISODES)
              throw Error("目录包含过多 Episode，请选择更具体的父目录");
          }
        }
        const tasks = assemble(result, catalog);
        onProgress("扫描完成 · " + result.length + " 个 Episode");
        return tasks;
      },
      async getFile(ep, relative) {
        const file = map.get(ep.entry.prefix + "/" + relative);
        if (!file) throw new Error("图片未包含在所选文件夹：" + relative);
        return file;
      },
      async getUrl(ep, relative) {
        const key = ep.entry.prefix + "/" + relative;
        if (urls.has(key)) return urls.get(key);
        const file = await this.getFile(ep, relative);
        const url = URL.createObjectURL(file);
        urls.set(key, url);
        return url;
      },
      release() {
        for (const url of urls.values()) URL.revokeObjectURL(url);
        urls.clear();
      },
    };
  }

  // If explicitly selected, local source videos override the default server.
  async function videoFile(root, task, episode, cameraKey) {
    const template = task.video_path;
    if (!template || !task.source_dir) return null;
    const local = episode.local_id;
    const name = template
      .replace("{episode_chunk:03d}",
        String(Math.floor(local / task.chunks_size)).padStart(3, "0"))
      .replace("{video_key}", cameraKey)
      .replace("{episode_index:06d}", String(local).padStart(6, "0"));
    for (const parts of [
      [...task.source_dir.split("/"), ...name.split("/")],
      name.split("/"),
    ]) {
      try { return await fileAt(root, parts); }
      catch (error) {
        if (error.name !== "NotFoundError") throw error;
      }
    }
    return null;
  }

  host.G2DirectorySource = {
    mappingIndex, validManifest, resolveTask, assemble,
    createHandleProvider, createFileListProvider, videoFile,
  };
  if (typeof module !== "undefined" && module.exports)
    module.exports = host.G2DirectorySource;
})(typeof window !== "undefined" ? window : globalThis);