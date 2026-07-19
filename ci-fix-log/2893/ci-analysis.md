# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI缺少shunit2测试框架
- 新模式症状关键词: shunit2: file not found, common_funs.sh, check test failed, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: CI [Check] 阶段，测试脚本 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI runner 上缺少 `shunit2`（Shell 单元测试框架），测试脚本在 `source`（`.`）该框架文件时失败，导致整个 [Check] 阶段报 CRITICAL 错误。

### 与 PR 变更的关联
**与 PR 无关**。PR 的改动仅涉及新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件。Docker 镜像构建和推送阶段均已成功完成：
- `meson compile` 全部 422 个编译目标通过，链接成功
- `meson install` 安装成功
- Docker 镜像导出和推送到 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64` 成功
- `[Build] finished` 和 `[Push] finished` 均正常

失败仅在构建完成后的 [Check] 阶段，因 CI runner 环境缺少 `shunit2` 测试框架导致容器启动检查脚本无法执行，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 测试框架。该框架通常通过包管理器（如 `dnf install shunit2` 或 `yum install shunit2`）安装，或将其 shell 脚本部署至测试脚本 `common_funs.sh` 能 source 到的路径（当前期望路径为 `PATH` 中可搜索或相对路径 `shunit2`）。此为纯粹的 CI 环境配置问题，无需修改任何 PR 代码。

## 需要进一步确认的点
- 确认 CI runner 的操作系统版本及可用的 `shunit2` 包名（openEuler 上可能为 `shunit2` 或需从 EPOL 仓库安装）。
- 确认该 CI runner 上是否其他同类 PR 的 [Check] 阶段也出现相同错误（判断是单个 runner 问题还是整个 CI 集群的镜像缺少 `shunit2`）。
- 确认 aarch64 架构 job 和 x86_64 架构 job 是否均受此影响（当前日志仅展示了 aarch64 job 的输出）。
