# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架依赖缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 的 `common_funs.sh` 脚本在第 13 行尝试 `source shunit2`，但 CI runner 环境中未安装/配置 `shunit2`（shell 单元测试框架），导致测试完全无法执行，测试结果表为空。

### 与 PR 变更的关联

**与 PR 变更无关。** 该 PR 新增的 Dockerfile 构建完全成功（所有 7 个 RUN 步骤均通过），镜像已成功构建并推送至容器仓库：
- `[Build] finished` — 构建成功
- `[Push] finished` — 推送成功
- 日志中仅有 1 个 Docker 非致命 warning（`LegacyKeyValueFormat`，第 5 行 ENV 使用旧格式），不影响构建

失败发生在 [Check] 阶段，即 `eulerpublisher` 测试框架对已构建镜像执行容器化测试时，因 CI 环境缺少 `shunit2` 依赖导致测试脚本无法启动。PR 的代码变更不涉及也无法影响 CI 测试框架的依赖配置。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 包。`shunit2` 是 `eulerpublisher` 容器测试框架的运行时依赖，CI 节点上需确保该包可被 `common_funs.sh` 脚本 `source` 到（即位于 `PATH` 中或作为 `eulerpublisher` 的捆绑依赖安装）。

### 方向 2（置信度: 低）
若 `shunit2` 应为 `eulerpublisher` Python 包的一部分（如打包在 `site-packages` 内），则可能是 `eulerpublisher` 版本不完整或安装损坏，需重新安装或升级 CI 环境中的 `eulerpublisher` 包。

## 需要进一步确认的点
1. 确认其他近期 PR 的 CI [Check] 阶段是否也因同样原因失败（若普遍存在，则为 CI 环境全局问题）
2. 确认 CI runner 上 `shunit2` 的预期安装路径和来源（系统包管理器安装？还是 eulerpublisher 自带？）
3. 若该 CI runner 之前可正常运行 httpd 或其他镜像的 Check 测试，需排查近期 CI 环境是否有变更导致 shunit2 被移除
