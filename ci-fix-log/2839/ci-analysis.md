# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-09 09:40:24,013 - INFO - [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（eulerpublisher 容器检查脚本）
- 失败原因: CI 测试框架 `eulerpublisher` 在执行 `[Check]` 阶段时，`common_funs.sh` 尝试 source `shunit2`（一个 Shell 单元测试框架），但该库未安装在 CI runner 上，导致检查脚本直接崩溃，测试表（Check Items / Description / Check Result）完全为空——零个测试用例被执行。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像的构建和推送阶段均已成功完成（日志中可见 `[Build] finished`、`[Push] finished`，Docker build 阶段 `#8 DONE 268.4s` 正常结束，镜像已推送到 registry）。失败仅发生在 CI 管道的 `[Check]`（运行时验证）阶段，且根因是 CI runner 缺少 `shunit2` 测试框架，属于 CI 基础设施问题，非 PR 代码改动导致。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 或 eulerpublisher 测试环境中安装 `shunit2`。`shunit2` 是一个标准的 Shell 单元测试框架，需确保 `common_funs.sh` 中引用的路径（或通过 `PATH` 可搜索到的位置）存在 `shunit2` 的可执行文件/库文件。

### 方向 2（置信度: 低）
若 `shunit2` 在 CI runner 上实际已安装但路径未正确配置，则需修正 `common_funs.sh` 中 `shunit2` 的 source 路径，或调整 runner 的环境变量确保其可被发现。

## 需要进一步确认的点

1. **该 CI runner 上同一流水线中其他镜像（如 `postgres:17.6-oe2403sp2`）的 `[Check]` 阶段是否也因相同原因失败？** —— 如果其他 postgres 镜像的 check 也失败，则确认是 CI runner 全局缺少 `shunit2`；如果只有 SP4 变体失败，则可能涉及 check 阶段的配置差异。

2. **`entrypoint.sh` 运行时正确性无法验证**：由于 `[Check]` 阶段零个测试用例被执行，容器的启动和运行时行为（如 `gosu` 权限切换、`initdb` 初始化、网络监听等）未经测试验证。需在修复 CI 测试环境后重新触发构建，确认容器实际运行正常。

3. **Docker BuildKit 警告**：日志中出现 2 个 `LegacyKeyValueFormat` 警告（Dockerfile 第 26、30 行，`ENV PGDATA /var/lib/pgsql/data` 和 `ENV PATH ${PATH}:/usr/local/pgsql/bin` 使用了旧式 `ENV key value` 格式而非 `ENV key=value`）。虽不导致构建失败，但建议修复以消除警告。

4. **aarch64 架构构建结果未知**：当前日志仅包含 x86_64 架构的构建输出，arm64 架构的构建是否成功需从其专属 job 日志确认。
