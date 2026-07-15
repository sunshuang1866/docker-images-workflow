# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式（参考模式39：CI工具依赖缺失）
- 新模式标题: shunit2未安装
- 新模式症状关键词: shunit2: file not found, eulerpublisher, check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 环境的 `eulerpublisher` 测试框架中 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段执行容器镜像测试时，`common_funs.sh` 尝试 `source` 加载 `shunit2` 测试框架，但 `shunit2` 未安装或不在 `PATH` 中，导致测试脚本无法运行，[Check] 判定失败。

### 与 PR 变更的关联
**与 PR 无关**。Docker 镜像的 [Build] 和 [Push] 阶段均已成功完成：
- `meson compile` 全部 422/422 编译步骤通过
- `meson install` 正常安装所有二进制文件
- 镜像构建成功导出并推送至 Docker Hub（`9.21.23-oe2403sp4-aarch64`）

PR 新增的 Dockerfile（`Others/bind9/9.21.23/24.03-lts-sp4/Dockerfile`）和配置文件的构建流程本身没有问题。`shunit2` 缺失是 CI runner 环境配置问题，非代码缺陷。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 的测试环境中安装 `shunit2`（shell 单元测试框架）。`eulerpublisher` 容器的 [Check] 阶段依赖 `shunit2` 执行容器启动验证测试，当前 CI 节点缺少此依赖。可在 CI runner 初始化的 yum/dnf 安装步骤中补充 `shunit2` 包。

### 方向 2（置信度: 低）
检查是否仅 aarch64 runner 缺少 `shunit2`，x86_64 runner 可能另有独立问题。当前日志仅展示了 aarch64 构建和 check 过程，可能存在未提供的 x86_64 构建 job 日志。若 x86_64 构建成功但 check 同样因 `shunit2` 缺失失败，则根本原因一致；若 x86_64 有其他构建错误，则需获取对应日志。

## 需要进一步确认的点
1. 确认 CI 的 x86_64 架构构建 job 日志中是否有其他错误（当前仅提供了 aarch64 日志）
2. 确认 CI runner 所在节点是否原本应预装 `shunit2` 但被意外移除/未安装
3. 确认同类镜像（如 `bind9 9.21.23-oe2403sp3`）的 CI [Check] 是否也曾因同样原因失败，以判断是否为近期 CI 环境变更导致
