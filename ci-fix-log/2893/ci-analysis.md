# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39
- 新模式标题: （已匹配模式39，"CI工具依赖缺失"）
- 新模式症状关键词: shunit2, file not found, common_funs.sh

## 根因分析

### 直接错误
```
#13 exporting to image
#13 pushing layers 15.6s done
#13 pushing manifest for docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64@sha256:7a2bec1b0dc64d150b6cc9ed997e83ac4cd270db7f2f7c35c5af32ef0fa99ba5
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
- 失败原因: CI 环境的 `[Check]` 阶段在执行容器启动测试时，`common_funs.sh` 脚本尝试 `source` 加载 `shunit2` 测试框架，但 `shunit2` 未安装在 CI runner 上（`shunit2: file not found`），导致检查步骤直接崩溃。

### 与 PR 变更的关联

**与 PR 变更无关。**

- Docker 镜像构建阶段全部成功：422 个编译目标全部通过（`[422/422] Linking target named`），所有二进制产物成功安装到镜像中（`#9 DONE 41.4s`）。
- 镜像推送也成功完成：`[Push] finished`，manifest 已推送到 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`。
- 失败发生在构建/推送全部完成后的 `[Check]` 阶段，因 CI runner 环境缺少 `shunit2` shell 单元测试框架，容器健康检查脚本无法执行。

PR 新增的 Dockerfile（bind9 9.21.23 + openEuler 24.03-LTS-SP4）本身在构建上没有任何问题。

## 修复方向

### 方向 1（置信度: 高）
**由 CI 基础设施维护者处理，Code Fixer 无需介入。**

在 CI runner 镜像中安装 `shunit2` 包。openEuler 上可通过 `yum install shunit2 -y` 安装，或在 CI 编排脚本的预配置阶段执行该安装。这与 PR #2894（bisheng-jdk）中模式39 的根因类似——属于 CI 工具的运行时依赖缺失，与 Dockerfile 内容无关。

## 需要进一步确认的点

- 日志仅显示了 aarch64 架构的构建和 Check 流程（镜像 tag 含 `aarch64` 后缀）。需确认 x86_64 架构的构建 job 是否也受同样问题影响，或者是独立成功/失败的。
- 确认该 CI runner 上 `shunit2` 是原本存在但被误删，还是该 runner 类型历史上从未安装过此依赖。

## 修复验证要求

（不适用——本次失败属于 infra-error，无代码修改需求。）
