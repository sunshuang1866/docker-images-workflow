# 修复摘要

## 修复的问题
Maven 3.9.12 从 `dlcdn.apache.org` CDN 下架导致下载 404，将下载源替换为 Apache 归档站。

## 修改的文件
- `Others/spring-framework/7.0.3/24.03-lts-sp4/Dockerfile`: 第 12 行 Maven 下载 URL 从 `dlcdn.apache.org` 改为 `archive.apache.org/dist`

## 修复逻辑
分析报告指出 `dlcdn.apache.org` 只托管当前最新版 Maven，版本 3.9.12 已被移除导致 HTTP 404。采用置信度最高的修复方向：将下载源从 CDN (`dlcdn.apache.org`) 替换为 Apache 归档站 (`archive.apache.org/dist`)，归档站保留所有历史版本，Maven 版本号 3.9.12 保持不变，其余 URL 路径结构完全一致。

## 潜在风险
无。归档站长期保留历史版本，不受 CDN 清理策略影响。