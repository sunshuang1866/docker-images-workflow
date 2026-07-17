# 修复摘要

## 修复的问题
CI 基础设施缺陷（eulerpublisher 工具 bug），无需修改源码仓库中的任何代码。

## 修改的文件
无（无需修改 `README.md` 或任何其他源文件）。

## 修复逻辑

通过获取并审查 eulerpublisher 上游源码 `update/container/app/format.py`（`parse_image_prefix` 和 `_check_all_file_paths` 函数），定位到 CI 失败的根本原因是 **eulerpublisher 工具自身的路径构造 bug**：

1. PR #2790 修改了根目录 `README.md`，CI diff 阶段检测到该文件变更。
2. `format.py` 的 `check_report()` 判断 `README.md` 的文件类型 `README` 属于 `DOC_FILES_PATH_FORMAT` 定义的需要校验的类型。
3. `parse_image_prefix("README.md")` 因 `contents` 长度为 1（无目录层级），返回 `("", "")`。
4. `_check_all_file_paths()` 使用格式 `"{0}/README.md".format("")` 构造出正确路径 `/README.md`（**错误的绝对路径，指向文件系统根目录**，而非仓库根目录的相对路径）。
5. 由于 CI 工作目录下不存在 `/README.md`（该路径指向系统根目录），`os.path.exists("/README.md")` 返回 `False`，导致 `[Path Error] The expected path should be /README.md` 报错。

**修复方向**：此问题应在 `eulerpublisher/update/container/app/format.py` 中修复——当 `parse_image_prefix` 返回空前缀时（即文件位于仓库根层级，非应用镜像目录），应跳过 appstore 路径校验。这是 CI 团队需要介入修复的工具缺陷，源码仓库 `README.md` 的内容和路径均正确，无需任何修改。

## 潜在风险
无。此问题由 CI 工具对根层级文档文件的路径校验逻辑缺陷导致，不涉及源码仓库代码变更，不会影响任何功能。