# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check, test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
```

### 根因定位
- 失败位置: CI Runner 的 eulerpublisher 工具链（`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh` 第 13 行）
- 失败原因: CI Runner 环境中未安装 `shunit2`（Shell 单元测试框架），导致 [Check] 阶段的测试脚本 `common_funs.sh` 无法执行。Docker 镜像构建（`make && make install`）和推送（push）均已完成成功。

### 与 PR 变更的关联
本次 PR 变更与 CI 失败**无关联**。PR 仅新增了 PostgreSQL 17.6 on openEuler 24.03-LTS-SP4 的 Dockerfile、entrypoint.sh 及更新 README.md 和 meta.yml，所有构建步骤（configure → make → make install → Docker 镜像构建 → 推送）均在日志中明确显示成功完成（`#8 DONE 268.4s`、`[Build] finished`、`[Push] finished`）。失败发生在构建完成后的 CI [Check] 阶段，原因是 Runner 环境缺少 `shunit2` 测试框架，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 构建环境中安装 `shunit2` 测试框架。这是一个 Shell 单元测试库，需确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 第 13 行 `source` 或调用的 `shunit2` 路径可用。可在 CI Runner 初始化阶段通过包管理器安装（如 `dnf install shunit2` 或从 GitHub 下载 shunit2 脚本到预期路径）。

## 需要进一步确认的点
- 确认 `shunit2` 在 openEuler 24.03-LTS-SP4 系统上的包名和安装方式（可能是 `shunit2` 包，也可能需要从 `https://github.com/kward/shunit2` 手动部署）
- 确认 CI Runner 上 `common_funs.sh` 脚本期望 `shunit2` 的具体加载路径（是 `/usr/bin/shunit2`、`/usr/share/shunit2/shunit2` 还是其他路径）
- 确认这是否是 Runner 环境配置变更导致的偶发问题，还是 CI 环境模板中遗漏了 `shunit2` 的预先安装步骤
- 如果 Docker 构建日志中的 2 个 LegacyKeyValueFormat 警告需要消除（ENV 格式），可在后续 PR 中处理，但这不是本次失败的原因

## 修复验证要求
不适用（本次失败为 `infra-error`，与 PR 代码变更无关，无需 Code Fixer 修改 PR 内容）。
