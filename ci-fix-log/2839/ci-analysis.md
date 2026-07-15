# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试环境缺少shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段 — `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 节点的测试环境中缺少 `shunit2`（shell 单元测试框架），导致 Check 阶段的容器测试脚本无法执行

### 与 PR 变更的关联
- **与 PR 无关**。Docker 镜像构建（`#8 DONE 268.4s`）和推送（`#11 DONE 58.0s`）均已完成并成功，所有 `make` / `make install` 步骤正常退出，镜像已成功推送到目标 registry。
- 日志中出现的 2 条 `LegacyKeyValueFormat` 警告仅为 Docker BuildKit 的风格提示，不影响构建结果。
- 失败仅发生在 `[Check]` 测试阶段，因为运行测试的 CI 节点缺少 `shunit2` 命令行工具，无法执行容器验证脚本。这是一个 CI 基础设施缺陷，与 PR 新增的 Dockerfile / entrypoint.sh / meta.yml 无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI 节点的测试环境（`eulerpublisher` 测试框架所在路径）中安装 `shunit2`。`shunit2` 是 Shell 的 xUnit 测试框架，通常通过以下方式之一安装：
- 从系统包管理器安装（如 `dnf install shunit2`）
- 或将该 shell 脚本库部署到 `common_funs.sh` 第 13 行 `source` 或 `.` 指令所能找到的路径中

### 方向 2（可选）
如果短期无法修复 CI 节点环境，可临时跳过该镜像的 Check 阶段，先合并 PR 并通过手工验证确认镜像功能正常。但此方向仅适用于 `shunit2` 安装确有困难的场景。

## 需要进一步确认的点
1. 同类型的其他 PostgreSQL 镜像（如 `17.6/24.03-lts-sp2`）在 CI 构建时是否也触发了 Check 阶段？如果未触发，说明新增 SP4 镜像触发了之前未覆盖的测试路径，需确认 CI 调度配置。
2. CI 节点上 `shunit2` 是否曾经安装过（例如被清理或升级导致缺失），还是该节点从一开始就未配置此工具。
3. 是否存在 `shunit2` 的替代测试脚本路径（如 `/usr/share/shunit2/shunit2`），`common_funs.sh` 第 13 行的 source 路径是否可配置。

## 修复验证要求
无需验证。本失败为 CI 基础设施问题，不涉及对 Dockerfile、entrypoint.sh 或 meta.yml 的代码修改。
