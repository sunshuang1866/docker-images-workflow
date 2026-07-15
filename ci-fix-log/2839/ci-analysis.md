# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架依赖缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架（eulerpublisher tests）在 [Check] 阶段尝试执行镜像验证测试时，依赖的 `shunit2`（bash 单元测试框架）未安装在该 CI runner 上，导致 `common_funs.sh` 第 13 行 `source shunit2` 失败，所有检查项无法执行（测试结果表为空）。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh、meta.yml 条目和 README 更新。Docker 构建阶段（`#8 DONE 268.4s`）和镜像推送阶段（`[Push] finished`）均成功完成，失败仅发生在 CI 流水线自身的 Check（镜像验证测试）环节，原因是 CI runner 环境缺少 `shunit2` 测试依赖，与 PR 代码变更无任何关联。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境上安装 `shunit2` 测试框架。该工具通常可通过发行版的包管理器安装（如 `dnf install shunit2`），或从 GitHub releases 下载后放置到 `PATH` 中。`common_funs.sh` 直接 `source shunit2` 而未指定路径，说明预期 `shunit2` 已在 `PATH` 中可用。

### 方向 2（置信度: 低）
若 `shunit2` 是 CI 测试套件自带的 vendored 依赖（应随 eulerpublisher 包一同安装），则问题可能是 eulerpublisher 包版本不完整或安装步骤遗漏了测试依赖文件，需要检查 CI 环境中 eulerpublisher 包的安装完整性。

## 需要进一步确认的点
- 确认同一 CI runner 上其他 PR 的 [Check] 阶段是否也出现 `shunit2: No such file or directory` 错误。若是，则确认为 runner 环境问题（而非本 PR 独有）。
- 确认 CI runner 镜像模板中是否已安装 `shunit2` 包，以及 `common_funs.sh` 期望的 `shunit2` 来源（系统包 vs. vendored）。

## 修复验证要求
无需 code-fixer 介入。此失败为 CI 基础设施问题，需由 CI 运维团队在 runner 环境安装 `shunit2` 后重新触发构建验证。
