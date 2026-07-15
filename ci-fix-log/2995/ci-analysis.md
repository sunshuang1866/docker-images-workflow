# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, No such file or directory, ^M, /bin/sh^M

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 包内的测试脚本）
- 失败原因: bwa 测试脚本 `bwa_test.sh` 的 shebang 行 `#!/bin/sh` 末尾带有 Windows 风格的 CRLF 行尾符（`^M` 即 `\r`），导致系统尝试调用 `/bin/sh\r` 作为解释器，该路径不存在因而报 "bad interpreter"。

### 与 PR 变更的关联
**与 PR 无关。** PR 的变更仅限于新增 bwa 0.7.18 Dockerfile 及配套元数据文件（README.md、meta.yml、image-info.yml）。日志显示 Docker 镜像构建和推送均成功完成（`#8 DONE`、`[Build] finished`、`[Push] finished`），编译阶段仅有 GCC 无关紧要的 warning（`-Wunused-but-set-variable`）。失败发生在 CI 后处理阶段（`[Check]`），由 eulerpublisher 测试工具包内的测试脚本 `bwa_test.sh` 包含 CRLF 行尾符导致——这是 CI 运行环境中已安装的 eulerpublisher 包自身的问题。

## 修复方向

### 方向 1（置信度: 高）
CI 运行节点上 eulerpublisher 包中 `bwa_test.sh` 文件包含 Windows CRLF 行尾符。需要在 CI 运行节点上执行 `dos2unix` 或 `sed -i 's/\r$//'` 对该脚本去除回车符，重新以 LF 行尾保存。该修复与 PR 代码无关，应由 CI 基础设施维护者处理。

### 方向 2（置信度: 低）
若 eulerpublisher 包近期通过 Git/打包方式更新过，可能是打包或提交时该测试脚本未正确处理行尾。需要从源仓库重新拉取 eulerpublisher 包并确保 `.gitattributes` 中 `.sh` 文件标记为 `text eol=lf`。

## 需要进一步确认的点
1. eulerpublisher 包的 `bwa_test.sh` 是何时部署到该 CI 运行节点的——是否是最近一次 eulerpublisher 升级引入的 CRLF 问题。
2. 确认 eulerpublisher 源码仓库中 `tests/container/app/bwa_test.sh` 的行尾格式是否正确（应为 LF）。
3. 其他镜像（非 bwa）的 CI 运行是否也受此影响——如果是全局性问题，说明 eulerpublisher 包整体存在 CRLF 污染；如果仅 bwa_test.sh 有问题，说明是单个文件部署时的异常。
