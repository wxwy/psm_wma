# Authority-root Execution Authority Implementation 设计 v0.2

**日期**：2026-09-12
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-EXECUTION-AUTHORITY-IMPLEMENTATION-DESIGN`
**状态**：docs-only；替代 v0.1 的两项 HIGH；待三方审核。

本版继承 v0.1 的两文件 allowlist、四模块 closure、禁止真实 materialization/child/GPU/训练范围；仅把 ChatGPT `569a34d` HIGH-1/2 变为可实现合同。

## 1. 进程级 bootstrap 观测

唯一启动序列为 `<frozen-python> -I -S -B -c <bootstrap-utf8> -- <adapter-argv...>`。bootstrap 在 project import 前只从 Python 3.11 `sys.orig_argv` 读取实际进程参数，逐项要求 `[frozen_python,"-I","-S","-B","-c",bootstrap_utf8,"--",*adapter_argv]`。不得用 `sys.argv`、环境变量、caller hash、fixture builder 或模板代替。

```text
observed_bootstrap_raw_sha256 = sha256(sys.orig_argv[5].encode("utf-8"))
observed_bootstrap_argv_sha256 = sha256(canonical_json(sys.orig_argv[6:]))
```

canonical JSON 固定 UTF-8、`sort_keys=True`、`separators=(",", ":")`、`ensure_ascii=False`。非 UTF-8 round-trip、额外/缺失 flag、错误 `--`、解释器路径或声明/观察摘要不等均在 `sys.path.insert`、`runpy`、project import、Git/evidence action前退出。Evidence-v1 exact-check declared/observed 两对摘要。CPU/static 必须真实启动 `python -I -S -B -c`，只替换 `-c` payload而保持声明摘要，证明 runpy/Git/evidence counters为零。

## 2. 精确 native-Git isolation

Git 子进程使用不继承父环境的 exact env，仅允许：`GIT_INDEX_FILE`、`GIT_NO_REPLACE_OBJECTS=1`、`GIT_CONFIG_NOSYSTEM=1`、`GIT_CONFIG_GLOBAL=/dev/null`、`GIT_CONFIG_SYSTEM=/dev/null`、`LC_ALL=C`、`LANG=C`及六个冻结 commit metadata键。每条命令使用固定 prefix：

```text
<frozen-git> --no-replace-objects
  -c core.hooksPath=/dev/null
  -c core.attributesFile=/dev/null
  -c filter.lfs.process=
  -c protocol.file.allow=never
```

生产 endpoint 只接受无 credential/query/fragment 的 canonical `https://<lowercase-host>/<nonempty-path>`；禁止 alias、relative/path endpoint、`url.*.insteadOf`输入和自动重写。`git_isolation_fingerprint=sha256(canonical_json({env,prefix,endpoint_grammar,local_config_policy}))`由 production code计算。

authority action前对实际 Git-dir config作 lstat regular/non-symlink+raw-SHA检查，并以`git config --no-includes --local --null --list`拒绝`include*`、`url.*`、`remote.*`、`protocol.*`、`core.hooksPath`、`core.attributesFile`、`filter.*`、`alias.*`及非固定 allowlist key。next request冻结 config SHA/allowlist；不匹配即首个 object/ref/transport action前退出。每个`ls-remote`/push只接收endpoint字节。

## 3. Direct native witnesses

除 injected error seam 外，existing test创建temporary Git repo和temporary local bare remote（绝不用project origin），经 production `NativeAuthorityGit`验证replace ref、`url.*.insteadOf`、include、remote alias、hook/filter/attributes/protocol config均pre-action拒绝；正例经真实local bare remote完成create/delete CAS。test-only local transport由constructor seam注入，production parser仍拒绝非 HTTPS endpoint。保留所有v0.1四模块/FD/argv/evidence exact-key测试；运行完整stdlib unittest、Ruff、py_compile、diff-check；不运行真实动作。

## 4. 请求 verdict

请求唯一`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC`或`REQUEST_CHANGES(file:line)`；三方同pair批准前不得改两root文件或执行真实动作。
