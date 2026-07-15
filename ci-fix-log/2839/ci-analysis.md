# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2: No such file or directory, Check test failed, common_funs.sh

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
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 测试框架层）
- 失败原因: CI 运行环境的 eulerpublisher 测试框架中，`common_funs.sh` 脚本尝试加载 `shunit2` shell 单元测试框架，但该工具在当前 CI runner 上未安装或不可用，导致整个 Check 阶段失败。

### 与 PR 变更的关联
**与 PR 无关。** 此次 PR 新增了 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh 及元数据文件。Docker 镜像构建（`#8 DONE 268.4s`）和推送（`[Push] finished`）均成功完成。失败发生在构建完成后的 CI Check 验证阶段——测试框架 `shunit2` 缺失导致验证脚本无法执行，而非镜像构建或代码本身的问题。

Docker 构建日志中存在两个 BuildKit 警告（`LegacyKeyValueFormat` 针对 Dockerfile 第 26、30 行的 `ENV` 格式），但这些是 Docker 风格建议，不构成构建错误。

## 修复方向

### 方向 1（置信度: 高）
此失败为 CI 基础设施问题，**无需修改 PR 代码**。需由 CI 管理员在 runner 上安装 `shunit2`（Shell Unit Testing Framework），确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 中的 `source shunit2` 能正常加载。安装方式如：`dnf install shunit2` 或从 GitHub 下载并放入 PATH。

## 需要进一步确认的点
- 确认该 CI runner 是否为临时节点（clean environment），如果是永久节点，需检查为何 `shunit2` 被移除/未安装。
- 确认同一 CI 流水线中其他同类镜像（如 PostgreSQL 其他版本）的 Check 阶段是否也出现相同错误，判断是否是系统性基础设施缺失。
