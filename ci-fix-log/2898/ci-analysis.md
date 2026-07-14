# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 测试阶段（`common_funs.sh:13`）
- 失败原因: CI 测试框架 `eulerpublisher` 在执行容器镜像验证测试时，试图加载或执行 `shunit2`（Shell 单元测试框架），但该工具在 CI runner 环境中未安装或不在 PATH 中，导致 [Check] 阶段失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** Docker 镜像构建（步骤 #7–#11）全部成功完成，镜像已成功推送到 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64`。失败发生在构建之后的 CI [Check] 测试阶段，原因是 CI runner 上缺少 `shunit2` 测试框架。PR 新增的 Dockerfile、README.md、image-info.yml、meta.yml 修改均不涉及 CI 基础设施配置，不会导致 `shunit2` 缺失。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 环境中安装 `shunit2`（Shell 单元测试框架）。在 openEuler 上可通过包管理器安装（如 `dnf install shunit2`），或在 CI 初始化脚本中将 `shunit2` 二进制/脚本部署到 `/usr/local/bin/` 或 CI 测试脚本可搜索到的路径中。

### 方向 2（置信度: 低）
如果 `shunit2` 在 SP4 的 yum 仓库中不可用（包名不同或未收录），则需要在 CI 测试环境的初始化阶段从 GitHub（`https://github.com/kward/shunit2`）手动下载 `shunit2` 脚本并放入 PATH，作为 CI 基础设施的前置依赖安装步骤。

## 需要进一步确认的点
1. `shunit2` 在 `openeuler:24.03-lts-sp4` 基础镜像或 CI runner 系统上是否可通过 `dnf install shunit2` 安装。
2. 同一 CI runner 上其他 OS 版本（如 SP3）的 [Check] 测试是否正常通过——以确认 `shunit2` 缺失是 SP4 专属问题还是全局 CI 环境退化。
3. CI runner 的测试环境初始化脚本（`common_funs.sh` 的上层调用方）是否遗漏了对 `shunit2` 依赖的安装/检查步骤。
4. 是否有 x86_64（amd64）架构的构建日志可供对比——当前仅提供了 aarch64 日志，无法判断另一架构是否也受同一问题影响。
