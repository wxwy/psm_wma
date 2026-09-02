# R09-B2 P4-v4 Execution Request `interpreter` 静态合同 v0.2

**状态**：draft；整改 Kimi 对 v0.1 的 `REQUEST_CHANGES`，仅申请 root static parser/validator tooling 与 stdlib CPU fixtures。前置为 source closure root=`b0581d8`、review=`a9c2eb3`，并严格复用 interpreter provenance v1.3。

`interpreter` 精确键为 `python_path,python_payload_sha256,python_base_path,python_base_sha256,pyvenv_cfg_sha256,venv_lock_sha256,git_path,git_elf_sha256,git_closure_sha256,loader_args,identity_sha256`；identity 是删除自身字段后的 canonical JSON SHA256，所有 digest 为 64 lowercase hex。path 均绝对、strict-resolved、non-symlink regular file。

Python 不得声称 Git blob：`python_path` 是 lexical venv launcher，按单 fd `O_NOFOLLOW` 读取并绑定 payload SHA；其 symlink payload、base binary、`pyvenv.cfg` 和由 source revision 中已追踪 lock/registry 文件绑定的 wheel/RECORD 链，按 v1.3 重算并分别比对 `python_base_sha256`、`pyvenv_cfg_sha256`、`venv_lock_sha256`。venv 未追踪字节只接受上述 current-byte/no-follow 链，不接受伪造 Git blob。

Git 不得依赖 ambient `PATH`：`git_path` 是 host-native TCB 的绝对 executable，单 fd `O_NOFOLLOW`+`fstat`+single raw 绑定 `git_elf_sha256`；其 ELF interpreter、DT_NEEDED、RPATH/RUNPATH 和递归 canonical object SHA 集由 bytes 自行重算为 `git_closure_sha256`。不要求不存在的 source-root frozen Git binary；`which`、shell lookup、相对路径、shebang 均永久拒绝。

`loader_args` 必精确有序编码 `-I,-S,-B,-c,<64-hex bootstrap digest>,<absolute request path>,<64-hex request SHA>`；bootstrap 仍以 v1.3 Git/current-byte verified loader binding。永久拒绝 direct exporter、`-m`、缺失/重排 flags、额外 argv 与任一 unbound executable。

CPU fixtures必须覆盖 venv payload/base/cfg/lock drift、host Git ELF/closure drift、Python/Git symlink/replacement、ambient PATH shadow、loader argv/bootstrap/request SHA drift及无 pathname reopen。任一失败 ValueError，既有 hard-stop 不变。

请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_INTERPRETER_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。禁止真实 preflight、staging/materialize、record/refreeze、P5 export/compose、torchrun、GPU、模型/数据/checkpoint I/O、训练/评测/推理、B2-T 或 Local Memory 训练。
