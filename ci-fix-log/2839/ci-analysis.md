# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

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
- 失败位置: CI Check 阶段，`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 上缺少 `shunit2`（Shell 单元测试框架），导致 Check 阶段脚本 `common_funs.sh` 无法通过 `source` 加载该框架，所有容器验证测试均无法执行（Check Items 表格为空）。Docker 镜像构建 (`make`)、镜像导出和推送均已完成且成功。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 新增了 `Database/postgres/17.6/24.03-lts-sp4/Dockerfile`、`entrypoint.sh` 以及 README/meta.yml 条目。CI 日志中 Docker 构建阶段（`#8 DONE 268.4s`）正常完成，PostgreSQL 17.6 源码编译、安装均成功，镜像已成功构建并推送。失败发生在与 PR 代码无关联的 CI 基础设施层——Check 阶段因 `shunit2` 未安装在 runner 上而无法执行测试。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架。`shunit2` 是通用的 Shell 单元测试工具，应在 CI 节点的系统级安装（如通过 `dnf install shunit2` 或将 `shunit2` 脚本放入 `PATH`），而非在单个 Dockerfile 中处理。这是 CI 基础设施维护问题，Code Fixer 无需对 PR 代码做任何修改。

## 需要进一步确认的点
- 确认同一 CI runner 上其他 PR/镜像的 Check 阶段是否也因 `shunit2` 缺失而失败——如果是，则确认是 runner 环境问题。
- 确认 `shunit2` 在该 CI 环境中预期通过什么方式安装（系统包、pip、或预置脚本），以及为何在本轮运行中缺失。
