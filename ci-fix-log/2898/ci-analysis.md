# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, CRITICAL: [Check] test failed

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 测试框架脚本 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 测试环境中缺少 `shunit2`（Shell 单元测试框架），`common_funs.sh` 第 13 行尝试 source `shunit2` 时失败，导致 [Check] 阶段的容器启动测试无法执行，直接报 `test failed`

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了一个 Go 1.25.6 的 Dockerfile 用于 openEuler 24.03-LTS-SP4 基础镜像，并更新了 README.md、image-info.yml、meta.yml 等元数据文件。Docker 镜像的构建（Build）和推送（Push）阶段均成功完成：
- `#11 DONE 41.9s` — 镜像导出和推送完成
- `[Build] finished` — 构建完成
- `[Push] finished` — 推送完成

失败仅发生在构建后的 [Check] 阶段，原因是 CI runner 环境中 `shunit2` 未安装/不在 PATH 中。该失败与本次 PR 的代码变更无关，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2`。若其他同类镜像（如已有的 openEuler 24.03-LTS-SP3 Go 镜像）的 Check 阶段也使用同一测试框架，则应确认这些 job 的 runner 是否已安装了 `shunit2`，或是否使用了不同的 runner 镜像。需检查 CI 编排配置中负责 [Check] 阶段的 runner 环境是否遗漏了 `shunit2` 依赖。

## 需要进一步确认的点
- 同一 CI 流水线中其他架构（x86_64/amd64）的下游构建 job 是否也因 `shunit2` 缺失而失败（当前日志仅展示了 aarch64 的构建过程）
- 该 CI runner 环境中 `shunit2` 是原本就不存在，还是近期被移除/升级导致路径变更
- 已有的 openEuler 24.03-LTS-SP3 等同类型镜像的 job 是否使用同一 runner，若它们能通过 [Check] 阶段，说明问题可能出在新增 runner 的配置上

## 修复验证要求
（无需特殊验证 — 本次失败为 infra-error，无需修改任何代码文件）
