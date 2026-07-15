# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试框架依赖缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
[Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 测试框架 `eulerpublisher` 的 `[Check]` 阶段，文件 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI runner 的测试环境中缺少 `shunit2`（bash 单元测试框架），导致 `common_funs.sh` 脚本第 13 行无法找到/加载 `shunit2`，容器健康检查测试直接失败。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像的构建（5/5 步骤全部 DONE）和推送（Push finished）均成功完成，镜像已正确生成并推送到 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64`。失败发生在构建流程之后的独立 `[Check]` 测试阶段，根因是 CI 测试框架自身缺少运行时依赖 `shunit2`，属于 CI 基础设施问题。PR 新增的 Dockerfile、README.md、image-info.yml 和 meta.yml 变更均无问题。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 环境中安装 `shunit2`。对于 openEuler 环境，可通过 `dnf install shunit2` 或从源码安装 `shunit2` 到 `/usr/local/bin/` 或 `/usr/local/etc/eulerpublisher/tests/container/common/` 路径下，确保 `common_funs.sh:13` 能正常加载该框架。此问题与 PR 代码无关，应由 CI 维护团队处理。

## 需要进一步确认的点
1. 确认当前 CI aarch64 runner（`ecs-build-docker-aarch64-*`）上是否安装了 `shunit2` 包。可在 runner 上执行 `which shunit2` 或 `dnf list installed | grep shunit` 验证。
2. 确认 `common_funs.sh` 第 13 行是通过 `source`/`.` 加载本地文件，还是依赖 `PATH` 中的可执行文件，然后定位 `shunit2` 应被安装到的确切路径。
3. 确认同一个 CI 环境中其他成功通过 `[Check]` 的镜像（如其他 go 版本或其他应用镜像）是否使用了相同的测试框架路径，以判断该问题是 Go 镜像特有问题还是全局 CI runner 缺失依赖。

## 修复验证要求
Code-fixer 无需处理此问题。此失败为 CI 基础设施问题（`infra-error`），应由 CI 运维团队在 runner 环境中补充 `shunit2` 依赖后重新触发构建验证。
