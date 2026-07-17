# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
#13 exporting to image
#13 pushing layers 15.6s done
#13 pushing manifest for docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64@sha256:...
#13 DONE 36.0s
2026-07-10 09:23:59,481 - INFO - [Build] finished
2026-07-10 09:23:59,481 - INFO - [Push] finished
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 编排工具 `eulerpublisher` 在 [Check] 阶段执行容器测试时，其公共函数脚本 `common_funs.sh` 尝试 source `shunit2`（Shell 单元测试框架），但该框架在 CI Runner 上未安装或不在 `PATH` 中，无法被找到，导致测试直接失败。

### 与 PR 变更的关联
**无关**。本次 PR 仅新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、named.conf 配置文件，以及更新了 README.md、image-info.yml、meta.yml 等元数据文件。Docker 镜像构建（meson 编译 422/422 目标全部成功）和推送均已完成，失败纯粹发生在 CI 后处理阶段的测试环境依赖缺失——这是 CI Runner 自身的基础设施问题，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
CI Runner 测试环境中缺少 `shunit2` 包。需在 CI Runner 镜像或初始化脚本中安装 `shunit2`（openEuler 系统中通常通过 `yum install shunit2` 或 `dnf install shunit2` 安装），确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 中的 `. shunit2` 能成功找到该框架。

## 需要进一步确认的点

1. 确认 CI Runner（aarch64 执行节点）的操作系统环境是否正确安装了 `shunit2` 包。
2. 确认同一镜像的其他架构构建（如 x86_64）的 Check 阶段是否也出现相同错误——若 x86_64 runner 的 shunit2 正常，则问题仅限于 aarch64 runner 的环境配置。
3. 确认 CI Runner 初始化流程是否近期有变更（如基础镜像更新导致 shunit2 被移除）。
