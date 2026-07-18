# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI 测试框架缺少 shunit2
- 新模式症状关键词: shunit2: file not found, Check test failed, common_funs.sh, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 测试阶段的 `eulerpublisher` 容器测试脚本 `common_funs.sh` 尝试 `source` 加载 `shunit2` 单元测试框架，但该框架未安装或不在运行路径中，导致 `[Check] test failed`。Docker 镜像的 **Build 和 Push 阶段均已完成并成功**（422/422 编译目标通过，镜像已推送至 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`），失败仅发生在测试后处理阶段。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 仅新增 bind9 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套配置文件（`named.conf`、`README.md`、`image-info.yml`、`meta.yml`），构建过程完整通过（meson 编译 422 个目标、链接 56 个产物、安装全部成功），镜像已成功推送。失败是 CI runner 上 `shunit2` 测试框架缺失导致的基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
确认 CI 运行环境（aarch64 runner）上是否安装了 `shunit2` 测试框架。若未安装，需在测试阶段前通过包管理器（如 `yum install shunit2` 或 `pip install shunit2`）预装，或确保 `common_funs.sh` 脚本能正确定位 `shunit2` 文件的路径。此问题与本次 PR 无关，无需修改 Dockerfile 或构建逻辑。

## 需要进一步确认的点
1. 确认 aarch64 CI runner 的 `eulerpublisher` 测试环境中 `shunit2` 的预期安装路径和安装方式。
2. 确认同一 runner 上其他镜像的 Check 阶段是否也遇到相同问题（即该问题是否为新引入的 CI 环境变更所致）。
3. 确认 x86_64 架构的 Check 阶段是否通过（日志仅展示了 aarch64 架构的构建和测试）。
