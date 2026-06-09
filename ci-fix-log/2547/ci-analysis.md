# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: build-error
- 置信度: 低
- 知识库匹配: 模式22
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
日志被截断，可见部分未出现致命错误。日志覆盖了 getdeps 依赖构建阶段：
- zstd → boost → glog → gflags → googletest（构建/安装中）
- fbthrift 自身编译尚未出现在可见日志中
- Boost 构建过程中出现大量 `message(SEND_ERROR "Target Boost::xxx already has an imported location...")` ，但 CMake `SEND_ERROR` 不会中止构建，属于非致命警告

日志截断点位于 googletest 安装阶段，实际致命错误极可能发生在截断之后的 fbthrift 编译阶段。

### 根因定位
- 失败位置: 无法定位 — 日志截断前未出现致命错误
- 失败原因: **证据不足，无法确定根因**。唯一可识别的问题是 PR 中新增的 `fix_getdeps.py`（文件 `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py`）存在正则替换边界缺陷。

### 与 PR 变更的关联
本次 PR 新增了 3 个关键文件：
1. `Dockerfile` — 构建入口
2. `fix_getdeps.py` — 用于适配 openEuler 发行版识别 + 跳过 libaio 的哈希校验
3. `libaio-libaio-0.3.113.tar.gz` — 预下载的 libaio 源码包

`fix_getdeps.py` 中跳过 `_verify_hash` 的正则表达式存在边界 bug：
```python
re.sub(
    r'def _verify_hash\(self\):.*?(?=\n    def )',
    'def _verify_hash(self):\n        pass',
    c2,
    flags=re.DOTALL
)
```
正则中的正向前瞻 `(?=\n    def )` 要求 `_verify_hash` 方法后面必须有另一个 `def` 方法定义。如果 `_verify_hash` 是类中最后一个方法（后面无 `def`），则该正则会匹配失败，导致替换**静默不生效**，libaio tarball 的哈希校验未被跳过。

当 libaio 哈希校验未正确跳过时，使用本地预下载的 `libaio-libaio-0.3.113.tar.gz`（与上游原始 tarball 哈希不一致）会导致 `_verify_hash` 抛出校验失败异常，使 getdeps 构建流程中断。但日志中未看到该错误，说明：
- 要么日志截断位置早于该校验发生时机
- 要么上游 `fetcher.py` 的代码结构恰好使正则匹配成功（`_verify_hash` 后仍有其他方法），真正的失败原因在更后面的 fbthrift 编译阶段

## 修复方向

### 方向 1（置信度: 高）
**修复 `fix_getdeps.py` 中 `_verify_hash` 替换正则的边界问题**。将正则从依赖正向前瞻 `(?=\n    def )` 改为不依赖后续方法存在的方式。例如使用 `$`（类结束边界）作为备选匹配终点，或将整个方法的 body 从 `def _verify_hash` 到下一个同级 `def` 或类结束的所有内容都替换为 `pass`。

### 方向 2（置信度: 低）
**日志不足以定位真正确切的失败点**。如果方向 1 修复后仍然失败，需要获取完整的未截断 CI 日志，以确认是对 libaio 哈希校验失败，还是 fbthrift 编译/链接阶段的其他错误（如缺少依赖、C++ 编译错误等）。

## 需要进一步确认的点
1. **获取完整 CI 日志**：当前日志在 googletest 安装阶段截断，需完整日志确认致命错误的精确位置和内容
2. **确认 `_verify_hash` 在 `fetcher.py` 中的位置**：是否为类中最后一个方法（决定正则是否能匹配成功）
3. **确认 libaio tarball 的下载与校验时机**：是在依赖构建前还是 fbthrift 构建前触发
4. **确认 fbthrift v2026.06.08.00 与 openEuler 24.03-lts-sp3 的编译兼容性**：是否存在版本特定的编译/链接问题
