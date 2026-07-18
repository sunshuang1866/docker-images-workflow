# 修复摘要

## 修复的问题
无需代码修复。CI 失败属于基础设施问题（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 构建在 `Dockerfile:6`（`RUN dnf install -y ...`）步骤失败，原因是 openEuler 24.03-LTS-SP4 软件仓库服务器在通过 HTTP/2 传输 RPM 包（尤其是 `gcc-c++` 等大文件）时，间歇性返回 `Curl error (92): Stream error in the HTTP/2 framing layer`，导致 `gcc-c++` 在所有镜像源重试后仍无法下载成功。PR #2980 新增的 Dockerfile 内容完全正常，无语法或逻辑错误。这是上游仓库 HTTP/2 服务端的瞬时协议兼容性问题，不是代码问题。建议重跑 CI 即可。

## 潜在风险
无