# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 模式22
- 新模式标题: (无)
- 新模式症状关键词: (无)

## 根因分析

### 直接错误
日志在 googletest 依赖构建阶段被截断，未见致命错误。日志覆盖的范围为 getdeps 依赖构建链：zstd → boost → glog → gflags → googletest，尚未进入 fbthrift 本身的编译阶段。实际失败原因无法从提供的日志中确定。

日志中出现的非致命信息：
- `#11 53.43 -- Failed to find LLVM FileCheck` — cmake 功能探测，不影响构建
- `#11 176.1 SEND_ERROR "Target Boost::date_time already has an imported location..."` — Boost 构建期间的 CMake 配置警告（SEND_ERROR 在 Boost b2 构建上下文中为非致命警告），后续 Boost 库均成功编译并安装
- `#11 63.72 fatal: not a git repository (or any of the parent directories): .git` — 构建脚本在解压后的 tarball 目录中执行 git 命令，非致命

### 根因定位
- 失败位置: 无法定位 — 日志截断前未出现导致构建终止的致命错误
- 失败原因: 证据不足，无法确定根因。日志仅覆盖依赖构建阶段，实际致命错误极可能发生在日志截断之后的 fbthrift 编译阶段

### 与 PR 变更的关联
本次 PR 新增了 fbthrift 2026.06.08.00 版本的 Dockerfile 及相关文件，属于**全新引入的构建配置**。此 failure 与 PR 变更直接相关（构建的就是 PR 新增的镜像），但具体失败原因需要完整日志才能判定。

根据知识库模式22 的历史记录，该 PR 曾存在 `fix_getdeps.py` 中 `_verify_hash` 方法替换正则在「类中最后一个方法」场景下匹配失败的已知问题，可能仍是根因。

## 修复方向

### 方向 1（置信度: 低）
检查 `fix_getdeps.py` 中 `_verify_hash` 方法替换的正则表达式边界匹配问题。当前正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 使用「下一个 `def `」作为前瞻边界，当 `_verify_hash` 是类中最后一个方法时前瞻无法匹配，导致替换静默失败。

### 方向 2（置信度: 低）
日志被截断，实际错误可能完全不同于模式22 定位的问题。需获取完整日志后才能进一步分析。

## 需要进一步确认的点
1. **获取完整 CI 日志**：当前日志在 googletest 构建阶段被截断，需要获取 fbthrift 编译阶段的完整日志才能定位真正的致命错误
2. **确认日志截断原因**：日志是被 CI 系统的行数限制截断，还是构建在该阶段因超时被终止
3. **验证 fix_getdeps.py 正则有效性**：在目标 `fetcher.py` 源文件中确认 `_verify_hash` 方法后是否有后续方法定义，判断正则是否能正确匹配
4. **确认 fbthrift v2026.06.08.00 上游代码变化**：该版本可能引入了新的编译依赖或代码变更，导致之前有效的构建流程失效
