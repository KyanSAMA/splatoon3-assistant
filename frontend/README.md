# 前端层

该目录用于承载基于 Vue 或 React 的 Web 前端。前端的职责是以图形化方式展示位于 `../data` 的静态 JSON 语料，并通过后端暴露的 API 访问 SQLite 数据。

## 推荐目录结构

```
frontend/
├── README.md            # 当前说明
├── package.json         # npm 依赖定义（创建工程后自动生成）
├── src/                 # 应用源码
├── public/              # 静态资源
└── vite.config.ts       # 建议使用 Vite 作为脚手架
```

你可以根据 prefer 的技术栈选择脚手架：

- **Vue 3 + Vite**
  ```bash
  cd frontend
  npm create vite@latest splatoon-dashboard -- --template vue-ts
  cd splatoon-dashboard
  npm install
  npm run dev
  ```
- **React + Vite**
  ```bash
  cd frontend
  npm create vite@latest splatoon-dashboard -- --template react-ts
  cd splatoon-dashboard
  npm install
  npm run dev
  ```

## 与数据/后端交互

1. 所有静态 JSON（`../data/json`）和图片（`../data/images`）可直接通过 `fetch` 读取，也可以由后端提供 API 封装。
2. 若需要实时数据，请调用后端（位于 `../backend`）暴露的接口——建议通过 REST/GraphQL 对接 SQLite。
3. 联调时可在前端项目根目录创建 `.env`，设定 `VITE_API_BASE=http://localhost:8000` 等变量。

## 下一步

- 依据设计稿搭建 UI 组件库（Element Plus、Naive UI、AntD 等均可）。
- 将 JSON/SQLite 数据映射为可视化页面（例如武器图鉴、打工日程、战绩看板）。
- 配合 CI/CD，将 `frontend` 的构建产物部署到静态主机或与后端同源发布。
