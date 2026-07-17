# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: `shunit2: file not found`, `common_funs.sh`, `[Check] test failed`

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:161]-INFO: [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
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
- 失败位置: CI 测试框架 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 的 `eulerpublisher` 测试环境中缺少 `shunit2` 单元测试框架（bash shell 测试库），`common_funs.sh` 在第 13 行执行 `source shunit2` 时找不到该文件，导致所有镜像检查项（Check Items 表格）均为空，[Check] 阶段直接失败。

### 与 PR 变更的关联
本次失败与 PR 代码变更**无关**。证据如下：

1. **Docker 构建成功**：日志中 `[Build] finished` 和 `[Push] finished` 均确认镜像构建与推送全部完成，所有 7 个 Docker 构建步骤（#9-#13）均显示 `DONE`。
2. **失败仅发生在 CI 测试框架层**：`shunit2: file not found` 是 CI Runner 自身测试框架（`eulerpublisher` tests）的依赖缺失问题，不涉及镜像内容或 Dockerfile 语法。
3. PR 仅新增了一个标准化的 httpd Dockerfile（编译安装 → 配置 → 入口脚本），无任何特殊或异常构建逻辑。

## 修复方向

### 方向 1（置信度: 中）
在 CI Runner 的构建环境中安装 `shunit2` 测试框架（如通过 `dnf install shunit2` 或从源码部署到 `/usr/local/share/shunit2`），使 `common_funs.sh` 的 `source` 语句能找到 `shunit2`。此修复需由 CI 基础设施管理员操作，Code Fixer 无需处理任何代码。

## 需要进一步确认的点
- 该 CI Runner 节点是仅有 httpd 构建任务失败，还是所有使用同一 Runner 的 PR 均因 `shunit2` 缺失而失败。如果是后者，属于全局 infra 问题，等待 CI 基础设施修复即可。
- `shunit2` 是否曾经存在于该 Runner 上被误删？或者该 Runner 镜像/模板在近期更新时遗漏了该依赖？确认后由 CI 管理员恢复 Runner 环境。
- 其他架构（如 aarch64）的 Check 阶段是否也因同样原因失败？若是，说明所有架构节点的测试环境均缺 `shunit2`。

## 修复验证要求
此失败无需 code-fixer 介入（infra-error）。若后续 CI 环境修复后该 job 仍失败，需获取完整的 Check 阶段日志（含实际测试用例执行结果）重新分析。
