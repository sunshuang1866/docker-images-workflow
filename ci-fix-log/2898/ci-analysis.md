# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh`:13（CI 测试脚本）
- 失败原因: CI Runner 上未安装 `shunit2`（shell 单元测试框架），导致 [Check] 阶段的容器健康检查测试无法执行

### 与 PR 变更的关联

**与 PR 变更无关。** 该 PR 新增了一个 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，以及对应的 README、image-info.yml、meta.yml 更新。Docker 镜像构建阶段（步骤 #7 至 #11）全部成功完成，镜像已成功构建并推送至 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64`。日志中明确显示 `[Build] finished` 和 `[Push] finished` 均成功，失败仅发生在 CI 内置的 [Check] 测试阶段——该阶段调用 `shunit2` 对已构建的容器进行运行状态验证，但 CI Runner 缺少 `shunit2` 依赖。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 镜像/环境中安装 `shunit2` 包。`shunit2` 是一个标准的 shell 单元测试框架，在 openEuler 中可通过 `dnf install shunit2 -y` 安装，也可从 GitHub（`kward/shunit2`）获取。此问题与 PR 代码变更完全无关，属于 CI 基础设施的依赖缺失。

## 需要进一步确认的点
- 确认其他使用 `shunit2` 的 CI 测试是否同样受到影响（若全局影响说明 CI Runner 环境近期发生变更导致 shunit2 丢失）
- 确认 CI Runner 上 `shunit2` 的预期安装路径（`/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 第 13 行是如何引用 shunit2 的——是 `source`、`.` 还是直接调用）
