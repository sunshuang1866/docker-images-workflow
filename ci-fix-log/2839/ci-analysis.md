# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

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
- 失败位置: CI runner 的 eulerpublisher 容器测试脚本 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`，第 13 行
- 失败原因: CI [Check] 阶段的 shell 测试框架依赖 `shunit2`（一个 Shell 单元测试库）在 CI runner 上未安装，导致容器镜像的后构建验证测试无法执行

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了 postgres 17.6 在 openEuler 24.03-lts-sp4 上的 Dockerfile、entrypoint.sh、README 条目和 meta.yml 配置。Docker 镜像构建（包括 `./configure && make -j "$(nproc)" && make install` 全流程）和推送到仓库均已成功完成：
- `#8 DONE 268.4s` — 源码编译安装成功
- `#10 DONE 0.1s` — COPY/RUN 步骤成功
- `#11 DONE 58.0s` — 镜像构建、导出、推送全部成功
- `[Build] finished` / `[Push] finished` — 日志明确标记构建和推送完成

失败仅发生在构建完成之后的 [Check] 验证阶段，因 CI runner 缺少 `shunit2` 测试库导致测试脚本无法运行。此问题与镜像内容的正确性无关。

## 修复方向

### 方向 1（置信度: 高）
**CI 基础设施修复，Code Fixer 无需处理此 PR。** 需要在 CI runner 的测试环境中安装 `shunit2` Shell 测试框架。具体来说，`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh` 在第 13 行尝试 source/引用 `shunit2`，但该文件在当前 CI runner 上不存在。这是 CI 运维层面的问题，与 PR 的 Dockerfile、entrypoint.sh 等代码变更完全无关。

## 需要进一步确认的点
- 此 `shunit2` 缺失问题是仅影响此次构建的某个特定 runner，还是多个 runner 均缺少该依赖——这需要查看该 PR 的 aarch64 构建 job 日志及其他同类型 PR 的 CI 结果来确认
- `shunit2` 在 CI 测试环境中的预期安装路径是什么（当前 `common_funs.sh` 引用方式是否有误）

## 修复验证要求
无需验证——此为 infra-error，不涉及代码修复。
