# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39（CI工具依赖缺失）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 的 [Check] 阶段调用了 `common_funs.sh` 测试脚本，该脚本尝试加载 `shunit2`（Bash 单元测试框架），但 `shunit2` 工具未安装在 CI runner 上或无对应的 shell 可执行路径，导致测试框架无法初始化，[Check] 阶段失败。

关键事实：
1. Docker 镜像构建成功 —— `#11` 步骤显示镜像已成功导出并推送至 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64`
2. `[Build] finished` 和 `[Push] finished` 均成功
3. 失败仅发生在 `[Check]` 阶段，即镜像构建完成后的容器运行验证步骤

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及对应的 README/meta 元数据条目。Docker 构建本身已完全成功（所有 5 个构建阶段 DONE，镜像成功推送到 registry）。`shunit2: No such file or directory` 是 CI runner 侧测试框架依赖缺失，属于基础设施问题，与 PR 代码变更无任何关联。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施问题，Code Fixer 无需对 PR 代码做任何修改。应由 CI 运维人员在 `ecs-build-docker-aarch64-01-sp` runner 上安装 `shunit2` 测试框架（例如通过 `dnf install shunit2` 或从源码安装），确保 `shunit2` 可执行文件在 PATH 中。安装后重新触发 CI 即可通过。

### 方向 2（置信度: 低）
如果确认 `shunit2` 已在 runner 上正确安装，则可能是 CI 测试脚本 `common_funs.sh` 的 `PATH` 配置问题或 `shunit2` 安装路径不在脚本预期位置。需检查 runner 上 `shunit2` 的实际安装路径以及 `common_funs.sh` 第 13 行对 `shunit2` 的引用方式。

## 需要进一步确认的点
1. 确认 CI runner（`ecs-build-docker-aarch64-01-sp`）上 `shunit2` 是否已安装：`which shunit2` 或 `rpm -qa | grep shunit2`
2. 确认 `common_funs.sh` 第 13 行具体如何引用 `shunit2`（source / 直接执行 / 由上层脚本调用），判断是否需要调整 PATH 或改为使用绝对路径
3. 查看同批次其他 PR（如同一 SP4 版本的其他镜像新增）是否也出现相同的 `shunit2` 缺失错误，以确认是否为单个 runner 的个案问题还是所有 SP4 runner 的通用问题

## 修复验证要求
由于失败类型为 `infra-error`，Code Fixer 无需对 PR 代码进行任何修改。只需确认 CI runner 侧 `shunit2` 依赖安装完成后，重新触发 CI 流水线即可验证。
