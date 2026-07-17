# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行环境中的 `eulerpublisher` 测试框架 `common_funs.sh` 在第 13 行引用了 `shunit2`，但 `shunit2`（Shell 单元测试框架）未安装在 CI runner 上，导致 `[Check]` 阶段失败。

Docker 镜像构建（`[Build]`）和推送（`[Push]`）均已成功完成：
- 步骤 #7：Go 源码下载和验证 — 完成（67.8s）
- 步骤 #8：文件时间戳规范化 — 完成（40.5s）
- 步骤 #9：构建工具卸载 — 完成（1.5s）
- 步骤 #10：WORKDIR 设置 — 完成
- 步骤 #11：镜像导出和推送至 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64` — 完成（41.9s）
- 日志明确输出 `[Build] finished` 和 `[Push] finished`

失败仅发生在构建后的 `[Check]` 阶段，是 CI 基础设施缺少 `shunit2` 依赖所致。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml），Docker 镜像本身的构建和推送均已成功。`shunit2` 缺失是 CI runner 环境问题，属于基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境（`ecs-build-docker-aarch64-01-sp` 或对应节点）上安装 `shunit2` Shell 测试框架包。openEuler 仓库中 `shunit2` 的包名为 `shunit2`，可通过 `dnf install shunit2 -y` 安装。安装后重新触发 CI 构建即可通过 `[Check]` 阶段。

## 需要进一步确认的点
- 确认 build 日志来自 aarch64 runner，对应标签为 `1.25.6-oe2403sp4-aarch64`。需确认 x86_64 runner 的构建 job 是否也存在相同的 `shunit2` 缺失问题。
- 确认 `shunit2` 包在 openEuler 24.03-LTS-SP4 仓库中的确切包名和可用性。
