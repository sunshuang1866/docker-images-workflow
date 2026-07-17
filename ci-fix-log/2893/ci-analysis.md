# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39"CI工具依赖缺失"同类，但缺失组件不同）
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: `shunit2: file not found`, `common_funs.sh`, `CRITICAL: [Check] test failed`

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`（source shunit2 步骤）
- 失败原因: CI 检查阶段的测试框架脚本 `common_funs.sh` 在 source `shunit2`（shell 单元测试框架）时，该文件在 CI runner 环境中不存在，导致 `[Check]` 步骤直接崩溃（exit code 非零），Jenkins 将构建标记为 `FAILURE`。

### 与 PR 变更的关联
**无关联。** 此次 PR 仅新增了 bind9 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、配置文件、meta.yml 条目和文档更新。Docker 镜像的构建（[Build]）和推送（[Push]）均已成功完成：
- meson setup/compile/install 三个阶段全部通过（422/422 编译目标均成功）
- 镜像导出并成功推送至 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`
- 唯一的失败发生在 CI 后处理阶段的容器检查脚本中，因为 CI runner 缺少 `shunit2` 库导致测试脚本无法运行

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 的测试环境中安装 `shunit2` 包（或确保 `shunit2` 脚本存在于 `/usr/local/etc/eulerpublisher/tests/container/common/` 路径下），使容器健康检查脚本能够正常 source 该测试框架。这是 CI 基础设施配置问题，与 PR 代码变更无关，不需要修改任何 Dockerfile 或源码文件。

## 需要进一步确认的点
1. 确认 CI runner 节点上是否安装了 `shunit2` 包（可通过 `dnf list installed | grep shunit2` 或 `which shunit2` 检查）
2. 确认该 CI runner 是否是新近创建的节点（缺少依赖配置），而同仓库其他成功的 PR 是否使用了不同 runner
3. 确认 CI 编排脚本中是否缺少 `shunit2` 的安装步骤（检查 eulerpublisher 的部署/初始化逻辑）
