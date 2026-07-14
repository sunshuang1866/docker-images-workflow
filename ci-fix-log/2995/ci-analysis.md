# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试脚本CRLF行尾
- 新模式症状关键词: ^M, bad interpreter, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:05,860 - INFO - [Build] finished
2026-07-10 11:58:05,860 - INFO - [Push] finished
2026-07-10 11:58:06,454 - INFO - [Check] checking ... bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 基础设施的 `eulerpublisher` 包内测试脚本 `bwa_test.sh`（路径 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`）
- 失败原因: `bwa_test.sh` 文件包含 Windows 风格的 CRLF（`\r\n`）行尾，其 shebang 行 `#!/bin/sh` 末尾带有回车符 `\r`（显示为 `^M`），导致 Linux shell 将解释器路径解析为 `/bin/sh\r`，该路径不存在，触发 "bad interpreter: No such file or directory" 错误。

### 与 PR 变更的关联
**无关。** PR 的 Docker 镜像构建和推送均已成功完成：
- 所有 17 个依赖包安装成功（gcc、make、zlib-devel 等）
- bwa 源码下载、编译（make clean && make）全部通过，仅有两个编译警告（未使用变量），无错误
- 最终链接生成 bwa 二进制文件成功
- 镜像导出与推送成功（`[Build] finished`、`[Push] finished`）

失败仅发生在 CI 框架的后置检查阶段（`[Check]`），根因是 CI 框架自身的 `bwa_test.sh` 文件存在 CRLF 行尾问题，与 PR 提交的 Dockerfile、README.md、image-info.yml、meta.yml 四个文件的变更完全无关。

## 修复方向

### 方向 1（置信度: 高）
由 CI/基础设施维护者对 `eulerpublisher` 包中的 `bwa_test.sh` 文件执行 `dos2unix` 转换，将 CRLF 行尾转换为 LF。修复命令示例：
```
dos2unix /usr/etc/eulerpublisher/tests/container/app/bwa_test.sh
```
或在 `eulerpublisher` 包的源码仓库中将该文件重新保存为 Unix 行尾格式并重新发布 pip 包。

## 需要进一步确认的点
- 该 `bwa_test.sh` 是否在 `eulerpublisher` 源码仓库中被误提交为 CRLF 格式，需要检查源码仓库中 `tests/container/app/bwa_test.sh` 的行尾格式。
- 同一 CI runner 上其他镜像的测试脚本是否也存在相同的 CRLF 问题（可通过 `file` 命令批量检查 `eulerpublisher/tests/container/app/` 目录下所有 `.sh` 文件的行尾格式）。
