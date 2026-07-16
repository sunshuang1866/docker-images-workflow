# 修复摘要

## 修复的问题
README.md 中基础镜像存放路径 `Base/openeuler/Dockerfile` 缺少前导 `/`，不符合 CI appstore 发布规范校验器对路径格式的要求（路径必须以 `/` 开头）。

## 修改的文件
- `README.md`: 将第48行 `` `Base/openeuler/Dockerfile` `` 改为 `` `/Base/openeuler/Dockerfile` ``
- `README.en.md`: 未在 `pr.changed_files` 列表中，无法修改（该文件可能也存在同样问题，建议单独处理）

## 修复逻辑
CI 发布规范校验脚本 `eulerpublisher/update/container/app/update.py` 对 README.md 进行全量路径格式校验，要求所有路径引用以 `/` 开头。README.md 第48行"存放路径"下的 `Base/openeuler/Dockerfile` 未以 `/` 开头，触发了 `[Path Error] The expected path should be /README.md` 校验失败。添加前导 `/` 使其符合校验器期望的绝对路径格式。

## 潜在风险
无。该路径在 README 中仅作为文档描述用途（指示基础镜像 Dockerfile 的存放位置），添加前导 `/` 不影响实际文件路径解析，且使其语义更加明确（从仓库根目录算起）。