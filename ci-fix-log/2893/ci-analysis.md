# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: CI runner 环境（`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13）
- 失败原因: Docker 镜像构建和推送均已成功完成（[Build] finished、[Push] finished，422/422 编译目标全部通过，镜像成功推送到 docker.io），但在 CI [Check] 后处理验证阶段，测试脚本 `common_funs.sh` 尝试用 `.` source 引入 `shunit2` shell 测试框架（`shunit2`），该框架未安装在 CI runner 环境中，导致 `source` 命令报 "file not found"。

### 与 PR 变更的关联
**与 PR 无关**。PR 变更为新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml），属于标准的新镜像添加操作。Dockerfile 自身构建完全成功：
- meson 编译阶段完成（422/422 目标全部编译并安装）
- Docker 镜像分层构建全部完成（#9 至 #13 全部 DONE）
- 镜像成功推送至 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`

失败发生在 CI 流水线本身的容器启动验证步骤，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` shell 测试框架，使 `common_funs.sh` 脚本中的 `. shunit2` source 命令能够正确找到该文件。具体而言，需要在执行 `eulerpublisher` 的 CI 节点上预先安装 `shunit2` 包（如通过 `yum install shunit2` 或类似方式）。这不是 PR 代码层面的问题，无需修改 Dockerfile 或任何仓库文件。

## 需要进一步确认的点
1. 确认 CI runner 环境是否应预装 `shunit2`，以及该依赖是在哪个环节被遗漏的（runner 镜像更新、环境变更等）。
2. 检查 `common_funs.sh` 中 `shunit2` 的 source 路径是否正确，是否应指向 CI runner 上 `shunit2` 的实际安装路径。
3. 验证其他镜像的 CI [Check] 步骤是否也有同样的 `shunit2` 缺失问题——若是，说明是 CI 环境级别的回归。
