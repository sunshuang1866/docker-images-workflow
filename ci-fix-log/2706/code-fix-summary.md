# 修复摘要

## 修复的问题
预置 libaio tarball 解压后内部目录名为 `libaio-0.3.113`，与 getdeps manifest 中声明的 `subdir = libaio-libaio-0.3.113` 不匹配，导致 getdeps 在错误的目录中执行 `make` 而失败（"No targets specified and no makefile found"）。

## 修改的文件
- `Others/fbthrift/2026.06.22.00/24.03-lts-sp3/fix_getdeps.py`: 新增第 23-27 行，在脚本末尾添加对 libaio manifest 的 `subdir` 字段的 patch，将 `libaio-libaio-0.3.113` 修正为 `libaio-0.3.113`，以匹配预置 tarball 的实际内部目录结构。

## 修复逻辑

**根因**：CI 分析报告指出 `make: *** No targets specified and no makefile found.` 的直接原因是 libaio 源码提取后缺少 Makefile。经验证：
1. 预置的 `libaio-libaio-0.3.113.tar.gz` 内部顶层目录为 `libaio-0.3.113/`，且该目录内确实包含 `Makefile`（通过 `tar tzf` 验证 tarball 内容）。
2. fbthrift v2026.06.22.00 的 manifest（`build/fbcode_builder/manifests/libaio`）中声明 `subdir = libaio-libaio-0.3.113`（已从上游 `https://raw.githubusercontent.com/facebook/fbthrift/v2026.06.22.00/build/fbcode_builder/manifests/libaio` 获取验证）。
3. getdeps 提取 tarball 后会 cd 到 `{extract_dir}/{subdir}` 执行 `make`，由于 subdir 名不匹配，make 在父目录中执行（父目录无 Makefile），导致构建失败。

**修复**：在 `fix_getdeps.py` 中增加第 3 步，用字符串替换将 manifest 中的 `subdir` 值从 `libaio-libaio-0.3.113` 改为 `libaio-0.3.113`，使 getdeps 能正确进入含有 Makefile 的源码目录进行构建。

**正则验证**：已从上游 `fbthrift v2026.06.22.00` 获取 `build/fbcode_builder/getdeps/fetcher.py`，其中 `_verify_hash` 方法签名为 `def _verify_hash(self) -> None:`，经 Python 测试确认 `fix_getdeps.py` 第 17-20 行的正则 `r'def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )'` 能正确匹配该方法体，正则 patch 有效。

## 潜在风险
- 修复假设预置 tarball 中的 `libaio-0.3.113/Makefile` 能够正常编译 libaio。若该 tarball 来源于 Ubuntu Launchpad 的 Debian 打包源码而非上游 libaio 发布源码，其 Makefile 可能包含 Debian 特定逻辑导致后续编译失败。若出现此情况，需从 pagure.io 官方源重新获取 tarball。
- Boost CMake `SEND_ERROR` 冲突（日志中的次要问题）与当前修复无关，未处理。