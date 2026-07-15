# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式39 (CI工具依赖缺失)
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI Runner 上的 eulerpublisher 测试框架文件）
- 失败原因: CI `[Check]` 阶段中，eulerpublisher 的容器校验脚本 `common_funs.sh` 在第 13 行引用了 Shell 单元测试框架 `shunit2`，但该工具未安装在当前 CI Runner 节点上，导致校验步骤直接报错退出。

### 与 PR 变更的关联
**与 PR 无关。** Docker 镜像构建和推送均完全成功：

1. `#7 DONE 67.8s` — Go 源码包下载解压成功
2. `#8 DONE 40.5s` — `find` / `touch` / `ln` 文件操作成功
3. `#9 DONE 1.5s` — GOPATH 目录创建、编译工具卸载成功
4. `#11 exporting to image` — 镜像导出并推送到 registry 成功（`#11 DONE 41.9s`）
5. `[Build] finished` 和 `[Push] finished` 均在日志中确认成功

失败发生在构建/推送完成后的 `[Check]` 阶段，原因是 CI Runner 上缺少 `shunit2` 依赖，属于 CI 基础设施问题。PR 仅新增了一个标准的 Go 1.25.6 Dockerfile（模式与已有的 `24.03-lts-sp3` 版本完全一致），未引入任何可能导致 Check 阶段失败的代码变更。

## 修复方向

### 方向 1（置信度: 中）
在 CI 的 aarch64 Runner 节点上安装 `shunit2`（Shell 单元测试框架）。eulerpublisher 的容器镜像 Check 测试依赖此工具，当前节点缺失导致所有镜像的 Check 阶段失败。该修复应由 CI 基础设施维护者操作，Code Fixer 无需处理。

### 方向 2（置信度: 低）
如果 `shunit2` 是 eulerpublisher 自身应携带的依赖，则可能是 eulerpublisher 包在 aarch64 架构上的安装/分发不完整，需检查 eulerpublisher 的打包和安装流程。

## 需要进一步确认的点

1. 在同一 CI 环境中，其他 aarch64 镜像（如 `24.03-lts-sp3` 的 Go 镜像）的 Check 阶段是否也失败？若同样失败，则证明是 Runner 节点缺少 `shunit2` 的全局性问题。
2. `shunit2` 在 `common_funs.sh` 第 13 行具体是如何被引用的（source / command / function call）？这可以确定是需要系统级安装还是项目内自带。
3. 是否存在 x86_64 架构的 Check 日志？若 x86_64 的 Check 通过而 aarch64 失败，则进一步证明是特定 Runner 节点的环境差异。

## 修复验证要求

本次失败为 infra-error，不涉及代码修复。如需修复 CI 基础设施，验证方式为：在修复后重新触发 aarch64 Runner 上的 `[Check]` 阶段，确认 `shunit2` 可被正常加载且容器校验通过。
