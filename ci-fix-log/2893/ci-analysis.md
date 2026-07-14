# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架依赖缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher

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
- 失败原因: CI 的 [Check] 阶段测试脚本 `common_funs.sh` 尝试通过 `source` (`.`) 加载 `shunit2` 测试框架库，但 `shunit2` 在 CI Runner 上未安装或路径未正确配置，导致脚本无法执行容器验证测试。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile（Others/bind9/9.21.23/24.03-lts-sp4/Dockerfile）以及配套的 named.conf、meta.yml、README.md、image-info.yml 均成功完成构建和推送：
- Docker 镜像构建成功：所有 6 个 Dockerfile 步骤（RUN yum install、meson compile/install、groupadd/useradd、COPY、权限设置）均正常完成（DONE）。
- meson 构建成功：422/422 目标全部编译和链接通过。
- 镜像推送成功：`[Push] finished`，aarch64 镜像已推送至 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`。

失败发生在构建完成后的 `[Check]` 验证阶段，该阶段由 CI 基础设施中的 `eulerpublisher` 测试框架执行，`shunit2` 文件缺失属于 CI Runner 环境配置问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 上安装 `shunit2` 测试框架。`shunit2` 是标准的 Shell 单元测试框架，可通过包管理器安装（如 `yum install shunit2` 或 `apt install shunit2`），或手动下载放置到 CI Runner 的测试脚本可加载的路径。

### 方向 2（置信度: 低）
若 `shunit2` 已安装但不在测试脚本预期的搜索路径中，检查 `/usr/local/etc/eulerpublisher/tests/common/` 或相关目录下的 `shunit2` 文件是否存在，并确认 `common_funs.sh` 中的加载路径（相对或绝对）是否正确。

## 需要进一步确认的点
- 验证同一 CI Runner 上其他成功的 PR 是否能正常找到 `shunit2`（判断是本次构建环境异常还是长期缺失）。
- 确认 `shunit2` 包在 openEuler 24.03-LTS-SP4 Runner 上的包名和安装路径。
- 检查 `eulerpublisher` 测试框架的部署方式：`shunit2` 是自带在 `eulerpublisher` 包内，还是需要作为系统级依赖单独安装。
