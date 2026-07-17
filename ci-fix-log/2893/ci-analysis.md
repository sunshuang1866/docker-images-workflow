# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（关联 模式39：CI工具依赖缺失）
- 新模式标题: CI测试框架shunit2缺失
- 新模式症状关键词: `shunit2: file not found`, `common_funs.sh`, `Check test failed`

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`（CI 工具 eulerpublisher 的容器测试框架）
- 失败原因: CI runner 环境中缺少 `shunit2` 测试库，`common_funs.sh` 第 13 行执行 `source shunit2`（或 `. shunit2`）时找不到该文件，导致 [Check] 阶段的容器验证测试无法执行，进而整个 job 被标记为失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 构建和镜像推送均已成功完成（全部 422 个 meson 编译目标通过，所有库链接成功，镜像成功推送到 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`）。失败仅发生在构建和推送完成后的 [Check] 阶段——该阶段由 CI 工具 `eulerpublisher` 驱动，负责对已构建的镜像进行容器启动等运行时验证。`shunit2` 是 CI 测试框架的运行时依赖，其缺失属于 CI 基础设施配置问题，不受 Dockerfile 或 PR 任何文件变更影响。

## 修复方向

### 方向 1（置信度: 高）
CI 运维侧在 runner 环境中安装 `shunit2`。`shunit2` 是一个 shell 单元测试框架，通常通过系统包管理器安装（如 `dnf install shunit2`）或直接下载 shell 脚本放置到 `$PATH` 路径。确认 CI runner 镜像或初始化脚本中是否遗漏了 `shunit2` 的安装步骤。

### 方向 2（置信度: 低）
如果 `shunit2` 在 CI 环境中是可选的（即某些 runner 有、某些没有），则可能是此 Dockerfile 被错误调度到了一个缺少 `shunit2` 的 runner 上。检查该 job 的 runner 标签/调度规则。

## 需要进一步确认的点
1. CI runner 环境中 `shunit2` 是否从未安装，还是仅此特定 aarch64 runner 上缺失
2. 其他同类 PR（SP4 新增 Dockerfile）的 [Check] 阶段是否也有相同报错（可从 CI 历史记录交叉验证）
3. `eulerpublisher` 的部署方式是否有更新导致 `shunit2` 依赖丢失

## 修复验证要求
（不适用 — infra-error，Code Fixer 无需处理此问题）
