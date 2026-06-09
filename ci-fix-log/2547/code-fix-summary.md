# 修复摘要

## 修复的问题
fbthrift v2026.06.08.00 上游将 `ArchiveFetcher` 重构为抽象类（要求子类实现 `clean` 和 `hash` 方法），`_create_fetcher` 在开源环境无法导入 `LFSCachingArchiveFetcher` 后回退到直接实例化抽象类 `ArchiveFetcher`，导致 `TypeError: Can't instantiate abstract class ArchiveFetcher with abstract methods clean, hash`。

## 修改的文件
- `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py`: 新增第 3 步补丁，在 `manifest.py` 末尾追加 monkey-patch 代码，为 `ArchiveFetcher` 提供 `clean` / `hash` 的具体实现并清除 `__abstractmethods__`，使回退路径可正常实例化。

## 修复逻辑
在 `fix_getdeps.py` 中新增对 `build/fbcode_builder/getdeps/manifest.py` 的补丁：读取文件后在末尾追加三行代码 —— 分别给 `ArchiveFetcher` 打上 `clean`（no-op）和 `hash`（no-op）方法，并清空 `__abstractmethods__`。这样当 `_create_fetcher` 的回退路径执行 `return ArchiveFetcher(...)` 时，Python 不再认为该类是抽象的，实例化成功。此补丁在 `git clone` 源码后、`getdeps.py` 构建前执行，与现有补丁 #1、#2 的执行时机和方式一致。

## 潜在风险
无。`clean` 和 `hash` 的 no-op 实现仅影响开源环境下的 `ArchiveFetcher` 回退路径；PR 中已提供预下载的 libaio 归档并跳过了 `_verify_hash` 校验，不依赖 `hash` 返回值。