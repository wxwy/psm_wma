# P5 Evidence Git Authority 静态整改设计 v1.0

仅设计/未来 root CPU tooling。P5 pair verifier 在读取 P4-v4 三文件前必须要求 `evidence_root` 与 `cosmos-framework` full-clean Git；固定路径三文件为 tracked regular files，逐一比对 `git show HEAD:<path>` bytes、current bytes 与 canonical JSON bytes。verifier 独立记录 root HEAD/Gitlink；非 Git、untracked、symlink、blob/current drift、三文件共同替换均 FAIL。临时 CPU fixture 改为真实临时 Git evidence checkout 并覆盖这些负例。禁止 preflight/staging/refreeze/export/compose/GPU/训练。
