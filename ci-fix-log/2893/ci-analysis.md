# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2依赖缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, Check test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13（CI 测试基础设施脚本）
- 失败原因: CI 编排工具 `eulerpublisher` 在 [Check] 阶段执行容器测试时，测试框架脚本 `common_funs.sh` 尝试通过 `. shunit2` 导入 shell 单元测试库 `shunit2`，但该库未安装或不在 `PATH` 中，导致测试进程在启动阶段即失败。

### 与 PR 变更的关联

**与 PR 无关。** 证据如下：

1. Docker 镜像构建全部成功（Dockerfile 中 6 个 `RUN`/`COPY` 步骤均标记 `DONE`）
2. 镜像推送成功（`[Push] finished`，manifest sha256 已生成）
3. 编译阶段成功：422 个编译目标全部通过，`named` 链接成功（`[422/422] Linking target named`）
4. 错误发生在 `eulerpublisher` CI 工具的 [Check] 阶段，具体是 CI 测试基础设施脚本 `common_funs.sh` 找不到 `shunit2` 库——这是在检查容器启动/运行状态之前就发生的框架级错误

PR 新增的 Dockerfile、named.conf、meta.yml、README.md、image-info.yml 均与 `shunit2` 缺失无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 包。openEuler 上可通过以下方式安装：
```bash
yum install -y shunit2
```
确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 中的 `. shunit2` 能够正确找到该库。

### 方向 2（置信度: 低）
若 `shunit2` 确实已安装在 CI runner 上但仍报 `file not found`，需检查 `eulerpublisher` 测试脚本的 `PATH` 配置或 `shunit2` 的安装路径是否与脚本预期的搜索路径一致。

## 需要进一步确认的点

- 确认该 CI runner（`ecs-build-docker-aarch64` 系列）是否未预装 `shunit2`，或者 `shunit2` 的安装路径与 `eulerpublisher` 脚本预期不一致
- 确认其他同时期使用同一 CI runner 的新镜像 PR（尤其是 24.03-LTS-SP4 平台）是否也出现同类 [Check] 测试失败——如果是，说明是 CI 基础设施变更导致 `shunit2` 从 runner 镜像中移除
- 确认 x86_64 架构的 [Check] 是否也因同样原因失败（当前日志仅包含 aarch64 的检查结果）
