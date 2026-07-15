# 修复摘要

## 修复的问题
Docker 构建失败：`COPY entrypoint.sh tap2json.py /` 引用的两个文件在 `24.03-lts-sp4` 目录中缺失，导致 BuildKit 找不到文件。

## 修改的文件
- `Others/kselftests-virtme/1.27/24.03-lts-sp4/Dockerfile`: 将 `COPY entrypoint.sh tap2json.py /` 替换为 RUN heredoc 方式将两个脚本的内容内联写入到镜像中，并添加 `chmod +x` 确保可执行。

## 修复逻辑
PR #2901 新增了 Dockerfile，其中 `COPY entrypoint.sh tap2json.py /` 引用了两个辅助脚本，但作者未将它们一起提交到新目录。受限于只能修改 `pr.changed_files` 中的文件且不能新增文件，采用在 Dockerfile 中通过 heredoc 内联脚本内容的方式替代 COPY 指令。两个脚本的内容与 `22.03-lts-sp4` 目录中的完全相同（该镜像在两个 openEuler 版本间兼容，无需差异化修改）。

## 潜在风险
无。两个脚本的内容与已在生产环境中工作的 `22.03-lts-sp4` 目录完全一致，功能行为不变。