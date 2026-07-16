# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

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
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13（CI 测试基础设施脚本）
- 失败原因: CI runner 的测试环境中缺少 `shunit2` shell 测试框架，导致 eulerpublisher 的 [Check] 阶段无法运行容器验收测试

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 新增的 Dockerfile 构建和镜像推送均成功完成：
- Docker 镜像编译（PostgreSQL 17.6 源码 `make && make install`）成功，`#8 DONE 268.4s`
- 镜像构建（`COPY entrypoint.sh`、`RUN chmod`）成功，`#10 DONE 0.1s`
- 镜像导出与推送成功，`#11 DONE 58.0s`，manifest 已推送到 docker.io

失败发生在 CI 流水线的 `[Check]` 阶段——`eulerpublisher` 工具尝试运行 `common_funs.sh` 测试脚本时，发现 `shunit2` 命令不存在。`shunit2` 是一个 Shell 单元测试框架，是 CI 测试基础设施的依赖，而非 PR 中 Dockerfile 或 entrypoint.sh 应该安装的组件。该问题是 CI runner 环境配置问题，与本次代码变更完全无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 的测试环境中安装 `shunit2`。`shunit2` 是一个独立的 Shell 测试框架（通常为单个 `.sh` 文件），需确保其安装路径在 `common_funs.sh` 的 `PATH` 可搜索范围内，或修改 `common_funs.sh` 中 `shunit2` 的引用为绝对路径。

## 需要进一步确认的点
- 确认其他 PR（历史通过的 postgres 镜像提交）的 Check 阶段是否也曾调用 `shunit2`，以判断这是否是新引入的 CI runner 环境变更导致的问题
- 确认 `shunit2` 在 CI runner 上的预期安装路径（`common_funs.sh` 通过 `shunit2` 裸命令引用，未指定路径，说明期望在 `PATH` 中）

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
无。本次失败为 CI 基础设施问题（infra-error），PR 的 Dockerfile 和 entrypoint.sh 无需修改。
