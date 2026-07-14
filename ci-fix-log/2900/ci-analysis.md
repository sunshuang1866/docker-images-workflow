# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架文件缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh

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
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI [Check] 阶段在执行容器测试前，测试脚本 `common_funs.sh` 尝试 `source shunit2`（Shell 单元测试框架），但 `shunit2` 在 CI Runner 的 `PATH` 中不存在，导致测试框架加载失败，所有测试项均未执行（结果表为空）。

### 与 PR 变更的关联
**本次失败与 PR 变更无关。**

- Docker 镜像构建全部 7 个阶段（#9~#13）均成功完成，`Configure` → `Make` → `Make Install` → 配置 → 导出均无错误。
- 构建产物已成功推送到 registry（`sha256:b38237a0854eb058b77e7e857d62923d7166fbe49740c2ce2f0206f7e858ea4b`）。
- 日志明确显示 `[Build] finished` 和 `[Push] finished` 均为 INFO 级别。
- 失败仅发生在后续 `[Check]` 阶段，且根因是 CI Runner 环境缺少 `shunit2` 测试框架文件，与 PR 新增的 Dockerfile、httpd-foreground 脚本及文档变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 节点上安装 `shunit2` 测试框架，确保 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh` 中 `source shunit2` 能从 `PATH` 中找到该脚本。该问题为 CI 基础设施配置缺失，无需修改任何代码。

## 需要进一步确认的点
- 确认同一 CI Runner 上其他镜像（PR）的 [Check] 阶段是否也因同样原因失败（判断是全局基础设施故障还是该 Runner 节点的问题）。
- 确认 `shunit2` 在 Runner 上的预期安装路径，以及是否需要修改 `common_funs.sh` 中的 `source` 路径（如从 `shunit2` 改为绝对路径）。
