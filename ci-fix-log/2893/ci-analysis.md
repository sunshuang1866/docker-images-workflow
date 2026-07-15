# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（参见已知模式 39 "CI工具依赖缺失"，症状类似但具体缺失组件不同）
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, [Check] test failed

## 根因分析

### 直接错误
```
[Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
CRITICAL: [Check] test failed
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI runner 上缺少 shell 单元测试框架 `shunit2`，导致 `eulerpublisher` 工具在 [Check] 阶段执行容器测试时，`common_funs.sh` 脚本在第 13 行 `source shunit2` 失败，检查步骤无法执行。

### 与 PR 变更的关联
**与 PR 变更无关。** 此次 PR 新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关配置文件（named.conf、meta.yml、README.md、image-info.yml）。Docker 镜像的编译（422 个 C/C++ 编译单元全部通过）、安装和推送阶段均已完成且成功：
- `[Build] finished` — 构建成功
- `[Push] finished` — 推送成功（`docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`）

失败发生在镜像构建完成后的 **测试/检查阶段**，根因是 CI runner 上缺少 `shunit2` 测试框架依赖，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
由 CI 运维在构建 runner 上安装 `shunit2`（shell 单元测试框架）。该框架未被安装在 `/usr/local/etc/eulerpublisher/tests/container/` 路径下或其 shell `PATH` 可搜索范围内，导致测试脚本 `common_funs.sh` 无法 source 该库。修复后重新触发 CI 运行即可验证。

### 方向 2（置信度: 低）
若 `shunit2` 本应作为 `eulerpublisher` 包的一部分被安装但在此次构建环境中遗漏，可能是 `eulerpublisher` 包版本的打包问题，需与 eulerpublisher 维护者确认其安装脚本是否包含了 `shunit2` 依赖。

## 需要进一步确认的点
1. 当前日志仅包含 aarch64 架构的构建过程。PR 声明支持 `amd64, arm64` 双架构，需确认 amd64 架构的构建 job 是否同样成功，或是否存在独立的失败。日志中未见 amd64 构建的 job ID 或输出。
2. 确认 `shunit2` 在其他成功 PR 的 CI runner 上是否已安装。若其他 PR 的 [Check] 阶段同样失败，说明是 CI 环境的全局问题；若仅此 PR 失败，则可能是特定 runner 节点缺少该依赖。
3. `shunit2` 预期安装路径为 `/usr/local/etc/eulerpublisher/tests/container/app/../common/` 还是系统级路径（如 `/usr/share/shunit2`），需与 eulerpublisher 工具文档确认。
