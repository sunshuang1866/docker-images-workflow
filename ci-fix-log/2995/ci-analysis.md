# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, /bin/sh^M, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 包安装路径，非 PR 代码）
- 失败原因: `eulerpublisher` Python 包中自带的 `bwa_test.sh` 测试脚本使用 Windows 风格换行符（CRLF），导致 shebang `#!/bin/sh\r` 被内核解析为解释器路径 `/bin/sh\r`（带回车符），该路径不存在而报 `bad interpreter`

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了以下 4 个文件，均为标准镜像定义文件：
- `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新增，19 行）
- `HPC/bwa/README.md`（仅新增一行版本条目）
- `HPC/bwa/doc/image-info.yml`（新增版本条目，修复末尾换行）
- `HPC/bwa/meta.yml`（新增 sp4 版本条目）

Docker 镜像构建阶段完全成功——源码下载、gcc 编译、bwa 二进制产物的安装及依赖清理均正常完成，镜像已成功构建并推送至 registry。失败仅发生在 [Check] 阶段，该阶段调用 `eulerpublisher` 包预置的测试脚本 `bwa_test.sh`，该脚本因 CRLF 行尾问题无法被 Shell 执行。

## 修复方向

### 方向 1（置信度: 高）
修复 `eulerpublisher` 包中 `bwa_test.sh`（以及可能存在的其他测试脚本）的 CRLF 行尾问题。该文件位于 eulerpublisher 源码仓库的 `tests/container/app/` 目录下，需将其行尾从 CRLF 转换为 LF。可使用 `dos2unix` 或在编辑器中设置行尾为 LF 后重新提交。

## 需要进一步确认的点
- `bwa_test.sh` 文件在 eulerpublisher 源码仓库中的实际路径（日志显示为 pip 安装后的路径，需确认对应源码位置）
- eulerpublisher 包中是否还有其他测试脚本同样存在 CRLF 行尾问题（建议批量检查 `tests/` 目录下所有 `.sh` 文件）
