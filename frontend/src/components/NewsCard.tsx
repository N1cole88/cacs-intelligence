import { NewsArticle } from "@/lib/news-api";
import { ExternalLink, Clock, Newspaper } from "lucide-react";

interface NewsCardProps {
  article: NewsArticle;
  showRelevance?: boolean;
}

export function NewsCard({ article, showRelevance = false }: NewsCardProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <div className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-lg line-clamp-2">
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-blue-600"
          >
            {article.title}
          </a>
        </h3>
        {showRelevance && (
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
            {Math.round(article.relevance_score * 100)}% match
          </span>
        )}
      </div>

      <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
        <span className="flex items-center gap-1">
          <Newspaper className="w-4 h-4" />
          {article.source_name}
        </span>
        <span className="flex items-center gap-1">
          <Clock className="w-4 h-4" />
          {formatDate(article.published_at)}
        </span>
      </div>

      {article.summary && (
        <p className="mt-3 text-gray-600 line-clamp-3">{article.summary}</p>
      )}

      {article.topics.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {article.topics.map((topic) => (
            <span
              key={topic}
              className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded"
            >
              {topic}
            </span>
          ))}
        </div>
      )}

      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-3 inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
      >
        Read More <ExternalLink className="w-4 h-4" />
      </a>
    </div>
  );
}
