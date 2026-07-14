# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2缺失
- 新模式症状关键词: shunit2, file not found, Check, test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI Runner（Check 阶段），非容器内
- 失败原因: CI 的 [Check] 阶段调用 `common_funs.sh` 脚本时会 `source`（`.`）`shunit2` 测试框架库，但该框架未安装/不可用在该 CI runner 上，导致 shell 脚本在 line 13 执行失败，整个 Check 阶段被标记为失败。

### 与 PR 变更的关联
**与 PR 变更无关**。理由如下：
1. 该 PR 仅新增 bind9 的 Dockerfile、named.conf 配置文件，以及 README/meta/image-info 等元数据文档更新。
2. Docker 镜像构建（Build）、推送（Push）两个阶段均完全成功——meson 编译 422 个目标全部通过，镜像已成功推送至 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`。
3. 失败发生在构建完成后的 [Check] 阶段，根因是 CI runner 上缺少 `shunit2` shell 测试框架，属于 CI 基础设施问题，与 PR 代码无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境（`ecs-build-docker-aarch64-01-sp` 或对应 aarch64 节点）上安装 `shunit2` shell 单元测试框架。openEuler 上可通过 `yum install shunit2` 或从源码安装。安装后将该镜像的 Check 步骤重新触发即可。

## 需要进一步确认的点
- 确认 CI [Check] 阶段调用的 `common_funs.sh` 期望的 `shunit2` 安装路径（是系统目录如 `/usr/share/shunit2/shunit2` 还是项目自定义路径）。
- 确认该 CI runner 节点上其他已通过镜像的 Check 是否使用了 `shunit2`，还是这类测试框架仅在部分镜像上生效——若其他镜像从未经过 Check 验证，可能说明 Check 流程本身存在 bug，报告为 `shunit2` 缺失可能是误导。

## 修复验证要求
无需验证（infra-error，与 PR 代码无关）。
