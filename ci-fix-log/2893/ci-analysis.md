# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架依赖缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 主机 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI runner 上缺少 `shunit2` shell 测试框架依赖，测试脚本 `common_funs.sh` 第 13 行尝试 `. shunit2` 加载该库时失败，导致 [Check] 阶段直接报错退出，容器启动测试未能执行。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 构建阶段完全成功：
- 所有 422 个编译目标（libisc、libdns、libns、named 等）均成功编译和链接
- `meson install` 将所有二进制安装至 `/usr/bin`、`/usr/sbin`、`/usr/lib64` 等路径
- Docker 镜像构建（6/6 步骤）和推送（aarch64）均成功完成

失败发生在 eulerpublisher 流程的 [Check] 测试阶段，根本原因是 CI runner 环境中缺失 `shunit2` 测试库，而非容器镜像本身的任何问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 的 eulerpublisher 测试环境中安装 `shunit2` shell 单元测试框架（通常为 `shunit2` RPM/DEB 包或源码部署至 `/usr/local/etc/eulerpublisher/tests/container/common/` 路径），使测试脚本 `common_funs.sh` 能正常加载该依赖，恢复 [Check] 阶段的容器启动测试能力。

## 需要进一步确认的点
1. 确认 `bind9:9.21.23-oe2403sp4` 在 amd64 架构上的 CI job 是否也存在同样的 `shunit2` 缺失问题（本次日志仅包含 aarch64 job）。
2. 确认 CI runner 测试环境（eulerpublisher）中 `shunit2` 的预期安装路径和版本要求。

## 修复验证要求
无需 Code Fixer 处理。此问题属于 CI 基础设施层面，需由 CI 运维人员在 runner 环境中安装 `shunit2`。若安装后 [Check] 测试仍然失败，需重新获取完整日志以判断是否存在容器镜像自身的运行时问题。
