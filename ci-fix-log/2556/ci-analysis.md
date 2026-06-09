# CI 失败分析报告

## 基本信息
- PR: #2556 — fix: libyuv 1948 (fix #2546)
- 失败类型: N/A（本次 CI 构建成功，无失败）
- 置信度: 高
- 知识库匹配: 模式21
- 新模式标题: —
- 新模式症状关键词: —

## 根因分析

### 直接错误
本次 CI 运行**未出现错误**，构建、编译、安装、导出、推送全过程均成功完成。CI 日志最终状态：
```
2026-06-09 12:56:21,254 - INFO - [Build] finished
2026-06-09 12:56:21,254 - INFO - [Push] finished
Finished: SUCCESS
```

### 根因定位
- 失败位置: N/A（本次构建成功）
- 失败原因: N/A

**说明**：PR #2556 是 PR #2546 的修复 PR。PR #2546 的失败模式为 **模式21：ENV自引用未定义变量**：

> `Others/libyuv/1948/24.03-lts-sp3/Dockerfile:19` — `ENV LD_LIBRARY_PATH=/usr/local/lib:/libyuv/build:$LD_LIBRARY_PATH` 在一个全新构建阶段中自引用了 `$LD_LIBRARY_PATH`。该变量此前从未在同一构建阶段被定义，BuildKit 检测到对未定义变量的引用，产生 `UndefinedVar` 警告。

PR #2556 的 Dockerfile 将第 19 行修改为：
```dockerfile
ENV LD_LIBRARY_PATH=/usr/local/lib:/libyuv/build
```
移除了 `:$LD_LIBRARY_PATH` 自引用，CI 构建通过。

### 与 PR 变更的关联
PR #2556 的变更是针对 PR #2546 的修复。变更包括：
1. 新增 `Others/libyuv/1948/24.03-lts-sp3/Dockerfile`（21 行，ENV 行不再自引用）
2. 更新 `Others/libyuv/README.md`（新增 1948-oe2403sp3 条目）
3. 更新 `Others/libyuv/doc/image-info.yml`（新增 1948-oe2403sp3 条目）
4. 更新 `Others/libyuv/meta.yml`（新增 1948-oe2403sp3 版本路径）

核心修复：Dockerfile 中 ENV 行从 `ENV LD_LIBRARY_PATH=/usr/local/lib:/libyuv/build:$LD_LIBRARY_PATH` 改为 `ENV LD_LIBRARY_PATH=/usr/local/lib:/libyuv/build`。

本次 CI 日志确认修复有效，全部步骤正常通过。

## 修复方向
本次 CI 已成功，无需修复操作。

## 需要进一步确认的点
- CI 日志中有一个 WARNING：`[Check] File: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/libyuv_test.sh does not exist, no test runs.` — 缺少 libyuv 功能测试脚本，虽然不影响构建成功，但无法验证容器内 libyuv 库的实际可用性。如需完善测试覆盖，可在对应路径补充 `libyuv_test.sh` 测试脚本。
