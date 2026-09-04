"use client";
import { useState, useEffect } from "react";
import { fetchNews, refreshNews, calculateRelevance, getUserTopics, NewsArticle } from "@/lib/news-api";
import { NewsCard } from "@/components/NewsCard";
import { RefreshCw, Filter, LayoutGrid, List, BarChart3, BookOpen } from "lucide-react";

const TOPICS = [
  "All",
  "Anti-Money Laundering",
  "Know Your Customer",
  "Combating Terrorist Financing",
  "Financial Crimes",
  "Sanctions",
  "Crypto/FinTech Regulation",
  "FATF Guidelines",
  "Bank Secrecy Act",
];

const SOURCES = ["all", "newsapi", "gnews", "rss"];
const VIEWS = [
  { id: "timeline", label: "Timeline", icon: List },
  { id: "relevance", label: "Relevance", icon: BarChart3 },
  { id: "category", label: "Category", icon: LayoutGrid },
];

export default function NewsPage() {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [userTopics, setUserTopics] = useState<string[]>([]);

  // Filters
  const [view, setView] = useState("timeline");
  const [source, setSource] = useState("all");
  const [topic, setTopic] = useState("All");

  // Load user topics and calculate relevance on mount
  useEffect(() => {
    const initNews = async () => {
      try {
        // Get user topics from documents
        const { topics } = await getUserTopics();
        setUserTopics(topics);

        // Calculate relevance based on user's documents
        await calculateRelevance();
      } catch (err) {
        console.error("Failed to initialize news:", err);
      }
    };
    initNews();
  }, []);

  const loadNews = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { view };
      if (source !== "all") params.source = source;
      if (topic !== "All") params.topic = topic;
      const data = await fetchNews(params);
      setArticles(data.articles);
      setLastUpdated(new Date().toLocaleString());
    } catch (err) {
      console.error("Failed to load news:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshNews();
      // Recalculate relevance after refresh
      await calculateRelevance();
      await loadNews();
    } catch (err) {
      console.error("Failed to refresh news:", err);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadNews();
  }, [view, source, topic]);

  // Group by category for category view
  const groupedArticles = view === "category"
    ? (() => {
        const grouped = articles.reduce((acc, article) => {
          article.topics.forEach((t) => {
            if (!acc[t]) acc[t] = [];
            acc[t].push(article);
          });
          return acc;
        }, {} as Record<string, NewsArticle[]>);

        // Sort categories alphabetically, and articles by date (newest first)
        const sorted: Record<string, NewsArticle[]> = {};
        Object.keys(grouped).sort().forEach((key) => {
          sorted[key] = grouped[key].sort(
            (a, b) => new Date(b.published_at).getTime() - new Date(a.published_at).getTime()
          );
        });
        return sorted;
      })()
    : null;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-4 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">Financial News</h1>
            {lastUpdated && (
              <p className="text-sm text-gray-500">Last updated: {lastUpdated}</p>
            )}
          </div>
          <div className="flex items-center gap-4">
            {userTopics.length > 0 && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <BookOpen className="w-4 h-4" />
                <span>Your topics:</span>
                <div className="flex gap-1">
                  {userTopics.slice(0, 3).map((topic) => (
                    <span key={topic} className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-xs">
                      {topic}
                    </span>
                  ))}
                  {userTopics.length > 3 && (
                    <span className="text-xs text-gray-500">+{userTopics.length - 3}</span>
                  )}
                </div>
              </div>
            )}
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-4">
        {/* Filters */}
        <div className="bg-white rounded-lg border p-4 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            {/* View Toggle */}
            <div className="flex items-center gap-1 bg-gray-100 p-1 rounded-lg">
              {VIEWS.map((v) => (
                <button
                  key={v.id}
                  onClick={() => setView(v.id)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors ${
                    view === v.id
                      ? "bg-white shadow text-gray-900"
                      : "text-gray-600 hover:text-gray-900"
                  }`}
                >
                  <v.icon className="w-4 h-4" />
                  {v.label}
                </button>
              ))}
            </div>

            {/* Source Filter */}
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="border rounded-md px-3 py-1.5 text-sm"
              >
                {SOURCES.map((s) => (
                  <option key={s} value={s}>
                    {s === "all" ? "All Sources" : s.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>

            {/* Topic Filter */}
            <select
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="border rounded-md px-3 py-1.5 text-sm"
            >
              {TOPICS.map((t) => (
                <option key={t} value={t}>
                  {t === "All" ? "All Topics" : t}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* News Content */}
        {loading ? (
          <div className="text-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin text-gray-400 mx-auto" />
            <p className="mt-2 text-gray-500">Loading news...</p>
          </div>
        ) : view === "category" && groupedArticles ? (
          /* Category View */
          <div className="space-y-8">
            {Object.entries(groupedArticles).map(([category, cats]) => (
              <div key={category}>
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  {category}
                  <span className="text-sm bg-gray-200 px-2 py-0.5 rounded-full">
                    {cats.length}
                  </span>
                </h2>
                <div className="grid md:grid-cols-2 gap-4">
                  {cats.slice(0, 6).map((article) => (
                    <NewsCard key={article.id} article={article} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* Timeline / Relevance View */
          <div className="grid md:grid-cols-2 gap-4">
            {articles.map((article) => (
              <NewsCard
                key={article.id}
                article={article}
                showRelevance={view === "relevance"}
              />
            ))}
          </div>
        )}

        {!loading && articles.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No news articles found. Try adjusting your filters or refresh.
          </div>
        )}
      </main>
    </div>
  );
}
