# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失shunit2
- 新模式症状关键词: shunit2: No such file or directory, common_funs.sh, eulerpublisher, Check test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 执行引擎 `eulerpublisher` 的容器检查阶段（`[Check]`）依赖 Shell 测试框架 `shunit2`，但该工具未安装在 CI Runner 上，导致检查脚本 `common_funs.sh` 在 `source shunit2`（第 13 行）时报错，所有检查项均无法执行（Check Items 表格为空）。

### 与 PR 变更的关联
**此失败与 PR 代码变更无关。**PR 仅新增了 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和 entrypoint.sh（共 3 个新文件 + 1 个 meta.yml 条目 + 1 个 README 更新）。Docker 镜像构建阶段（`[Build]`）完全成功——PostgreSQL 17.6 从源码编译、安装、`COPY entrypoint.sh`、镜像导出及推送均无误（`#8 DONE 268.4s`，`[Build] finished`，`[Push] finished`）。失败仅发生在镜像构建完成后的 `[Check]` 测试阶段，原因是 CI 基础设施（`eulerpublisher` 测试框架）缺少 `shunit2` 依赖。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 上安装 `shunit2` Shell 测试框架（如 `dnf install shunit2` 或将其部署到 eulerpublisher 的测试依赖路径中），确保 CI 的 `[Check]` 阶段能正常加载并执行容器功能测试脚本。此修复属于 CI 基础设施配置变更，**Code Fixer 无需修改任何仓库代码**。

## 需要进一步确认的点
- 确认 `shunit2` 在 openEuler 24.03-LTS-SP4 上的包名（可能是 `shunit2` 或 `shunit`），或确认 eulerpublisher 期望 `shunit2` 的安装路径。
- 确认该 CI Runner 节点是否遗漏了 `shunit2` 的预装步骤（对比其他正常运行的同类 Runner 的环境），以排除个别节点配置漂移的问题。
