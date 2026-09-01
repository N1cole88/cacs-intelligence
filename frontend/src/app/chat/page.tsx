"use client";
import { useState } from "react";
import { Send, FileText, User, Bot } from "lucide-react";
import { chat } from "@/lib/api";
import type { ChatMessage, SourceReference } from "@/types";

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Hello! I'm your CACS study assistant. Upload your study materials and ask me anything about the concepts." },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);
    try {
      const response = await chat(userMessage);
      setMessages((prev) => [...prev, { role: "assistant", content: response.response, sources: response.sources }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I encountered an error. Please try again." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b px-4 py-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-xl font-bold">Chat with your materials</h1>
          <p className="text-sm text-gray-600">Ask questions about CACS concepts</p>
        </div>
      </header>
      <main className="flex-1 max-w-4xl mx-auto w-full p-4 flex flex-col">
        <div className="flex-1 overflow-y-auto space-y-4 mb-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              {msg.role === "assistant" && <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center"><Bot className="w-5 h-5 text-green-600" /></div>}
              <div className={`max-w-[80%] rounded-lg p-3 ${msg.role === "user" ? "bg-blue-600 text-white" : "bg-white border"}`}>
                <p className="whitespace-pre-wrap">{msg.content}</p>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t text-sm">
                    <p className="font-semibold mb-2">Sources:</p>
                    {msg.sources.map((source, j) => (
                      <div key={j} className="text-xs mb-2">
                        <span className="font-medium">{source.document_title}</span>
                        <span className="text-gray-500"> (page {source.page_number})</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              {msg.role === "user" && <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center"><User className="w-5 h-5 text-blue-600" /></div>}
            </div>
          ))}
          {isLoading && <div className="flex gap-3"><div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center"><Bot className="w-5 h-5 text-green-600" /></div><div className="bg-white border rounded-lg p-3"><p className="text-gray-500">Thinking...</p></div></div>}
        </div>
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask a question..." className="flex-1 p-3 border rounded-lg" disabled={isLoading} />
          <button type="submit" disabled={!input.trim() || isLoading} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"><Send className="w-5 h-5" /></button>
        </form>
      </main>
    </div>
  );
}
