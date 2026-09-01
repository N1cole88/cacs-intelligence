export interface Document {
  id: string;
  title: string;
  file_path: string;
  file_size: number;
  status: string;
  error_message: string | null;
  uploaded_at: string;
  processed_at: string | null;
}

export interface SourceReference {
  document_title: string;
  page_number: number;
  content: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: SourceReference[];
}
