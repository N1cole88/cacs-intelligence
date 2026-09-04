const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface NewsArticle {
  id: string;
  title: string;
  content: string;
  summary: string | null;
  url: string;
  image_url: string | null;
  source: string;
  source_name: string;
  published_at: string;
  topics: string[];
  relevance_score: number;
  created_at: string;
}

export interface NewsListResponse {
  articles: NewsArticle[];
  total: number;
}

export interface NewsSource {
  source: string;
  name: string;
  count: number;
}

export async function fetchNews(params: {
  source?: string;
  topic?: string;
  view?: string;
  limit?: number;
}): Promise<NewsListResponse> {
  const searchParams = new URLSearchParams();
  if (params.source) searchParams.set("source", params.source);
  if (params.topic) searchParams.set("topic", params.topic);
  if (params.view) searchParams.set("view", params.view);
  if (params.limit) searchParams.set("limit", params.limit.toString());

  const res = await fetch(`${API_URL}/api/news?${searchParams}`);
  if (!res.ok) throw new Error("Failed to fetch news");
  return res.json();
}

export async function refreshNews(): Promise<{ articles_fetched: number }> {
  const res = await fetch(`${API_URL}/api/news/refresh`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to refresh news");
  return res.json();
}

export async function getNewsSources(): Promise<NewsSource[]> {
  const res = await fetch(`${API_URL}/api/news/sources/list`);
  if (!res.ok) throw new Error("Failed to fetch sources");
  return res.json();
}
