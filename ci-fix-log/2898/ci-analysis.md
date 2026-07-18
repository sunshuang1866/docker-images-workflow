# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI检查缺少shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher, Check, test failed

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
- 失败位置: CI runner 宿主机 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 在 `[Check]` 阶段执行容器镜像健康检查测试时，宿主机的 `common_funs.sh` 脚本第 13 行尝试加载 `shunit2`（Shell 单元测试框架），但该工具在 CI runner 上未安装/不可用。

### 与 PR 变更的关联
**与 PR 无关。** Docker 镜像构建和推送均已成功完成：
- `#7` 下载并解压 Go 1.25.6 二进制包 → DONE 67.8s
- `#8` touch 文件、创建符号链接 → DONE 40.5s
- `#9` 创建 GOPATH、卸载构建工具 → DONE 1.5s
- `#10` WORKDIR → DONE 0.0s
- `#11` 导出镜像并推送至 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64` → DONE 41.9s
- `[Build]` 和 `[Push]` 均输出 `finished`

失败仅发生在构建完成后的 `[Check]` 阶段，该阶段由 CI 编排工具 `eulerpublisher` 的测试框架执行，因 runner 环境缺少 `shunit2` 而崩溃，与 PR 新增的 Dockerfile、README.md、image-info.yml、meta.yml 文件内容均无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner（aarch64 构建节点）上安装 `shunit2` Shell 测试框架包。`shunit2` 通常可通过包管理器安装（如 `dnf install shunit2`）或从源码部署。安装后重新触发构建，`[Check]` 阶段应能正常执行。

### 方向 2（置信度: 低）
若 `shunit2` 实际已安装但 `$PATH` 未包含其位置，检查 `common_funs.sh` 中对 `shunit2` 的引用方式（`source` 路径或 `PATH` 依赖），确认路径配置是否正确。

## 需要进一步确认的点
- `shunit2` 在 aarch64 CI runner 上是否已安装（`which shunit2` 或 `rpm -qa | grep shunit2`）
- 同一 runner 上其他镜像（如 `go:1.25.6-oe2403sp3`）的 `[Check]` 阶段是否也会失败（用于确认这是新引入的 infra 问题还是近期环境退化）
