# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39"CI工具依赖缺失"同类但症状不同）
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Building step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI runner 上的 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`（非 PR 代码）
- 失败原因: CI 的 [Check] 阶段（镜像构建后验证）依赖 `shunit2` shell 单元测试框架，但该框架在 CI runner 上未安装或不在预期路径，导致测试脚本 `common_funs.sh` 在第 13 行 `source shunit2` 时报 `file not found`

### 与 PR 变更的关联
**与 PR 无关**。本次 PR 仅新增了以下文件：
- `Others/bind9/9.21.23/24.03-lts-sp4/Dockerfile`（新增 bind9 构建文件）
- `Others/bind9/9.21.23/24.03-lts-sp4/named.conf`（新增配置文件）
- 更新 `meta.yml`、`README.md`、`image-info.yml`（新增版本条目）

Docker 镜像构建本身**已完全成功**：
- 所有 422 个编译目标通过（`[422/422] Linking target named`）
- `meson install` 成功安装所有二进制和 man 手册页
- 镜像导出和推送到 registry 成功（`#13 DONE 36.0s`，`[Build] finished`，`[Push] finished`）

失败仅发生在 CI runner 上 `eulerpublisher` 的 [Check] 阶段，`shunit2` 是 CI 基础设施中的测试依赖，与 PR 提交的任何文件无关。

## 修复方向

### 方向 1（置信度: 高）
CI infra 问题，**Code Fixer 无需处理此 PR**。需要在 CI runner 上安装 `shunit2` 测试框架（通常为 `shunit2` RPM 包或从 GitHub 获取），确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 能正常 `source` 到它。此操作属于 CI 运维团队职责范围，不在 PR 代码修改范畴内。

## 需要进一步确认的点
1. 确认 CI runner（aarch64 架构的 `ecs-build-docker-aarch64-*` 系列节点）上 `shunit2` 的预期安装路径和包名（不同发行版包名可能为 `shunit2`、`shunit2-sh` 或 `shunit2-ng`）
2. 确认 `common_funs.sh` 中 `source shunit2` 的具体写法（是否需要全路径，或是否依赖 `PATH` 环境变量）
3. 如果 `shunit2` 是近期被移除或 CI runner 镜像更新导致丢失，需排查该节点的镜像构建流程
