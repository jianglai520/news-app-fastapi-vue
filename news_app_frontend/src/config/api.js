/**
 * API配置文件
 * 包含API基础URL和AI问答功能所需的API参数
 */

// API基础URL配置
export const apiConfig = {
  // 末尾不要带斜杠：调用处已经写成 `${apiConfig.baseURL}/api/xxx`
  // 开发环境留空 → 请求走 Vite 代理（vite.config.js 把 /api 转发到 127.0.0.1:8000），无跨域问题
  // 打包部署时用 VITE_API_BASE_URL 指定后端地址，例如 https://api.example.com
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
}

export const aiChatConfig = {
  // OpenAI API地址
  apiEndpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
  
  // API Key (由开发人员指定)
  apiKey: '你自己的api',
  
  // 使用的模型
  model: 'qwen3-max-preview'
}
