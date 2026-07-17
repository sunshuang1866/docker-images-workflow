# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2 缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段的测试框架脚本 `common_funs.sh` 在第 13 行尝试 source `shunit2`（shell 单元测试库），但该库在 CI runner 环境中不存在或不在可搜索路径中，导致容器测试无法执行。

### 与 PR 变更的关联
**与 PR 变更无关**。证据：
1. Docker 镜像构建阶段（`#9` meson compile + install）成功完成，所有 422 个编译目标全部通过，二进制文件正常安装到 `/usr/bin`、`/usr/sbin`、`/usr/lib64` 等路径。
2. Push 阶段也成功完成（`[Push] finished`），镜像已推送到 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`。
3. 失败仅发生在 [Check] 阶段——即 CI 工具 `eulerpublisher` 调用测试框架验证容器的环节。`shunit2` 是 CI 测试基础设施的一部分（位于 `/usr/local/etc/eulerpublisher/tests/`），而非容器镜像或 Dockerfile 的组成部分。PR 的改动（新增 Dockerfile、named.conf、文档更新）完全不涉及测试框架的配置。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 环境中安装 `shunit2` 测试框架。`shunit2` 是一个 shell 单元测试库（详见 https://github.com/kward/shunit2），需确保其可执行文件位于 `/usr/local/etc/eulerpublisher/tests/container/common/` 目录或系统的 `PATH` 中，使 `common_funs.sh` 的 `. shunit2` 能够正确 source。

### 方向 2（置信度: 低）
若 `shunit2` 已安装在 CI runner 上但路径配置错误，可能需要检查 `common_funs.sh` 中 source 路径是否为相对路径引用（如 `./shunit2` 或 `../lib/shunit2`）而非裸 `shunit2`，确保路径与 runner 上的实际安装位置一致。

## 需要进一步确认的点
1. 确认同一节点上其他已通过 [Check] 阶段的应用镜像（如同为 openEuler 24.03-LTS-SP4 的镜像）是否也使用同一 `common_funs.sh` 测试框架。若其他 SP4 镜像的 [Check] 能通过，则可能不是全局 infra 问题，需排查此 PR 触发的测试路径是否存在特殊逻辑。
2. 确认 `shunit2` 的预期安装位置——是在 CI runner 的系统路径中，还是随 `eulerpublisher` 包一起安装到某个特定目录（如 `/usr/local/etc/eulerpublisher/tests/container/common/shunit2`）。
3. 向 CI 运维确认该 runner 是否存在近期环境变更导致 `shunit2` 被误删或未安装。

## 修复验证要求
此失败为 infra-error，不涉及 Dockerfile 或代码修复，code-fixer 无需处理。建议由 CI 运维排查 runner 环境。
