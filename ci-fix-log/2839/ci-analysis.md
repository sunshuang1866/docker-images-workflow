# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39（CI工具依赖缺失）
- 新模式标题: （不适用，匹配已有模式）
- 新模式症状关键词: （不适用）

## 根因分析

### 直接错误
```
[Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 测试框架内部脚本）
- 失败原因: CI 流水线 [Check] 阶段的 runner 环境中未安装 `shunit2`（Shell 单元测试框架），导致测试脚本无法执行镜像健康检查测试。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 和 entrypoint.sh 均未引用或依赖 `shunit2`。Docker 镜像构建（`[Build]`）和推送（`[Push]`）阶段均已成功完成：
- `#8 DONE 268.4s` — PostgreSQL 从源码编译安装成功，所有二进制文件均已安装到 `/usr/local/pgsql/`
- `#11 DONE 58.0s` — 镜像已成功推送到 `docker.io/****test/postgres:17.6-oe2403sp4-x86_64`
- 失败仅发生在构建和推送完成后的 `[Check]` 阶段，是 CI runner 环境缺少测试工具导致的基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架。`shunit2` 是标准的 Shell 单元测试框架，可通过以下方式之一安装：
- 使用系统包管理器安装（如 `dnf install shunit2`）
- 手动将 `shunit2` 脚本部署到 `/usr/local/etc/eulerpublisher/tests/container/common/` 路径
- 在 CI 测试脚本中将 `shunit2` 安装步骤加入前置准备阶段

Code Fixer Agent 无需对 PR 代码做任何修改。

## 需要进一步确认的点
1. CI runner 环境中 `shunit2` 是否需要通过 `dnf` 安装，还是应作为 eulerpublisher 测试框架的预置文件部署；
2. 同类镜像（如 postgres/17.6/24.03-lts-sp2）的 [Check] 阶段是否使用同一 runner 并同样缺失 `shunit2`，以排除 runner 差异化配置问题；
3. 该 runner 是 x86_64 专属还是共享架构 runner，以及 aarch64 runner 是否也需要 `shunit2`。

## 修复验证要求
（不适用，无需修改 PR 代码）
