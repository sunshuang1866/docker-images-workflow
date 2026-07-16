# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: `^M`, `bad interpreter`, `No such file or directory`, shebang

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher CI 工具包内置的测试脚本）
- 失败原因: `bwa_test.sh` 文件含有 Windows 风格行结束符（CRLF），导致 shebang 行 `#!/bin/sh` 末尾附带了不可见的回车符 `\r`（即 `^M`），Linux 内核将解释器路径解析为 `/bin/sh\r`，该路径不存在，因此报 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
PR 变更（新增 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及配套元数据文件）**与本次失败无关**。日志明确显示：
- Docker 镜像构建成功（`#7 DONE 199.0s`）
- 镜像推送成功（`#8 DONE 8.4s`、`[Push] finished`）
- 失败仅发生在 CI [Check] 阶段，即 `eulerpublisher` 工具调用其内置的 `bwa_test.sh` 对构建好的镜像进行验证时。测试脚本自身的 CRLF 行尾问题导致脚本无法执行。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施修复：将 `eulerpublisher` 包中的 `bwa_test.sh` 行结束符从 CRLF（Windows 格式）转换为 LF（Unix 格式）。可使用 `dos2unix` 或在编辑器中设置行尾为 LF 后重新打包/部署该文件。

## 需要进一步确认的点

1. 确认 `bwa_test.sh` 是何时引入 CRLF 行尾的——是 `eulerpublisher` 包的某次更新引入，还是该文件始终存在此问题（此前 bwa 仅支持 22.03-lts-sp3，24.03-lts-sp4 是首次触发 bwa 测试路径的新 OS 版本）。
2. 检查 `eulerpublisher/tests/container/app/` 目录下其他 `*_test.sh` 脚本是否也存在同样的 CRLF 问题，以防止同类失败再次发生。
