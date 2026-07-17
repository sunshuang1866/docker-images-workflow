# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2缺失
- 新模式症状关键词: shunit2: No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-09 09:40:24,013 - INFO - [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 测试框架内部文件，非 PR 变更内容）
- 失败原因: CI 流水线的 `[Check]` 阶段运行时，`eulerpublisher` 工具的测试框架 `common_funs.sh`（第 13 行）尝试 source `shunit2`，但该 Shell 单元测试库未安装或不在 `PATH` 中，导致整个 Check 阶段无法执行任何测试用例即告失败。Check 结果表为空，说明所有测试项均未实际运行。

### 与 PR 变更的关联
**本次失败与 PR 代码变更无关。** 证据如下：
1. Docker 镜像构建阶段（`#8`）全部成功完成（268.4s），`./configure && make -j "$(nproc)" && make install` 均正常退出，所有 make install 子目标无错误。
2. Docker 镜像推送阶段（`[Push] finished`）成功完成，manifest 已推送至 registry。
3. 唯一的错误发生在 CI 工具自身的 `[Check]` 阶段——测试框架启动时即因缺少 `shunit2` 而崩溃，早于任何针对该镜像的测试用例执行。

PR 仅新增了 Dockerfile、entrypoint.sh、README.md 更新和 meta.yml 条目，这些变更均不涉及 CI 基础设施配置。

## 修复方向

### 方向 1（置信度: 高）
**CI 基础设施修复**：在 CI runner 的执行环境中安装 `shunit2` Shell 单元测试库。该库应由 CI 平台管理员或 Docker runner 镜像维护者提供，而非通过本次 PR 修复。Code Fixer **无需处理**此问题。

### 方向 2（置信度: 中）
若 `shunit2` 仅在该特定 runner 上缺失（而非所有 runner），可能是 runner 环境不一致导致。可尝试重新触发 CI 构建，观察是否在其他 runner 上通过 Check 阶段。

### 旁注（非修复方向）
日志中出现的两个 Docker BuildKit 警告：
```
LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 26)
LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 30)
```
对应 Dockerfile 中的 `ENV PGDATA /var/lib/pgsql/data`（第 26 行附近）和 `ENV PATH ${PATH}:/usr/local/pgsql/bin`（第 30 行附近）使用了旧式 `ENV key value` 格式。这是警告而非错误，不导致构建失败，但建议后续改为 `ENV key=value` 格式以符合 BuildKit 最佳实践。

## 需要进一步确认的点
- 确认 `shunit2` 在该 CI runner 上是否应默认预装。若其他 PR（如其他 postgres 版本的同类提交）的同阶段 Check 正常通过，则可能是本次调度到的 runner 环境有差异，重新触发即可。
- 确认 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh` 中 `shunit2` 的 source 路径是否为相对路径依赖问题（如依赖 `PATH` 或特定工作目录）。
