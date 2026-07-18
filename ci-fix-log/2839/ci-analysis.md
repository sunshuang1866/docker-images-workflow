# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: No such file or directory, common_funs.sh, Check test failed, eulerpublisher

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
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `shunit2`（Shell 单元测试框架）未安装在 CI runner 上，`common_funs.sh` 第 13 行尝试 `source` 或引用 `shunit2` 时找不到该文件/命令。导致 eulerpublisher 的 `[Check]` 阶段无法执行容器功能验证测试（Check Items 表格为空），触发 CRITICAL 报错。

### 与 PR 变更的关联
**此失败与 PR 代码变更无关。** 证据如下：

1. Docker 镜像构建完全成功（`#8 DONE 268.4s`，PostgreSQL 编译、安装全部通过；`#10 DONE 0.1s`；`#11 DONE 58.0s` 导出并推送至 registry）
2. `[Build]` 和 `[Push]` 阶段均正常完成（日志输出 `[Build] finished`、`[Push] finished`）
3. 失败发生在 CI 基础设施层：`eulerpublisher` 的 `[Check]` 阶段调用 `common_funs.sh` 时，因 CI runner 缺少 `shunit2` 框架而直接崩溃，**从未实际执行任何容器功能测试**
4. 日志中仅有的两个 BuildKit 警告（`LegacyKeyValueFormat`，第 26 行和第 30 行的 `ENV` 格式）为非致命性建议，不影响构建结果

PR 新增的 3 个文件（Dockerfile、entrypoint.sh）和 2 个修改文件（README.md、meta.yml）均与 CI runner 上 `shunit2` 缺失无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 测试框架。`shunit2` 是标准的 Shell 单元测试库，可通过以下方式安装：
- **RPM 包**：检查 openEuler 仓库是否提供 `shunit2` RPM 包（部分发行版包名为 `shunit2`）
- **手动部署**：从 https://github.com/kward/shunit2 克隆或下载 `shunit2` 脚本，放置到 `/usr/local/etc/eulerpublisher/tests/container/app/../common/` 或 CI 脚本预期的路径下

此修复属于 CI 基础设施运维操作，**无需修改 PR 中的任何代码文件**。

## 需要进一步确认的点
1. 其他同一 CI runner 上近期执行的 postgres 镜像构建（如已有的 `17.6-oe2403sp2`、`17.5-oe2403sp1` 等）的 `[Check]` 阶段是否也出现相同错误？若均出现，则确认是 runner 环境问题；若仅本次失败，需进一步排查 runner 环境变更时间线。
2. `common_funs.sh` 中 `shunit2` 的预期安装路径是什么？确认 CI runner 配制脚本是否遗漏了 `shunit2` 的部署步骤。
