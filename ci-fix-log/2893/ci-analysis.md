# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI 测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, CRITICAL: [Check] test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 后置 [Check] 阶段中，`common_funs.sh` 脚本尝试 source 加载 `shunit2` 单元测试框架，但该框架未安装在当前 aarch64 CI runner 上，导致测试脚本直接失败。

### 与 PR 变更的关联
**与 PR 无关。** Docker 镜像构建完全成功：
- 编译阶段：422/422 个 C 编译目标全部完成，`meson compile -j -1 -C build` 成功
- 安装阶段：所有二进制文件、库文件、man 手册页正常安装至 `/bind9/build`
- 推送阶段：镜像 `openeulertest/bind9:9.21.23-oe2403sp4-aarch64` 已成功推送至 `docker.io`

PR 新增的内容（Dockerfile、named.conf、README、image-info.yml、meta.yml）均不涉及 CI 测试基础设施，构建产物本身没有问题。

## 修复方向

### 方向 1（置信度: 高）
CI 管理员在当前 aarch64 runner 上安装 `shunit2` 测试框架。openEuler 下可通过以下方式之一安装：
- `dnf install shunit2`（如果仓库中包含该包）
- 或从 EPOL 源安装
- 或手动部署 shunit2 脚本到 CI runner 的 `/usr/local/etc/eulerpublisher/tests/container/common/` 路径

### 方向 2（置信度: 低）
若 `shunit2` 安装后问题依旧，检查 `common_funs.sh:13` 中 source 的 `shunit2` 路径是否正确（是相对路径还是绝对路径、文件是否在预期位置）。

## 需要进一步确认的点
- CI runner 的 OS 版本及可用包仓库，确认 `shunit2` 或 `shunit2` 的包名（在不同发行版中包名可能为 `Shunit2`、`shunit2` 或需从 EPOL 获取）
- 本次 CI 是否还有其他架构（如 x86-64）的 [Check] 失败日志未提供，若有则一并确认
