# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Check测试依赖缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check, test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段在执行容器镜像测试时，`common_funs.sh` 脚本第 13 行尝试引用 `shunit2`（一个 Shell 单元测试框架），但该依赖在 CI runner（宿主机）上未安装，导致测试脚本无法执行，[Check] 阶段直接失败。

### 与 PR 变更的关联
**此失败与 PR 变更无关**。证据如下：
1. Docker 镜像构建完全成功（`#7 DONE 67.8s` → `#10 DONE 0.0s`），日志明确输出 `[Build] finished` 和 `[Push] finished`，镜像已成功推送到 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64`。
2. 失败仅发生在 CI 流水线的 [Check] 阶段，且直接原因是 CI 宿主机的测试框架依赖 `shunit2` 缺失，而非镜像内容问题。
3. PR 变更仅涉及新增 Dockerfile（下载 Go 二进制、设置环境变量）、README.md 表格条目、image-info.yml 标签记录和 meta.yml 路径映射，这些变更均不会影响 CI runner 上 `shunit2` 的安装状态。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境（`ecs-build-docker-aarch64-01-sp` 或相应的 openEuler 24.03-lts-sp4 构建节点）上安装 `shunit2` 包。shUnit2 是一个 Shell 单元测试框架，通常可通过以下方式安装：
- openEuler/DNF 仓库中的 `shunit2` 或 `shunit2-standalone` 包
- 或从 GitHub 下载 `shunit2` 脚本放置到 `PATH` 中

该问题属于 CI 基础设施配置缺失，Code Fixer 无需对 PR 中的 Dockerfile 或元数据文件做任何修改。

### 方向 2（置信度: 低 — 供排除用）
若 `shunit2` 确实已安装在 CI runner 上但仍报 `No such file or directory`，可能是 `common_funs.sh` 中 `shunit2` 的引用路径不正确（如相对路径 vs 绝对路径，或 `source` 时未在 `PATH` 中）。需检查 `common_funs.sh:13` 的具体引用方式。

## 需要进一步确认的点
1. **CI 节点确认**：该失败发生在 aarch64 构建节点上。需确认同一 `24.03-lts-sp4` 的 x86_64 节点是否也存在相同的 `shunit2` 缺失问题（当前日志仅包含 aarch64 架构的构建输出，未提供 x86_64 日志）。
2. **shunit2 历史安装记录**：确认该 CI 节点是新建节点（首次配置不完整）还是已有节点（shunit2 被意外移除）。对比 `24.03-lts-sp3` 节点的 [Check] 阶段是否正常运行，以判断问题是架构/版本特定的还是全局性的。
3. **common_funs.sh 版本**：确认 `common_funs.sh:13` 对 shunit2 的引用方式（`source shunit2` / `. shunit2` / 硬编码路径），以确定正确的修复方式。

## 修复验证要求
无需修复验证——本失败为 CI 基础设施问题，PR 代码变更本身无需修改。若运维侧确认需要在 CI 节点上安装 `shunit2`，安装后重新触发 CI 即可验证。
