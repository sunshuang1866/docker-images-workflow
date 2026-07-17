# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 类似模式39（CI工具依赖缺失）
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2: file not found, eulerpublisher, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```
```
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 测试脚本）
- 失败原因: CI 运行环境中的 `eulerpublisher` 容器检测脚本 `common_funs.sh` 需要 `shunit2`（Shell 单元测试框架），但该框架未安装在 CI runner 上，导致 `[Check]` 阶段无法执行容器启动测试而失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套配置文件。Docker 构建、编译（422 个编译目标全部成功）、安装和镜像推送均已完成且无错误：
- `meson compile` 阶段：所有 422/422 编译/链接目标成功完成
- `meson install` 阶段：所有二进制文件、库文件和 man 手册页成功安装
- 镜像导出和推送：成功推送至 registry `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`

失败仅发生在构建完成后的 CI `[Check]` 后处理阶段，原因为 `shunit2` 测试框架缺失，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 包，使 `eulerpublisher` 的容器检测脚本能够正常加载该框架并执行容器启动测试。这是 CI 基础设施的配置问题，**无需修改 Dockerfile 或任何 PR 代码文件**。

## 需要进一步确认的点
- `shunit2` 是否应该作为 CI runner 镜像的预装依赖（即所有镜像的 `[Check]` 阶段当前是否均失败，而不仅限于本 PR）
- 若其他镜像（如基于 24.03-lts-sp3 或其他 OS 版本的同仓库镜像）的 `[Check]` 阶段正常工作，需确认它们是否使用了不同的测试脚本路径或 runner 配置
