import { FileText, MessageSquare, BarChart3, BookOpen } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">CACS Intelligence</h1>
          <p className="mt-1 text-gray-600">Your AI-powered learning companion</p>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <a href="/documents" className="p-6 bg-white rounded-lg border hover:shadow-md transition-shadow">
            <FileText className="h-10 w-10 text-blue-600 mb-4" />
            <h3 className="text-lg font-semibold">Documents</h3>
            <p className="text-sm text-gray-600 mt-1">Upload CACS study materials</p>
          </a>
          <a href="/chat" className="p-6 bg-white rounded-lg border hover:shadow-md transition-shadow">
            <MessageSquare className="h-10 w-10 text-green-600 mb-4" />
            <h3 className="text-lg font-semibold">Ask Questions</h3>
            <p className="text-sm text-gray-600 mt-1">Chat with your study materials</p>
          </a>
          <a href="/practice" className="p-6 bg-white rounded-lg border hover:shadow-md transition-shadow">
            <BookOpen className="h-10 w-10 text-purple-600 mb-4" />
            <h3 className="text-lg font-semibold">Practice</h3>
            <p className="text-sm text-gray-600 mt-1">Test your knowledge</p>
          </a>
          <a href="/progress" className="p-6 bg-white rounded-lg border hover:shadow-md transition-shadow">
            <BarChart3 className="h-10 w-10 text-orange-600 mb-4" />
            <h3 className="text-lg font-semibold">Progress</h3>
            <p className="text-sm text-gray-600 mt-1">Track your mastery</p>
          </a>
        </div>
        <div className="mt-12">
          <h2 className="text-xl font-semibold mb-4">Getting Started</h2>
          <div className="bg-white rounded-lg border p-6">
            <ol className="list-decimal list-inside space-y-2 text-gray-700">
              <li>Upload your CACS study materials (PDF)</li>
              <li>Wait for processing to complete</li>
              <li>Start chatting with your documents</li>
              <li>Track your progress as you learn</li>
            </ol>
          </div>
        </div>
      </main>
    </div>
  );
}
