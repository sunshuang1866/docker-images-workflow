# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI Runner 的 `[Check]` 阶段（`eulerpublisher/container/app/app.py:173`）
- 失败原因: CI 测试编排脚本 `common_funs.sh` 尝试 source `shunit2` shell 测试框架，但该框架未安装在当前 CI Runner 上，导致容器镜像的运行时检查步骤无法执行

### 与 PR 变更的关联

**与 PR 代码变更无关。** Docker 镜像构建和推送均已成功完成：

- Docker 构建 7 个步骤全部通过（`#10 DONE 41.6s`、`#11 DONE 0.1s`、`#12 DONE 0.0s`、`#13 DONE 0.1s`）
- `[Build] finished` — 构建成功
- `[Push] finished` — 推送成功（`2.4.66-oe2403sp4-x86_64` 已推送至 registry）
- 失败仅发生在构建和推送完成后的 `[Check]` 阶段，因 Runner 环境缺少 `shunit2` 测试框架导致

PR 变更仅新增 httpd 2.4.66 在 openEuler 24.03-lts-sp4 上的 Dockerfile、启动脚本及元数据文件，所有构建步骤在日志中无任何报错。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 环境（或 `eulerpublisher` 容器测试依赖）中安装 `shunit2` shell 测试框架。`shunit2` 是标准的 Shell 单元测试框架，可通过以下方式安装：
- `dnf install shunit2`（部分发行版提供）
- 或从 GitHub 下载并放置在 `PATH` 可访问路径

### 方向 2（置信度: 低）
若 `shunit2` 应为 `eulerpublisher` Python 包内置依赖（如 vendored 在 `tests/` 目录下），则需检查 `eulerpublisher` 包的安装是否完整，是否存在缺失的测试资源文件。

## 需要进一步确认的点

1. 确认 CI Runner 容器镜像是否应预先包含 `shunit2`（检查 Runner 的 Dockerfile 或初始化脚本）
2. 确认同仓库其他 PR 的 `[Check]` 阶段是否也因相同原因失败——若为首次出现，可能是 Runner 环境最近发生了变更
3. 确认 `shunit2` 是否应由 `eulerpublisher` 包自包含（检查 `tests/container/common/` 目录下是否应存在 `shunit2` 文件）

## 修复验证要求

无需代码修复验证。此为 CI 基础设施配置问题，重新安装/配置 `shunit2` 后重跑 CI 即可验证。
