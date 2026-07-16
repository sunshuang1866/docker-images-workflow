# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 部分匹配 模式39（CI工具依赖缺失）
- 新模式标题: shunit2缺失
- 新模式症状关键词: shunit2, No such file or directory, check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 构建环境（aarch64 runner）的测试框架依赖 `shunit2` 未安装，导致镜像构建成功后的 [Check] 验证阶段失败。Docker 镜像 `openeulertest/go:1.25.6-oe2403sp4-aarch64` 本身已成功构建并推送。

### 与 PR 变更的关联
**与 PR 无关**。PR 仅新增了一个 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及其元数据（meta.yml、README.md、image-info.yml）。Docker 镜像的所有构建步骤（下载 Go → 解压 → 修复时间戳 → 清理构建工具 → 推送）均已完成且成功。失败发生在 CI 的 [Check] 阶段，`shunit2` 是 eulerpublisher 测试框架的运行时依赖，其缺失属于 CI 基础设施问题，与 PR 的 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
CI runner 环境缺少 `shunit2` shell 测试框架。需在 CI runner（`ecs-build-docker-aarch64-01-sp` 或同类型节点）上安装 `shunit2`（可通过 `dnf install shunit2` 或手动部署脚本安装）。此修复由 CI 基础设施团队执行，不涉及 PR 代码修改。

## 需要进一步确认的点

1. **x86_64 架构构建状态未知**：当前日志仅包含 aarch64 架构的构建过程，PR 声明镜像同时支持 amd64 和 arm64。需要获取 x86_64 runner 的构建日志，确认 amd64 镜像构建是否也成功、是否同样在 [Check] 阶段因 `shunit2` 缺失而失败。
2. 确认 `shunit2` 是未安装还是路径配置错误（如已安装在非标准路径，`common_funs.sh` 的 `source` 路径需调整）。
3. 确认该 CI runner 是否在本次 PR 之前已存在 `shunit2` 缺失的问题（即是否为预存在的环境问题）。
