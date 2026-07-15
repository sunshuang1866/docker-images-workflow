# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式39（同类：CI工具依赖缺失）
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher, Check test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试工具 `eulerpublisher` 在执行 [Check] 阶段（容器启动后验证）时，其内置测试脚本 `common_funs.sh` 尝试加载 `shunit2`（Shell 单元测试框架），但该框架未安装在 CI runner 环境中，导致验证阶段失败。Docker 镜像构建（#7~#10）和推送（[Push]）均已成功完成，`Finished: FAILURE` 的根因是检查基础设施缺失依赖，而非镜像本身有问题。

### 与 PR 变更的关联
与 PR 代码变更无关。PR 仅新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，以及对应的 README.md、image-info.yml、meta.yml 更新。日志中 Docker 构建步骤（#7 下载 Go、#8 文件时间戳调整、#9 清理构建工具包、#10 WORKDIR）全部 `DONE`，镜像成功推送至 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64`。失败发生在 CI 自身的 [Check] 阶段（`eulerpublisher` 容器测试工具），与本次 PR 的 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 中）
在运行 `openEuler 24.03-LTS-SP4` 的 CI runner（aarch64）上安装 `shunit2` 包。`shunit2` 是 Shell 单元测试框架，需要预装在 CI 执行环境的系统路径中，供 `eulerpublisher` 的 `common_funs.sh` 脚本引用。可通过 `dnf install shunit2 -y` 或 `pip install shunit2` 安装。

### 方向 2（置信度: 低）
如果 `shunit2` 无法直接安装（包名可能因发行版不同而异），可检查其他 CI runner（如 24.03-lts-sp3 环境）上 `shunit2` 的安装方式，确保 SP4 runner 的测试环境包清单与已有稳定环境一致。

## 需要进一步确认的点
1. 确认 `shunit2` 在 24.03-LTS-SP4 aarch64 上的可用包名（`shunit2` 或 `shunit2-standalone` 等）。
2. 确认同仓库其他 SP4 镜像（如已有成功构建检出的 SP4 应用镜像）是否也依赖 `shunit2`，用于判断该问题是否为所有 SP4 runner 的系统性缺失。
3. 若仅本 PR 触发此问题而其他 SP4 检查正常，需进一步排查 runner 环境差异（如使用不同构建节点）。

## 修复验证要求
无。本次失败为 infra-error，与 PR 代码变更无关，code-fixer 无需对 Dockerfile 或元数据文件做任何修改。
