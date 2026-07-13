# 修复摘要

## 修复的问题
CI 构建失败根因为 **infra-error**（构建节点磁盘耗尽），非代码缺陷。同时修复了 Dockerfile 中 2 处 BuildKit `UndefinedVar` 警告（模式20）。

## 修改的文件
- `AI/cann/8.2.RC1.alpha002-python3.10/24.03-lts-sp4/Dockerfile`: 修复 ENV 自引用未定义变量产生的 UndefinedVar 警告
  - 第 108 行: `$LD_LIBRARY_PATH` → `${LD_LIBRARY_PATH:-}`（首次定义 LD_LIBRARY_PATH 时自引用了不存在的变量）
  - 第 111 行: `$PYTHONPATH` → `${PYTHONPATH:-}`（首次定义 PYTHONPATH 时自引用了不存在的变量）

## 修复逻辑
- **磁盘耗尽（infra-error）**：CANN 工具包完整安装后体积数 GB，BuildKit 在导出镜像层时 CI 节点磁盘空间不足。此问题需 CI 运维侧扩容构建节点磁盘配额（建议 `/var/lib/buildkit` 所在分区至少 30-50GB 可用），或为 CANN 类大镜像分配专用大容量节点。不在代码修复范围内。
- **UndefinedVar 警告（模式20）**：Dockerfile 第108行 `ENV LD_LIBRARY_PATH=...:$LD_LIBRARY_PATH` 和第111行 `ENV PYTHONPATH=...:$PYTHONPATH` 在首次定义变量时自引用了尚未存在的变量，导致 BuildKit 产生警告。使用 shell 默认值语法 `${VAR:-}` 替代裸引用 `$VAR`，当变量未定义时展开为空字符串，消除警告且不影响功能（因为首次定义前变量本应为空）。

## 潜在风险
无。`${VAR:-}` 与 `$VAR` 在 VAR 未定义时行为一致（均展开为空字符串），仅在 VAR 已定义时有差异（前者保持原值，后者追加），而此处恰好是首次定义，语义完全相同。