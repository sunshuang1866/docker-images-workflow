# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（类别与模式39相似——CI工具依赖缺失）
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行环境缺少 `shunit2` Shell 单元测试框架。`common_funs.sh` 在第 13 行尝试加载 `shunit2`（通过 `. shunit2` 或 `source shunit2`），但该文件/命令不在 `PATH` 中，导致 [Check] 阶段在开始执行任何容器测试之前即宣告失败。

### 日志中的其他信息说明
- Docker 镜像构建（`#7` ~ `#10`）和推送（`#11`）均成功完成，日志中可见 `[Build] finished`、`[Push] finished` 以及 `#11 DONE 41.9s`。
- "Error lines" 区域中大量 `go/src/.../errors.go` 等文件路径实际上是 Dockerfile 中 `find ... -exec touch` 命令的 stdout 输出（文件名包含 "error" 被日志解析器误采集为错误行），并非真正的构建错误。
- aarch64 构建节点上所有 Docker 构建步骤均正常退出，无一报错。

### 与 PR 变更的关联
**与 PR 变更无关。**
- PR 变更内容为：新增 Go 1.25.6 on openEuler 24.03-LTS-SP4 的 Dockerfile、更新 `README.md`（新增表格行）、更新 `image-info.yml`（新增 tags 条目）、更新 `meta.yml`（新增版本路径）。这些变更均为声明式配置，不影响 CI 测试框架的运行时依赖。
- Docker 镜像本身的构建和推送在 aarch64 节点上均成功。失败发生在构建完成后的 CI [Check] 阶段，是 `eulerpublisher` 工具链中 Shell 测试脚本的运行时依赖（`shunit2`）缺失导致的，属于 CI 环境/基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
此次失败为 `infra-error`——CI 运行环境中 `shunit2` Shell 测试框架未安装或不在可搜索路径中。**不需要修改任何 PR 中的代码文件（Dockerfile、README.md、image-info.yml、meta.yml）。** 修复应由 CI 基础设施管理员在构建节点上安装 `shunit2` 包（如 `yum install shunit2` 或确保 `/usr/share/shunit2/shunit2` 可被脚本 source），然后重新触发构建。

### 方向 2（置信度: 低）
如果 `shunit2` 在其他同类镜像的 [Check] 阶段可以正常工作而仅本镜像失败，则可能是 Go 镜像的测试用例配置中存在特殊路径引用问题。但从日志看，错误发生在 `common_funs.sh:13`（通用测试前置库），而不是具体的 Go 测试脚本中，因此该可能性极低。

## 需要进一步确认的点
- 确认 CI aarch64 构建节点（`ecs-build-docker-aarch64-*`）上是否安装了 `shunit2` 包。
- 确认 `eulerpublisher` 的测试脚本 `common_funs.sh` 期望的 `shunit2` 安装路径（如 `/usr/share/shunit2/shunit2` 或 `/usr/local/bin/shunit2`）。
- 确认同类镜像（如已有的 go 1.25.6-oe2403sp3）在当前 CI 环境中是否也会触发相同的 `shunit2` 缺失错误——如果会，则进一步确认 infra 问题；如果不会，则需要检查是否有特别的 CI 配置差异。
