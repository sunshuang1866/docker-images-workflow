# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI runner 宿主环境 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段的测试脚本 `common_funs.sh` 尝试通过 `.` 命令 source `shunit2` 测试框架，但 CI runner 上未安装该框架，文件不存在，导致 Check 阶段直接失败。

### 与 PR 变更的关联
**与 PR 改动无关。** PR 仅新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套配置文件（named.conf）、元数据（meta.yml、image-info.yml、README.md）。Docker 镜像的构建（meson compile + install，422 个编译目标）和推送（Push）阶段均已成功完成：
- `#9 DONE 41.4s` — meson 构建完成
- `[Build] finished` — 构建成功
- `[Push] finished` — 推送成功
- `#13 DONE 36.0s` — 镜像导出与推送完成

失败仅发生在构建/推送之后的 Check（容器测试）阶段，且根因为 CI runner 宿主环境缺少 `shunit2` 测试框架，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 宿主环境上安装 `shunit2` 测试框架。该框架是 `eulerpublisher` 容器测试脚本 `common_funs.sh` 的依赖项，缺失会导致所有容器镜像的 Check 阶段都无法执行。可在 CI runner 初始化脚本中添加 `shunit2` 的安装步骤。

### 方向 2（置信度: 低）
如果 `shunit2` 已经安装但路径不对，检查 `common_funs.sh` 中 source `shunit2` 的路径配置是否正确（是否依赖 `PATH` 环境变量或硬编码路径）。

## 需要进一步确认的点
1. `shunit2` 是否仅在该特定 runner 上缺失，还是所有 CI runner 均未安装。可通过对比其他成功 PR 的 Check 阶段日志确认。
2. `shunit2` 在 CI runner 上的预期安装路径（标准位置或自定义路径）。
3. 是否有 CI runner 环境初始化脚本（如 Ansible playbook、Puppet manifest 或 cloud-init 脚本）负责安装测试依赖，该脚本是否需要更新。
4. 该 runner 是 aarch64 架构（日志中镜像 tag 为 `9.21.23-oe2403sp4-aarch64`），是否存在架构特定的 runner 环境差异。
