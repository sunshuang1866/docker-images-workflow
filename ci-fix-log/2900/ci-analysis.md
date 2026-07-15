# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺shunit2
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, [Check] test failed

## 根因分析

### 直接错误

```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位

- 失败位置: CI 主机上 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 宿主环境的 `eulerpublisher` 测试框架在执行容器 [Check] 阶段时，`common_funs.sh` 尝试通过 `.` 命令加载 `shunit2`（Shell 单元测试库），但该文件在 CI runner 的 `PATH` 或脚本预期路径中不存在，导致测试框架初始化失败，所有检查项均未执行（Check Results 表格为空）。

### 与 PR 变更的关联

**此失败与 PR 代码变更无关**。Docker 镜像构建和推送阶段均成功完成：

- Docker 构建 7 个步骤全部通过（`#10 DONE 41.6s` 为 httpd 编译安装，`#11 DONE 0.1s` 为配置阶段，`#12 DONE 0.0s` 为 COPY，`#13 DONE 0.1s` 为 chmod）
- 镜像已成功推送到 registry（`#14 pushing manifest ... done`，日志显示 `[Push] finished`）
- 唯一失败点在 CI 基础设施的后置 [Check] 阶段，因为 `shunit2` 缺失导致容器启动/运行检查无法执行

PR 新增的 Dockerfile 本身语法和构建流程无误，`groupadd`/`useradd` 在 openEuler 24.03-LTS-SP4 基础镜像中可用（与模式05不同，此基础镜像已包含 `shadow` 包）。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner（x86_64 构建节点）上安装 `shunit2` 包。openEuler 中可通过 `dnf install shunit2` 安装，或确认 `eulerpublisher` 测试框架期望的 `shunit2` 路径（位于 `/usr/local/etc/eulerpublisher/tests/` 同级目录或系统路径），确保 `common_funs.sh` 能够正确加载。

## 需要进一步确认的点

1. 确认该 CI runner（`ecs-build-docker-x86-64-01-sp` 或同类节点）上是否确实缺少 `shunit2`，可登录 CI 节点执行 `which shunit2` 或 `rpm -qa | grep shunit2` 验证。
2. 确认同一时期其他 PR（特别是同样使用 SP4 基础镜像的 PR）的 Check 阶段是否也遇到相同错误，以判断这是单个 runner 的问题还是全局环境问题。
3. 确认 `eulerpublisher` 测试框架对 `shunit2` 的预期加载路径是否需要与 `common_funs.sh` 中的相对路径一致。
