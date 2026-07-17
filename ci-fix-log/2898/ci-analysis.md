# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
#7 DONE 67.8s
#8 DONE 40.5s
#9 DONE 1.5s
#11 DONE 41.9s
[Build] finished
[Push] finished
[Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
[Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI runner（aarch64）上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试脚本 `common_funs.sh` 第 13 行尝试 `source` 或执行 `shunit2`，但 `shunit2` 测试框架在 aarch64 CI runner 上未安装或不在 `PATH` 中，导致 `[Check]` 阶段直接崩溃

### 与 PR 变更的关联
PR 变更与 CI 失败**无关**。PR 的改动为纯增量：新增 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，及对应的 README、image-info.yml、meta.yml 条目。Docker 镜像的构建（Build）和推送（Push）阶段均已成功完成（#7～#11 全部 DONE），失败仅发生在 `eulerpublisher` 容器测试工具链的 `[Check]` 阶段，该阶段依赖的 `shunit2` 是 CI runner 环境级别的依赖，不受 Dockerfile 内容影响。

## 修复方向

### 方向 1（置信度: 高）
在 aarch64 CI runner（`ecs-build-docker-aarch64-01-sp`）上安装 `shunit2` 测试框架，或确保其所在路径已被加入 `$PATH`。`shunit2` 是 shell 单元测试框架（通常位于 `/usr/share/shunit2/shunit2` 或类似路径），需要在 runner 层面由 CI 管理员安装配置。类似地将 `shunit2` 包安装命令添加到 aarch64 runner 的 provisioning/初始化脚本中。

### 方向 2（置信度: 低）
若 `shunit2` 应为 `eulerpublisher` Python 包自带的依赖，检查 `eulerpublisher` 在 aarch64 runner 上的安装是否完整，`pip install eulerpublisher` 是否遗漏了 shell 层面的 `shunit2` 依赖。

## 需要进一步确认的点
1. 同 PR 的 x86_64 架构构建 job 是否也因同样原因失败？还是只有 aarch64 失败？（当前日志仅提供了 aarch64 runner 的输出）
2. 其他 SP4 镜像（非 Go）的 `[Check]` 阶段在 aarch64 runner 上是否也失败？——这可用于判断问题是本 runner 特有问题还是 SP4 镜像测试的普遍问题
3. `shunit2` 是 eulerpublisher CI 框架的标准依赖还是需要额外手动安装？在 x86_64 runner 上 `shunit2` 是否已存在？
4. `common_funs.sh` 中 `shunit2` 的预期安装路径是什么？（如 `/usr/share/shunit2/shunit2` 或 `/usr/bin/shunit2`）

## 修复验证要求
若修复方向 1 被采纳（CI 管理员安装 shunit2），验证方式：在 aarch64 runner 上重新触发该 PR 的 CI 构建，确认 `[Check]` 阶段不再报 `shunit2: No such file or directory` 且整体 pipeline 通过。
