# Real-output request-instance writer implementation design v0.1

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-REQUEST-INSTANCE-REAL-OUTPUT-WRITER-IMPLEMENTATION-DESIGN`

本设计复用已批准 real-output design formal root=`32e0486353754ff975c24f979076baf95f0d038a`、child=`93a89ba61306d840a008813f62f26a34d54850f4`，以及既有 `tools/psm_wma/immutable_source_collection.py:AtomicFileEvidenceSink` 的 no-follow/link/fsync 语义。

## 实现边界

唯一入口为 `tools/psm_wma/write_source_evidence_closure_request_instance.py:write_request_pair`；测试为同名
`test_*.py`，白名单另含 `TODO.md`、`SESSION.md` 与本设计。入口只接受已由 constructor 生成并验证的 JSON bytes、
detached Markdown bytes 和显式目标目录；不得自行读取 source、执行 Git/网络或调用 torch/CUDA。

## CPU/static 合约

测试使用 temporary fixture 验证：staging 目录 `0700`、staged 文件 `O_CREAT|O_EXCL|O_NOFOLLOW`/`0644`，单 fd
写入+`fsync`，parent fsync；按 JSON→Markdown 顺序以 `os.link(..., follow_symlinks=False)` 发布，`EEXIST` 为
`REAL_OUTPUT_WRITE_FAILED`，禁止 replace/unlink/retry。每次 link 后 parent fsync，并以 no-follow fd 验证 inode、
parent identity、mode/owner、size/raw SHA；成功后仅在全部 readback 通过时移除 staged names 和空 staging 目录。

失败 fixture 必须覆盖目标已存在、link/fsync/readback 失败及 JSON-only partial；只返回结构化 residue，不清理已发布
目标。真实固定路径执行另需 `APPROVE_TO_WRITE_SOURCE_EVIDENCE`，本 Gate 不写真实 instance、不执行 source I/O、
GPU 或训练。

请求 verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_REAL_OUTPUT_WRITER_CPU_STATIC`
或 `REQUEST_CHANGES(file:line)`。
