"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { sendChat } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import type { ChatMessage } from "@/types";

export default function ChatPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [alertNotice, setAlertNotice] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const question = input.trim();
    if (!question || loading) return;

    // 立即显示用户消息
    const userMsg: ChatMessage = {
      timestamp: new Date().toLocaleString("zh-CN"),
      question,
      answer: "",
      topic_tags: [],
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setAlertNotice(null);

    try {
      const res = await sendChat(user?.user_id || "", question);
      const aiMsg: ChatMessage = {
        timestamp: res.timestamp,
        question,
        answer: res.answer,
        topic_tags: res.topic_tags,
      };
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = aiMsg;
        return updated;
      });
      if (res.alert_triggered) {
        setAlertNotice("⚠️ 检测到健康预警，已通知关联人。请前往预警中心查看详情。");
      }
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          answer: "抱歉，暂时无法回答，请稍后再试。",
        };
        return updated;
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex h-[calc(100vh-3rem)] max-w-3xl flex-col">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900">💬 健康问答助手</h1>
        <p className="mt-1 text-sm text-gray-500">
          有什么不舒服随时问我，我会用简单的话给您解释
        </p>
      </div>

      {/* 预警提示 */}
      {alertNotice && (
        <div className="mb-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {alertNotice}
        </div>
      )}

      {/* 消息区 */}
      <div className="flex-1 overflow-y-auto rounded-xl border border-gray-200 bg-gray-50 p-4">
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center text-gray-400">
            <div className="text-center">
              <p className="text-4xl mb-3">👋</p>
              <p className="text-lg">您好！有什么不舒服可以问我</p>
              <p className="text-sm mt-1">比如：&ldquo;头晕是怎么回事？&rdquo;&ldquo;血压高要注意什么？&rdquo;</p>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className="mb-4">
            {/* 用户消息 */}
            <div className="flex justify-end">
              <div className="max-w-[80%] rounded-2xl rounded-br-md bg-primary px-4 py-3 text-base text-white">
                {msg.question}
              </div>
            </div>
            {/* AI 回答 */}
            {msg.answer && (
              <div className="mt-2 flex justify-start">
                <div className="max-w-[85%] rounded-2xl rounded-bl-md bg-white px-4 py-3 text-base text-gray-800 shadow-sm border border-gray-100">
                  <div className="prose prose-sm max-w-none prose-p:my-1">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.answer}
                    </ReactMarkdown>
                  </div>
                  {msg.topic_tags.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {msg.topic_tags.map((tag) => (
                        <span
                          key={tag}
                          className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-bl-md bg-white px-4 py-3 text-gray-400 shadow-sm border border-gray-100">
              <span className="animate-pulse">正在思考中...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* 输入区 */}
      <div className="mt-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          placeholder="请描述您的不舒服..."
          className="flex-1 rounded-xl border border-gray-300 px-4 py-3 text-base focus:border-primary focus:ring-1 focus:ring-primary"
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="rounded-xl bg-primary px-6 py-3 text-base font-semibold text-white transition-colors hover:bg-primary-dark disabled:opacity-50"
        >
          发送
        </button>
      </div>
    </div>
  );
}
