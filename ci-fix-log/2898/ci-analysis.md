# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI测试框架依赖缺失
- 新模式症状关键词: `shunit2, No such file or directory, common_funs.sh, eulerpublisher, Check test failed`

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 在执行 `[Check]` 阶段时，`common_funs.sh` 脚本尝试 source `shunit2`（Shell 单元测试工具），但该工具未安装在 CI runner 上，导致测试无法启动。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建（`[Build]`）和推送（`[Push]`）阶段均成功完成：
- 所有 5/5 个 Docker 构建步骤正常通过
- 镜像成功导出并推送到 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64`
- 日志中 `[Build] finished` 和 `[Push] finished` 均为 INFO 级别

失败仅发生在构建后的 `[Check]` 测试阶段，原因是 CI runner 上缺少 `shunit2` 工具，与本次 PR 新增的 Dockerfile 及其内容（Go 1.25.6 安装流程、meta.yml 条目、README 文档更新）无关。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 镜像或构建环境中安装 `shunit2` 测试框架。`shunit2` 是 shell 脚本测试工具，通常可通过包管理器（如 `dnf install shunit2`）或从源码安装到 `/usr/local/bin/` 等 PATH 路径下，确保 `common_funs.sh` 中 `source shunit2` 能正确找到该工具。

## 需要进一步确认的点
1. 本次提供的日志仅覆盖 aarch64 架构的构建和检查流程，需要确认 x86_64（amd64）架构的构建 job 日志是否存在同类问题。
2. 即使 `shunit2` 缺失问题修复后，`[Check]` 阶段的测试用例本身是否会因 Go 1.25.6 / openEuler 24.03-LTS-SP4 的组合而产生新的失败，当前无法确定——因为测试从未真正执行。
3. 需确认 `shunit2` 是 CI 基础设施级别的依赖（应预装在 runner 镜像中），还是应作为 `eulerpublisher` 的运行时依赖由 CI pipeline 的 setup 脚本动态安装。
