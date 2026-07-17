# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试工具缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 测试脚本 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 测试框架的 `common_funs.sh` 脚本在第 13 行尝试加载 `shunit2` (shell 单元测试工具)，但 CI Runner 上未安装 `shunit2`，导致 `[Check]` 阶段容器验证测试失败。

Docker 镜像的构建和推送阶段均已**成功完成**：
- `[Build] finished` — 构建成功
- `[Push] finished` — 推送成功
- 镜像 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64` 已成功推送

失败仅发生在构建后的 `[Check]` 容器测试验证阶段，且原因是 CI 基础设施缺少测试工具，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 变更（新增 `Others/go/1.25.6/24.03-lts-sp4/Dockerfile`、更新 README.md/image-info.yml/meta.yml）**不直接触发**此失败。Dockerfile 的构建步骤（#7-#11）全部成功完成，镜像已正常推送。失败源于 CI Runner 的测试环境缺少 `shunit2` 框架，属于基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 上安装 `shunit2` 包。openEuler 仓库中 `shunit2` 的包名通常为 `shunit2`，可在 CI 环境的初始化脚本或 runner 镜像中通过 `dnf install shunit2 -y` 或等效方式安装该测试框架。

### 方向 2（置信度: 低）
如果 CI Runner 镜像不支持安装额外包，可考虑在测试脚本 `common_funs.sh` 中将 `shunit2` 的加载改为从网络下载或从仓库内嵌的本地副本加载。

## 需要进一步确认的点
1. 该 CI Runner (`ecs-build-docker-aarch64-01-sp` 或类似 aarch64 节点) 上是否曾经安装过 `shunit2`，是否因 Runner 镜像更新导致该包丢失。
2. 同一 PR 的 x86_64 架构构建是否也存在同样问题，还是仅在 aarch64 runner 上 `shunit2` 缺失。
3. `common_funs.sh` 中加载 `shunit2` 的方式（是 `source`、`.` 还是绝对路径引用），以确认是 PATH 缺失还是包未安装。
