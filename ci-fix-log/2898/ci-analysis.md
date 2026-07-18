# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, Check test failed

## 根因分析

### 直接错误

Docker 镜像构建（#1-#11）全部成功完成，包括 Go 1.25.6 源码下载、解压、环境配置和镜像推送。失败仅发生在 CI 的 **[Check] 测试阶段**：

```
2026-07-09 12:32:49,909 - INFO - [Push] finished
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试脚本 `common_funs.sh` 在第 13 行尝试加载（source）`shunit2` shell 单元测试框架，但 `shunit2` 未安装在该 aarch64 CI runner 的 `PATH` 中，导致脚本执行终止。

### 与 PR 变更的关联

**完全无关**。本 PR 的变更仅包含：
1. 新增 `Others/go/1.25.6/24.03-lts-sp4/Dockerfile`（Go 1.25.6 镜像构建文件）
2. 更新 `Others/go/README.md`（文档）
3. 更新 `Others/go/doc/image-info.yml`（元数据）
4. 更新 `Others/go/meta.yml`（镜像版本注册）

Docker 构建和推送阶段均已成功完成（`[Build] finished`、`[Push] finished`），镜像 `openeulertest/go:1.25.6-oe2403sp4-aarch64` 已生成并推送。失败发生在 CI 工具 `eulerpublisher` 的内置容器测试阶段，`shunit2` 是 CI runner 环境依赖，与 PR 的代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在构建该镜像的 aarch64 CI runner 上安装 `shunit2`。`shunit2` 是一个标准的 shell 单元测试框架，可通过以下方式安装：
- `dnf install shunit2`（如果 openEuler 仓库包含该包）
- 或从源码部署到 CI runner 的 `PATH` 中（如 `/usr/local/bin/`）

**注意**：此修复需由 CI 基础设施管理员操作，Code Fixer 无需也无法通过修改 PR 代码解决此问题。

## 需要进一步确认的点

1. 确认 CI runner `ecs-build-docker-aarch64-01-sp`（从日志中 `linux_arm64` 架构推断）上是否确实未安装 `shunit2`
2. 确认其他最近在相同 runner 上通过 Check 测试的 PR（如同类 Go 镜像的 PR）是否安装了 `shunit2`，以排除 `shunit2` 被意外卸载或 PATH 变更的可能性
3. 确认 x86_64 架构的构建 job 是否也遇到同样的 `shunit2` 缺失问题（日志仅提供了 aarch64 的构建和检查结果）
