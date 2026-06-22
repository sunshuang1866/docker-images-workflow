# 修复摘要

## 修复的问题
`groupadd: command not found` — openEuler 24.03-lts-sp3 基础镜像缺少 `shadow-utils` 包，导致构建时 `groupadd`/`useradd` 命令不可用。

## 修改的文件
- `Cloud/percona/8.4.8/24.03-lts-sp3/Dockerfile`: 在 `dnf install` 列表中添加 `shadow` 包

## 修复逻辑
CI 分析报告指出根因是 `openeuler:24.03-lts-sp3` 基础镜像默认不包含 `shadow-utils` 包，导致 Dockerfile 第 11 行的 `groupadd -r mysql && useradd -r -g mysql mysql` 因找不到命令而失败（exit code 127）。修复方式是在第 9-10 行的 `dnf install` 命令中添加 `shadow` 包（openEuler 中提供 `groupadd`/`useradd` 的包名），使其在执行到用户/组创建步骤前已可用。

## 潜在风险
无