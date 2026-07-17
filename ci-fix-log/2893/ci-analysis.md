# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: `shunit2: file not found`, `common_funs.sh`, `[Check] test failed`

## 根因分析

### 直接错误
```
2026-07-10 09:23:59,481 - INFO - [Build] finished
2026-07-10 09:23:59,481 - INFO - [Push] finished
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试编排层（`eulerpublisher` 工具链）在执行 `[Check]` 阶段时，`common_funs.sh` 脚本第 13 行尝试通过 `. shunit2` 加载 `shunit2` shell 测试框架，但该框架未安装或不在预期的搜索路径中，导致测试阶段崩溃。Docker 镜像构建和推送均已完成且成功。

### 与 PR 变更的关联
本次 PR 变更（新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、named.conf、及元数据文件）**与 CI 失败无关**。日志显示 Docker 镜像构建（`meson compile` 422/422 目标全部完成、`meson install` 成功）和推送（`[Push] finished`）均正常完成，且 `#13 DONE 36.0s` 确认镜像层导出和 manifest 推送均无错误。失败仅发生在 `eulerpublisher` 工具的后处理/测试阶段，属于 CI 基础设施层面的缺陷。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 上安装 `shunit2` shell 测试框架（如在 openEuler 上通过 `dnf install shunit2`），或确保 `common_funs.sh` 脚本中引用的 `shunit2` 路径与实际安装位置一致。此修复与 PR 代码无关，需要 CI 运维团队介入。

### 方向 2（置信度: 低）
若该 CI runner（aarch64 节点 `ecs-build-docker-aarch64-01-sp` 或类似环境）确实不具备安装 `shunit2` 的条件，可考虑跳过 `[Check]` 阶段，或为 `bind9` 镜像配置专门的最小化测试脚本替代 `shunit2`。

## 需要进一步确认的点
1. 确认 CI aarch64 runner 上是否安装了 `shunit2` 包，以及安装的路径是否与 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13` 中 `. shunit2` 的搜索路径一致。
2. 确认同一 PR 的 x86-64 架构构建 job 是否也存在相同的 `shunit2` 缺失问题（若 x86-64 job 的测试也失败，则问题更可能是通用的 runner 环境缺陷而非架构特有问题）。
3. 确认 `eulerpublisher` 测试框架对 `shunit2` 的依赖是否为新增引入（近期 CI 工具链变更可能导致此前未暴露的依赖缺失）。

## 修复验证要求
无。本失败属于 infra-error，不需要 code-fixer 修改任何作业代码。若需验证，由 CI 运维团队在 runner 上执行 `which shunit2` 或 `rpm -q shunit2` 确认包安装状态即可。
