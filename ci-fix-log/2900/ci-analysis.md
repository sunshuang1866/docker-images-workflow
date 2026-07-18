# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, eulerpublisher, Check test failed, common_funs.sh

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/app.py:173`（Check 阶段调用的 `common_funs.sh` 第 13 行）
- 失败原因: CI 编排工具 `eulerpublisher` 在执行 [Check] 后置验证阶段时，`common_funs.sh` 尝试通过 `.` 命令 source `shunit2` 测试框架，但 `shunit2` 未安装在 CI runner 环境中，导致文件未找到，Check 阶段失败。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 仅新增 httpd 2.4.66 on openEuler 24.03-LTS-SP4 的 Dockerfile、启动脚本及元数据文件。日志明确显示 Docker 镜像的构建和推送阶段均已完成（`[Build] finished` → `[Push] finished`），所有 Docker build 步骤（#10~#13）均返回 `DONE` 且镜像已成功推送到 registry。失败发生在 CI 流水线的后置 [Check] 验证阶段，是 CI runner 环境缺少 `shunit2` 测试框架导致的，并非 PR 代码逻辑错误。

日志中出现的唯一 warning（`LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 5)`）是 Dockerfile Lint 的非致命提醒，与 Check 失败无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架（如通过 dnf/yum 安装 `shunit2` 包或手动部署 shunit2 脚本），确保 `common_funs.sh` 在执行时能找到并 source 该框架。此修复属于 CI 基础设施层面，**Code Fixer 无需处理 PR 中的任何文件**。

## 需要进一步确认的点
- 确认 CI runner 环境中是否曾安装过 `shunit2`，是否为近期环境变更（如 runner 镜像升级）导致该依赖丢失。
- 若其他 PR 的 Check 阶段也出现同类 `shunit2: file not found` 错误，则确认是 CI 系统性问题；若仅本 PR 出现，需排查 runner 调度到的特定节点的环境差异。
