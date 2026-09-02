# P5 Evidence Git Authority 静态整改设计 v1.1

仅设计。P5 verifier tooling 必内置 reviewed `AUTHORIZED_P4_V4_EVIDENCE`：exact evidence commit、tree SHA256、Gitlink、及固定 request/result/verification Git-blob SHA256；该常量只能在 record/refreeze closure 后以新 reviewed verifier revision写入，三文件永不自证该 commit。

接受 evidence root 仅当：full-clean；HEAD 等于 authorized commit（不接受 descendant）；`git ls-tree HEAD cosmos-framework` Gitlink 等于 authorized Gitlink 且等于 submodule HEAD；三个 tracked regular fixed files的 `git show authorized_commit:<path>` bytes/current bytes/canonical bytes SHA 均等于 frozen blob SHA。共同替换并提交新 clean HEAD、错误 clean submodule、任意 descendant、untracked/symlink/blob drift 均 FAIL。CPU Git fixtures永久覆盖上述负例。禁止 runtime、staging、refreeze、export、GPU与训练。
