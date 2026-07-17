# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 检查测试工具缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 环境中缺少 `shunit2`（shell 单元测试框架），导致 [Check] 阶段的测试脚本在初始化时即失败。Docker 镜像构建（[Build]）和推送（[Push]）阶段均已成功完成。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个 Go 1.25.6 on openEuler 24.03-LTS-SP4 的 Dockerfile，以及更新了 README.md、image-info.yml、meta.yml 中的表项。Docker 构建全程成功（所有 5 个步骤均 DONE，镜像成功 push 到 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64`）。失败发生在 CI 测试框架自身的初始化阶段，`shunit2` 工具不可用是 Runner 环境问题，与 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 中）
CI Runner 环境缺少 `shunit2` 可执行文件。需要在 CI Runner 节点上安装 `shunit2`（可通过包管理器如 `dnf install shunit2` 安装，或手动下载放置到 PATH 中），确保 `common_funs.sh` 第 13 行的 `source shunit2` 或 `. shunit2` 能正常加载。

### 方向 2（置信度: 低）
如果 `shunit2` 应从被测试的容器镜像（`openeulertest/go:1.25.6-oe2403sp4-aarch64`）中获得，则需检查 Go 镜像是否缺少 shunit2 相关文件、或者检查阶段的容器启动/挂载逻辑是否异常。但从日志路径看，`common_funs.sh` 位于 `/usr/local/etc/eulerpublisher/tests/` 下，是 CI Runner 侧的工具脚本，更可能是 Runner 环境问题。

## 需要进一步确认的点
1. 确认 CI Runner（`aarch64` 节点）上是否已安装 `shunit2`（执行 `which shunit2` 或 `rpm -q shunit2`）
2. 在同一次 CI Run 中，其他镜像（如已有的 sp3 版本）的 [Check] 阶段是否能通过——如果其他镜像也失败，则可确认是 Runner 级环境问题
3. 如果其他镜像检查通过但本镜像失败，需要获取 eulerpublisher 的 `common_funs.sh` 完整源码，确认 line 13 的 shunit2 加载逻辑以及失败原因是否与镜像内容有关
