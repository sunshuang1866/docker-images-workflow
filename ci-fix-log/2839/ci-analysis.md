# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 上 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 环境中的 `eulerpublisher` 测试框架缺少 `shunit2`（Shell 单元测试工具），导致 `common_funs.sh` 第 13 行尝试加载 `shunit2` 时失败，[Check] 阶段无法执行任何测试。Check 结果表为空（无任何 Check Items 记录），进一步证实测试脚本在 shunit2 加载阶段即崩溃，未进入实际测试逻辑。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 新增的 Dockerfile（PostgreSQL 17.6 on openEuler 24.03-LTS-SP4）构建和推送均已成功完成（`[Build] finished`、`[Push] finished`，镜像 tag `17.6-oe2403sp4-x86_64` 已推送到 registry），Dockerfile 中所有 4 个构建步骤（`#8` 至 `#10`）均以 `DONE` 结束。失败发生在 CI 编排工具 `eulerpublisher` 的 [Check] 阶段，属于 CI 基础设施层面的问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 环境中安装 `shunit2`。`shunit2` 是一个 Shell 单元测试框架，需确保它在 `/usr/local/etc/eulerpublisher/tests/container/app/../common/` 或其 PATH 可访问的路径中可用。检查 `common_funs.sh` 第 13 行加载 `shunit2` 的具体方式（是 `source` / `.` 相对路径还是绝对路径），确认 CI 镜像/环境中是否遗漏了 `shunit2` 包的安装。

**Code Fixer 无需处理此问题**。此失败属于 CI 基础设施配置问题，需要 CI 运维人员修复 Runner 环境，而非修改 PR 代码。

## 需要进一步确认的点
- `shunit2` 是通过系统包管理器（如 `dnf install shunit2`）安装，还是通过特定路径部署的？需确认 CI Runner 镜像中 `shunit2` 的正确安装方式及预期路径。
- 该失败是仅影响本次 PR，还是所有使用同一 CI Runner 的 PR 均受影响？如果是后者，说明 Runner 环境近期发生了变更导致 `shunit2` 丢失。
