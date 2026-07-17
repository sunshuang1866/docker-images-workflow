# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（类似模式39）
- 新模式标题: CI缺少shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher, check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 编排工具 `eulerpublisher` 的 [Check] 阶段在执行镜像测试时，尝试通过 `source shunit2` 加载 shunit2 测试框架，但该框架在 CI runner 上未安装/不可用，导致整个 Check 阶段崩溃。

### 与 PR 变更的关联

**与 PR 代码变更无关**。证据：
1. Docker 镜像构建阶段（`[Build]`）完全成功——PostgreSQL 17.6 从源码编译、安装、binary 打包和 Docker 分层全部正常完成，exit code 为 0。
2. 镜像推送阶段（`[Push]`）完全成功——镜像已成功推送到 `docker.io/****test/postgres:17.6-oe2403sp4-x86_64`。
3. 失败仅发生在 `eulerpublisher` 的 [Check] 后处理阶段（`2026-07-09 09:40:24,021`），即构建和推送均已完成后才报错。
4. `shunit2` 是 CI runner 宿主环境的系统级测试框架依赖，不属于 Dockerfile 或其构建产物。
5. BuildKit 报告的两个 `LegacyKeyValueFormat` 警告（Dockerfile 第 26、30 行的 `ENV` 格式）是**信息性警告（warnings）**，不会导致构建失败。

该问题与模式39（CI工具依赖缺失，`eulerpublisher` 缺少 `distroless` 模块）性质相同，均属于 CI 基础设施的运行时依赖缺失。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施需要在运行 `eulerpublisher` [Check] 阶段的 runner（x86_64 和 aarch64 构建节点）上安装 `shunit2` 包。这属于 CI 运维层面的问题，**无需修改 Dockerfile 或任何 PR 代码**。Code-fixer 无需处理，应由 CI 基础设施团队在 runner 镜像中补充 `shunit2` 依赖。

## 需要进一步确认的点

1. 确认该 CI runner（x86_64 构建节点）上 `shunit2` 的安装状态——是否之前可用但近期被移除，或是新 runner 镜像遗漏了该依赖。
2. 确认同 PR 的 aarch64 构建 job 日志中是否也有相同的 `shunit2: No such file or directory` 错误（如果 aarch64 job 也失败的话，说明两个架构的 runner 都缺少该依赖）。
3. 确认 CI 编排层是否有独立的 shunit2 安装步骤被跳过或失败。
