# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 的 `eulerpublisher` 测试环境中缺少 `shunit2` shell 测试框架，`common_funs.sh` 的 `source` 指令（`. shunit2`）无法找到该文件，导致 `[Check]` 阶段的容器测试无法执行。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建阶段完全成功：
- `meson setup / compile / install` 全部通过（422/422 编译目标）
- `groupadd` / `useradd` 创建用户成功（`#10 DONE 0.2s`）
- `COPY named.conf` 成功（`#11 DONE 0.0s`）
- 镜像导出与推送成功（`#13 DONE 36.0s`，manifest 已推送到 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`）

失败发生在构建完成后的 `[Check]` 阶段，即 `eulerpublisher` 工具调用 `shunit2` 对已构建容器做运行时健康检查时，因测试框架未安装而失败。这是 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 低）
在 CI Runner 镜像或构建环境配置中安装 `shunit2`（Shell 单元测试框架，通常可从 EPEL 或通过 `git clone` 获取）。具体安装方式需根据 CI Runner 的操作系统确定。

## 需要进一步确认的点
1. **是否仅有 aarch64 架构的日志**：日志中推送的镜像 tag 为 `9.21.23-oe2403sp4-aarch64`，需要确认 x86_64 架构 job 是否也失败以及是否因相同原因（shunit2 缺失）。
2. `shunit2` 在当前 CI Runner 环境中本应位于哪个路径（`/usr/local/etc/eulerpublisher/tests/container/common/` 或系统 PATH）。
3. 其他最近通过的 PR（如 bind9 的 sp3 构建）是否使用了相同的 CI Runner / Check 阶段，以确认 shunit2 是近期才缺失还是一直存在但被容错处理。
4. 若 shunit2 安装后 Check 仍失败，需获取容器运行时日志（`docker logs`）以排查 bind9 的实际启动行为。

## 修复验证要求
无需代码修复。此为 CI 基础设施问题，修复方式为在 CI Runner 环境中安装 `shunit2` 工具。若需验证，可在 Runner 上执行 `which shunit2` 或检查 `/usr/local/etc/eulerpublisher/tests/container/common/` 目录下是否存在 `shunit2` 文件。
