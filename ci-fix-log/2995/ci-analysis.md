# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, CRLF, /bin/sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段，`/etc/eulerpublisher/tests/container/app/bwa_test.sh`
- 失败原因: eulerpublisher 软件包内 `bwa_test.sh` 测试脚本的 shebang 行（`#!/bin/sh`）带有 Windows 风格换行符（CRLF），导致系统内核将解释器路径解析为 `/bin/sh\r`（含回车符 `\r`），该文件实际不存在，shell 报 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
**无关**。PR 变更仅涉及 bwa 镜像的新 Dockerfile（`HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`）及相关元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像构建与推送均已成功完成（#7 步骤 `RUN yum -y install make gcc zlib-devel && ...` 正常退出、#8 导出和推送镜像成功），日志中 [Build] finished 和 [Push] finished 均有正常日志输出。失败发生在 CI 流水线的 [Check] 测试阶段，归因于 CI 基础设置中的 eulerpublisher Python 软件包自带的测试脚本 `bwa_test.sh` 存在 CRLF 换行符问题，与本次 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 中）
将 eulerpublisher 软件包中 `tests/container/app/bwa_test.sh`（以及同一测试目录下其他可能受影响的脚本）的换行符从 CRLF 转换为 LF。可通过 `dos2unix` 或 CI 流水线中在调用测试脚本前执行 `sed -i 's/\r$//'` 命令修复。

### 方向 2（置信度: 低）
若 eulerpublisher 是 CI 运行时通过 `git clone` 拉取到构建节点（日志中出现 `Cloning into 'eulerpublisher'...`），则可能是该 git 仓库中的源脚本即包含 CRLF 换行符。需从 eulerpublisher 上游仓库源头修正该脚本的换行符格式。

## 需要进一步确认的点
1. 确认 `bwa_test.sh` 文件的实际来源：是随 eulerpublisher Python 包通过 pip 安装到 `/etc/eulerpublisher/tests/` 的，还是在 CI 运行时从 eulerpublisher git 仓库动态生成的。
2. 检查 eulerpublisher 测试目录下其他 `*_test.sh` 脚本是否同样存在 CRLF 换行符问题（可能影响其他镜像的 CI 检查）。
3. 确认本次失败是否为偶发性问题（如 CI 节点环境异常）还是稳定复现。
