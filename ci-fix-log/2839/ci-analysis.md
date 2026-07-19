# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39「CI工具依赖缺失」同族，但缺失的具体工具不同）
- 新模式标题: CI缺少shunit2
- 新模式症状关键词: shunit2: No such file or directory, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh`:13（CI 测试框架脚本）
- 失败原因: CI 运行器环境中缺少 `shunit2`（Shell 单元测试框架），导致 eulerpublisher 的容器镜像 [Check] 阶段无法加载测试桩函数，所有 Check Items 均为空，测试判定为失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 `Database/postgres/17.6/24.03-lts-sp4/` 目录下的 Dockerfile 和 entrypoint.sh，并在 meta.yml 和 README.md 中注册新镜像条目。Docker 镜像构建和推送均已成功完成：

- `#8 DONE 268.4s` — `make -j "$(nproc)" && make install` 编译安装成功
- `[Build] finished` — 构建完成
- `[Push] finished` — 推送完成

失败完全发生在 eulerpublisher CI 框架的 [Check] 后处理阶段，该阶段依赖 `shunit2` 执行容器冒烟校验，而当前 CI runner 环境中该工具缺失。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2`（Shell 单元测试框架）。这是 eulerpublisher 测试框架 `common_funs.sh` 的运行时依赖，缺失会导致所有容器镜像的 [Check] 阶段失败。需要在 CI runner 初始化/provisioning 脚本中添加 `shunit2` 的安装步骤（如 `dnf install shunit2` 或从源码安装）。

**Code Fixer 无需处理此问题。** 这是 CI 基础设施层面的缺陷，与 PR 中的 Dockerfile、entrypoint.sh、meta.yml 等代码变更无关。PR 的变更本身是正确的——镜像已成功构建并推送。

## 需要进一步确认的点
1. 同一 CI runner 上其他镜像（如已有的 24.03-lts-sp2 的 postgres 镜像）在 Check 阶段是否也因同样原因失败——如果其他镜像能通过 Check，则需确认该 runner 是否专门为新平台配置但遗漏了 `shunit2` 依赖。
2. CI runner 的操作系统版本和已安装包列表，以确认 `shunit2` 是否在预期安装列表中。
