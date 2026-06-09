# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 上游构建系统重构
- 新模式症状关键词: `ModuleNotFoundError: No module named 'getdeps.facebook'`, `Can't instantiate abstract class ArchiveFetcher with abstract methods clean, hash`, `manifest.py`, `_create_fetcher`

## 根因分析

### 直接错误
```
#11 7.225 Traceback (most recent call last):
#11 7.225   File "/build/build/fbcode_builder/getdeps/manifest.py", line 634, in _create_fetcher
#11 7.225     from .facebook.lfs import LFSCachingArchiveFetcher
#11 7.225 ModuleNotFoundError: No module named 'getdeps.facebook'
#11 7.225
#11 7.225 During handling of the above exception, another exception occurred:
#11 7.225
...
#11 7.229   File "/build/build/fbcode_builder/getdeps/manifest.py", line 647, in _create_fetcher
#11 7.229     return ArchiveFetcher(
#11 7.229            ^^^^^^^^^^^^^^^
#11 7.229 TypeError: Can't instantiate abstract class ArchiveFetcher with abstract methods clean, hash
```

### 根因定位
- 失败位置: `build/fbcode_builder/getdeps/manifest.py:647`
- 失败原因: fbthrift `v2026.06.08.00` 上游将 `ArchiveFetcher` 重构为抽象类（要求子类实现 `clean` 和 `hash` 方法），同时内部构建依赖 Facebook 专用模块 `getdeps.facebook.lfs.LFSCachingArchiveFetcher`。在开源环境下该模块加载失败后，回退逻辑直接实例化抽象类 `ArchiveFetcher`，导致 TypeError。

### 与 PR 变更的关联
PR 新增的 `fix_getdeps.py` 仅处理两项兼容性适配：
1. 添加 "openeuler" 到发行版识别列表
2. 跳过 libaio 哈希校验

但未处理 fbthrift `v2026.06.08.00` 版本上游构建系统的重大变更——`ArchiveFetcher` 从具体类变为抽象类，且缺少开源环境下的可用具体实现。`fix_getdeps.py` 中 `fetcher.py` 的 `_verify_hash` 方法替换与 `manifest.py` 的 `ArchiveFetcher` 抽象化完全无关（两者在不同文件中），因此该补丁无法修复此问题。

**结论：此失败由 PR 引入的新版本直接触发**。旧版本（如 `v2026.05.18.00`）的 `ArchiveFetcher` 为非抽象类，不依赖 Facebook 内部模块即可正常工作；新版本构建系统重构后，`fix_getdeps.py` 的适配策略已不足。

## 修复方向

### 方向 1（置信度: 高）
在 `fix_getdeps.py`（或新建 patch 文件）中增加对 `manifest.py` 的修补：为 `ArchiveFetcher` 的子类或具体实现补充 `clean` 和 `hash` 方法，或修改 `_create_fetcher` 的回退路径使其不直接实例化抽象类 `ArchiveFetcher`。可参照同仓库中 libyuv 的做法——在 `git clone` 后、构建前用 Python/sed 对上游源码进行针对性 patch。

### 方向 2（置信度: 中）
检查 fbthrift `v2026.06.08.00` 的 `manifest.py` 中 `_create_fetcher` 方法的完整回退逻辑。`ModuleNotFoundError` 被捕获后原本应有一个合法的 fetcher 回退，但当前回退到了无法实例化的抽象类。可能需要从 `manifest.py` 中找到 `ArchiveFetcher` 的某个开源可用的具体子类（如 `SimpleArchiveFetcher`、`GitFetcher` 等）来替代回退目标。

## 需要进一步确认的点
- fbthrift `v2026.06.08.00` 的 `manifest.py` 中 `ArchiveFetcher` 是否有开源可用的具体子类可作为回退（当前日志只显示回退到了抽象类本身）
- `fix_getdeps.py` 中针对 `fetcher.py` 的 `_verify_hash` patch 是否由于上游方法签名变化而匹配失败（regex 依赖 `\n    def ` 为方法边界标识，上游重构后缩进或方法顺序可能改变）
- 旧版本 `v2026.05.18.00` 的构建是否确实成功（以确认此问题是版本升级引入的回归，而非预存问题）
