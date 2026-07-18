# 修复摘要

## 修复的问题
本次 CI 失败为 **infra-error**（CI 基础设施问题），无需对源代码进行任何修改。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出：该 PR (#3153) 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（更新基础镜像可用 tag 列表），属于纯文档维护。CI 的 `eulerpublisher` 工具在执行 appstore 发布规范校验时，对根目录文件 `README.md` 执行路径格式比对，将相对路径形式 `README.md` 与期望的绝对路径形式 `/README.md` 判定为不匹配，从而报告 `[Path Error]`。这是 `eulerpublisher` CI 工具自身的路径规范化缺陷，属于 CI 基础设施层面的误报。

根据修复原则，**infra-error 不应通过修改源代码来绕过**，强行修改 PR 涉及的文件无法解决 CI 工具内部的路径校验缺陷。该问题应在 CI 工具 `eulerpublisher/update/container/app/update.py` 中修复，将仓库根目录的非应用镜像文件（如 `README.md`）排除在 appstore 规范校验范围之外，而非在本次 PR 的源代码中处理。

## 潜在风险
无（未对源代码做任何修改）