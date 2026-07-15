# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, .: shunit2

## 根因分析

### 直接错误
```
#13 DONE 36.0s
euler_builder_20260710_092104 removed
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
- 失败原因: CI [Check] 阶段的测试脚本 `common_funs.sh` 尝试通过 `. shunit2` 引入 shunit2 shell 测试框架，但该文件在 CI runner 上不存在，导致 Check 测试步骤直接失败。

日志显示 Docker 镜像的构建（`[Build] finished`）和推送（`[Push] finished`）均已成功完成，bind9 的 meson 编译 422/422 步全部通过，镜像已推送到 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`。失败仅发生在构建完成后的容器功能验证（Check）阶段，与 PR 的代码变更无关。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 变更仅包含：
1. 新增 `Others/bind9/9.21.23/24.03-lts-sp4/Dockerfile`（bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Docker 构建文件）
2. 新增 `Others/bind9/9.21.23/24.03-lts-sp4/named.conf`（BIND 配置文件）
3. 更新 `Others/bind9/README.md`、`Others/bind9/doc/image-info.yml`、`Others/bind9/meta.yml`（文档和元数据更新）

Docker 构建阶段（包括依赖安装、meson 编译、链接、安装）全部成功完成，无任何编译或构建错误。失败发生在 CI 基础设施层面的 Check 测试框架中，`shunit2` 依赖缺失是 CI runner 环境问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架。`shunit2` 是一个 shell 单元测试框架，通常可通过 `dnf install shunit2` 或将其脚本下载到 `/usr/local/etc/eulerpublisher/tests/container/common/` 目录下解决。此为纯粹的 CI 基础设施问题，Code Fixer 无需修改任何 PR 代码。

## 需要进一步确认的点
1. `shunit2` 是否应作为 CI runner 镜像的预装依赖（即所有 Check 测试都依赖它），还是仅特定镜像的 Check 测试需要——从错误路径 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 判断，这是通用测试脚本，说明 `shunit2` 应当是 CI runner 的标准预装组件。
2. 本次日志仅展示了 aarch64 架构的构建和 Check 结果，x86_64 架构的构建 job 日志未提供，无法确认 x86_64 是否存在其他问题。
3. 确认 `shunit2` 在 CI runner 上的安装路径是否与 `common_funs.sh` 中 `. shunit2` 的查找路径（相对路径 / PATH）匹配。
