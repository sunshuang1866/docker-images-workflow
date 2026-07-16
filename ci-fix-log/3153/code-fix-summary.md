# 修复摘要

## 修复的问题
CI 基础设施（infra-error）：CI 工具 `eulerpublisher` 对根级 `README.md` 文件错误地执行了 appstore 发布规范路径校验，期望路径 `/README.md`（带前导 `/`）与 `git diff` 输出的 `README.md`（不带前导 `/`）不匹配，导致校验失败。`README.md` 为仓库根级文档，不隶属于任何应用镜像目录，本不应纳入 appstore 镜像发布规范检查范围。

## 修改的文件
无代码修改。`README.md` 的内容变更（更新可用基础镜像标签列表）是合法的纯文档变更，无需修改。

## 修复逻辑
此失败属于 CI 基础设施误报，根因在 `eulerpublisher/update/container/app/update.py` 的路径解析逻辑中缺少对根级文档文件（不隶属于任何 `{image-version}/{os-version}/Dockerfile` 结构的文件）的过滤或豁免机制，以及对路径格式前导 `/` 的统一标准化处理。修复应在 CI 工具侧进行，不在 PR 源码变更范围内。当前 PR 仅修改了 `README.md`（和 `README.en.md`），内容正确，无需代码层面改动。

## 潜在风险
无。`README.md` 内容变更仅为文档更新，不涉及任何构建逻辑、镜像配置或版本依赖。