# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: CI [Check] 阶段 — `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 工具链 `eulerpublisher` 在执行容器镜像 [Check] 阶段时，其测试框架脚本 `common_funs.sh` 尝试 `source` 加载 `shunit2`（shell 单元测试框架），但 `shunit2` 文件在 CI runner 上不存在，导致 Check 步骤直接失败。

### 与 PR 变更的关联
**与 PR 无关**。本次 PR 仅新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、named.conf 及配套元数据更新。整个构建阶段均成功完成：

- meson 编译：422/422 targets 全部编译通过并成功链接
- meson install：所有二进制文件和手册页安装成功
- Docker 镜像构建：所有 6 个构建步骤均 `DONE`
- 镜像推送：成功推送至 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`

失败发生在与 PR 代码完全无关的 CI 后置 [Check] 阶段，属于 CI 基础设施自身问题。

## 修复方向

### 方向 1（置信度: 高）
CI runner 环境缺少 `shunit2` 测试框架。`shunit2` 是一个 shell 单元测试框架（通常是一个名为 `shunit2` 的 shell 脚本文件），需要由 CI 管理员在构建节点上预装。这不是 Dockerfile 层面能解决的问题。处理方式：
- 联系 CI 基础设施团队，在构建节点上安装 `shunit2`（如通过系统包管理器或手动部署到 `eulerpublisher/tests/` 目录下）
- 或重试 CI job，确认是否为瞬时的 runner 环境异常

## 需要进一步确认的点
- `shunit2` 在 CI runner 上的预期安装路径是什么（是系统级安装还是 `eulerpublisher` 自带）
- `shunit2` 缺失是所有镜像的 Check 阶段都受影响，还是仅该 runner 节点的环境问题（如为后者，可通过更换 runner 重试解决）
