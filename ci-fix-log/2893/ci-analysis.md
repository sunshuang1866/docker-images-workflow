# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check, test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI Runner 环境 — `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段在执行容器功能测试时，`common_funs.sh` 脚本尝试通过 `source` 加载 `shunit2` 单元测试框架（`. shunit2`），但该框架未安装在 CI runner 环境中，导致 Check 步骤失败。

### 与 PR 变更的关联
**与 PR 变更无关**。本次 PR 仅新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件。证据如下：
- Docker 构建阶段**完全成功**：所有 422 个编译目标通过，`meson install` 完成，镜像导出并推送至 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`。
- 日志中 `[Build] finished` 和 `[Push] finished` 均明确标记成功。
- 失败仅发生在 `[Check]` 阶段——该阶段不属于 Dockerfile 构建逻辑，而是 CI 编排工具 `eulerpublisher` 的容器功能验证步骤，因 runner 缺少 `shunit2` 依赖而崩溃。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境或 `eulerpublisher` 部署中安装 `shunit2` shell 测试框架。`shunit2` 是一个标准的 shell 单元测试库，可通过以下任一方式安装：
- 从 EPEL/系统包管理器安装（如 `yum install shunit2` 或 `apt install shunit2`）
- 从 GitHub 发布页下载 `shunit2` 脚本放置到 CI runner 的 PATH 中

此修复由 CI 基础设施管理员执行，**Code Fixer 无需处理**。

## 需要进一步确认的点
1. 同一 CI runner 上其他镜像的 [Check] 阶段是否也因 `shunit2` 缺失而失败（若普遍存在，说明 runner 镜像模板需更新）。
2. `shunit2` 是否曾经安装在该 runner 上但因近期环境变更被移除。

## 修复验证要求
无。此失败为 infra-error，与 PR 代码变更无关，无需对 Dockerfile 或元数据文件做任何修改。
