# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI缺少shunit2框架
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 上缺少 `shunit2` Shell 测试框架，导致 [Check] 阶段的容器验证脚本在 source `shunit2` 时失败。Docker 镜像构建（12/12 步骤全部成功）和推送均已正常完成，此失败与 PR 代码变更无关。

### 与 PR 变更的关联
**无关**。PR 新增的 Dockerfile（bind9 9.21.23 on openEuler 24.03-LTS-SP4）构建完全成功：
- 编译阶段：422/422 个 meson 编译目标全部通过，二进制安装完成（`#9 DONE 41.4s`）
- 镜像构建：所有 6 个 Docker 构建步骤（`#9` 至 `#12`）均完成
- 镜像推送：`[Build] finished` + `[Push] finished`，镜像已成功推送到 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`

失败仅发生在构建完成后的 CI 工具链内部——`eulerpublisher` 的 [Check] 阶段因 runner 缺少 `shunit2` 而无法执行容器自检。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境（运行 `eulerpublisher` 检查流程的节点）上安装 `shunit2` 测试框架。该框架是 `common_funs.sh` 执行容器功能检查的依赖项，缺失导致所有需要容器自检的 PR 均会失败。此为 CI 基础设施问题，不需要修改任何 PR 中的代码文件。

## 需要进一步确认的点
- 确认 CI runner 环境中 `shunit2` 的预期安装路径（`common_funs.sh` 第 13 行 source 的路径）以及安装方式（系统包管理器安装或手动部署）。
- 确认该 CI runner（aarch64 架构节点）上的 `shunit2` 缺失是偶发（安装后又被移除）还是该节点从未安装过此依赖。如果是新 runner 节点，需要将其加入 CI 环境初始化流程。
