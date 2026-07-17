# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, Check test failed

## 根因分析

### 直接错误
```
2026-07-09 09:40:24,013 - INFO - [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
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
- 失败位置: CI Runner（非容器内），`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段的测试脚本 `common_funs.sh` 在第 13 行尝试加载 `shunit2`（Shell 单元测试框架），但该框架未安装在 CI Runner 上，导致整个 Check 阶段无法执行便直接崩溃。Docker 镜像构建（Build）和推送（Push）均已成功完成，Check 结果表为空（无任何测试项被执行）。

### 与 PR 变更的关联
**无关**。PR 仅新增了 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh、README.md 条目和 meta.yml 条目。Docker 镜像构建本身已成功完成（`#8 DONE 268.4s`，`#11 DONE 58.0s`），`[Build] finished` 和 `[Push] finished` 均在日志中确认。失败发生在独立的 `[Check]` 阶段，原因是 CI 测试环境缺少 `shunit2` 依赖，属于 CI 基础设施问题，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 上安装 `shunit2` 测试框架。`shunit2` 通常可通过包管理器安装（如 `dnf install shunit2` 或 `apt install shunit2`），或从 GitHub Release 下载后放入 `PATH`。此修复完全不涉及 PR 代码变更，由 CI 运维人员处理。

### 方向 2（置信度: 低）
若 `shunit2` 确实已安装在 Runner 上但路径不对，需检查 `common_funs.sh` 第 13 行中 `shunit2` 的加载路径是否正确（例如是否应通过 `source /path/to/shunit2` 而非直接 `shunit2` 命令加载）。

## 需要进一步确认的点
1. 该 CI Runner 上 `shunit2` 是否已安装？（`which shunit2` 或 `rpm -qa | grep shunit2`）
2. 其他在同一个 CI 环境构建的 PR 是否也同时出现该 Check 失败？（判断是否为 Runner 级别的全局问题）
3. `common_funs.sh` 第 13 行加载 `shunit2` 的具体方式是什么（`source`、`.`、直接执行？），以判断是否为路径配置错误而非真正的缺失。
