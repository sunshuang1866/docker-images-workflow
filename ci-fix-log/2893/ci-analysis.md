# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed, eulerpublisher

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段测试框架的 `common_funs.sh` 脚本试图 source `shunit2`（shell 单元测试框架），但该文件在 CI runner 环境中不存在（未安装或路径配置错误）。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、named.conf 配置文件，以及更新了 README.md、image-info.yml 和 meta.yml 的版本条目。Docker 镜像的构建（422 个编译目标全部成功）和推送均已完成：

```
2026-07-10 09:23:59,481 - INFO - [Build] finished
2026-07-10 09:23:59,481 - INFO - [Push] finished
```

失败发生在构建完成后的镜像检查（[Check]）阶段，原因是 CI runner 上缺失 `shunit2` 测试工具，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner（`ecs-build-docker-aarch64-*` 系列节点）上安装 `shunit2` shell 测试框架。`shunit2` 可从 EPEL 仓库或 GitHub 获取安装。

### 方向 2（置信度: 低）
若不希望在所有 CI runner 上安装 `shunit2`，可修改 `common_funs.sh` 脚本，使其在 `shunit2` 缺失时优雅降级（跳过测试并返回成功，而非报 CRITICAL 错误）。

## 需要进一步确认的点
1. 同一 CI runner 上其他镜像（如 `bind9:9.21.23-oe2403sp3`）的 [Check] 测试是否也因同样原因失败。如果其他镜像的 Check 测试正常通过，则可能是该 PR 触发了某个特定测试路径导致 `shunit2` 查找失败。
2. `shunit2` 在 CI 环境中的预期安装路径是什么——是 `/usr/share/shunit2/shunit2`、`/usr/bin/shunit2`，还是通过 pip 安装的。
3. `common_funs.sh` 中 source `shunit2` 的具体方式——是硬编码路径还是基于 `PATH` 查找，以确定修复方式。
