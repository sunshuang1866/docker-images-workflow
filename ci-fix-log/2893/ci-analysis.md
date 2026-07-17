# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架shunit2缺失
- 新模式症状关键词: `shunit2: file not found`, `common_funs.sh`, `[Check] test failed`, `eulerpublisher`

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 宿主机文件 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 测试框架 `eulerpublisher` 在 `[Check]` 阶段执行容器测试脚本时，尝试通过 `. common/common_funs.sh` 引入 `shunit2` Shell 单元测试框架，但该文件在 CI runner 上不存在，导致测试脚本加载失败。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了一个 bind9 Dockerfile 和配套的 README.md、image-info.yml、meta.yml 更新。Docker 镜像构建（编译 422 个 C 对象、链接可执行文件、安装二进制到镜像）、推送均已成功完成：

```
#9 DONE 41.4s            # 构建完成
#12 DONE 0.1s            # 最后一步 RUN 完成
#13 pushing layers 15.6s  # 推送成功
```

失败发生在构建和推送结束后的 `[Check]` 阶段，`eulerpublisher` 调用 `shunit2` 对已发布镜像进行启动/功能验证时，因 CI 环境缺少 `shunit2` 导致无法执行测试。该问题会影响所有需要经过 `[Check]` 阶段的 PR，属于 CI 基础设施层面缺陷。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` Shell 单元测试框架，使其位于 `eulerpublisher` 测试脚本预期的路径（`/usr/local/etc/eulerpublisher/tests/container/common/`）下，或通过环境变量 `SHUNIT2_HOME` / `PATH` 使其可被 source。

### 方向 2（置信度: 低）
若无法在 CI runner 上安装 shunit2，则需联系 CI 基础设施运维团队确认 `eulerpublisher` 测试框架的依赖是否完整，或检查 runner 镜像/环境是否因最近更新导致 shunit2 被移除。

## 需要进一步确认的点
- `shunit2` 是该 CI runner 环境的既有依赖还是近期新增的测试需求——需确认其他同期 PR 是否同样遇到此问题。
- 日志仅展示了 aarch64 架构的构建输出（`openeulertest/bind9:9.21.23-oe2403sp4-aarch64`），x86_64 架构的构建 job 可能在另一并行 runner 上执行，需确认其是否也因相同原因失败。

## 修复验证要求
不适用——本失败为 CI 基础设施问题（infra-error），不涉及对 Dockerfile 或任何 PR 代码的修改。
