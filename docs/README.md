# Yomii 文档索引

`docs/` 现在按两层来维护：

- 核心文档：当前开发、运行、对接还会持续使用
- 归档文档：历史过程、阶段性整理、一次性重构记录

## 一、核心文档

这些文件需要继续维护，默认优先看这一组。

### 项目材料

- [项目总览](./00-PROJECT/PROJECT_OVERVIEW.md)

### 启动与接入

- [快速开始](./01-GETTING_STARTED/QUICK_START.md)
- [API 参考](./02-REFERENCE/API_REFERENCE.md)
- [数据库设计](./DATABASE_DESIGN.md)

### 开发维护

- [开发指南](./03-DEVELOPMENT/DEVELOPER_GUIDE.md)

## 二、归档文档

这些文件不再作为主入口维护，统一压缩为一份归档摘要：

- [历史归档摘要](./90-ARCHIVE/ARCHIVE_NOTES.md)

## 建议阅读顺序

1. 新接手项目：先看 [根 README](../README.md)
2. 要跑起来：看 [快速开始](./01-GETTING_STARTED/QUICK_START.md)
3. 要对接接口：看 [API 参考](./02-REFERENCE/API_REFERENCE.md)
4. 要改库表或理解双数据库：看 [数据库设计](./DATABASE_DESIGN.md)
5. 要改实现：看 [开发指南](./03-DEVELOPMENT/DEVELOPER_GUIDE.md)
6. 只有在追溯历史决策时，再进入 `90-ARCHIVE`
