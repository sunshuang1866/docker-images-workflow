# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 测试脚本）
- 失败原因: CI runner 上缺少 `shunit2` shell 测试框架（`shunit2: file not found`），导致 [Check] 阶段的容器功能验证无法执行。该测试脚本第 13 行尝试 `source shunit2`，但 shunit2 未安装在 runner 环境中。

### 与 PR 变更的关联
**与 PR 无关。** PR 改动仅为新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套配置文件（named.conf、meta.yml、README.md、image-info.yml）。构建阶段完全成功：
- `meson setup/compile/install` 全部 422 个编译目标通过
- Docker 镜像构建 6 个步骤全部成功（DONE）
- 镜像 push 到 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64` 成功

失败发生在构建完成后的 [Check] 验证阶段，根本原因是 CI runner 测试环境缺少 `shunit2` 依赖，与本次代码变更无任何关联。

## 修复方向

### 方向 1（置信度: 高）
CI runner 维护人员在 `/usr/local/etc/eulerpublisher/tests/` 环境中安装 `shunit2` 测试框架，确保 `common_funs.sh` 能正确 source 该依赖。

### 方向 2（置信度: 低）
如果 shunit2 已安装但路径配置有误，检查 runner 的 `PATH` 或 shunit2 安装路径是否与 `common_funs.sh` 的 source 路径匹配。

## 需要进一步确认的点
1. 该 CI runner 上是否安装了 `shunit2`？执行 `which shunit2` 或检查 `/usr/share/shunit2/` 路径。
2. 同一 runner 上其他镜像的 [Check] 测试是否也失败（确认是否为全局性问题）。
3. 日志中仅展示了 aarch64 架构的构建，x86_64 架构的构建结果未知（但从日志末尾 `Finished: FAILURE` 已可明确失败点）。

## 修复验证要求
本次失败为 CI 基础设施问题，Code Fixer 无需处理任何代码。待 CI runner 环境修复后，重新触发构建即可验证。
