"use client";

import { useMutation } from "@tanstack/react-query";
import { Bot, Loader2, SendHorizontal, UserRound } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-provider";
import {
  type AIMessage,
  askDatasetQuestion,
} from "@/features/datasets/dataset-api";

type DatasetQuestionPanelProps = {
  datasetId: string | undefined;
};

export function DatasetQuestionPanel({ datasetId }: DatasetQuestionPanelProps) {
  const { session } = useAuth();
  const [question, setQuestion] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const accessToken = session?.access_token ?? "";

  const askMutation = useMutation({
    mutationFn: (nextQuestion: string) =>
      askDatasetQuestion({
        accessToken,
        datasetId: datasetId ?? "",
        question: nextQuestion,
        conversationId,
      }),
    onSuccess: (response) => {
      setConversationId(response.conversation.id);
      setMessages(response.messages);
      setQuestion("");
      toast.success("Answer generated.");
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "AI question failed.",
      );
    },
  });

  if (!datasetId) {
    return null;
  }

  const disabled = !accessToken || askMutation.isPending;

  return (
    <section className="mt-6 border-t border-white/10 pt-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-zinc-100">AI data Q&A</p>
          <p className="mt-1 text-xs text-zinc-500">
            Ask questions grounded in the parsed dataset profile and charts.
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-3">
          <Bot className="h-5 w-5 text-zinc-300" aria-hidden="true" />
        </div>
      </div>

      <div className="mt-4 min-h-52 space-y-3 rounded-3xl border border-white/10 bg-white/[0.03] p-4">
        {messages.length ? (
          messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))
        ) : (
          <div className="flex min-h-40 flex-col items-center justify-center text-center">
            <Bot className="h-6 w-6 text-zinc-400" aria-hidden="true" />
            <p className="mt-3 text-sm font-medium text-zinc-200">
              No questions yet.
            </p>
            <p className="mt-1 max-w-sm text-xs text-zinc-500">
              Try asking for trends, anomalies, missing data, correlations, or a
              short business summary.
            </p>
          </div>
        )}

        {askMutation.isPending ? (
          <div className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-zinc-400">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            Analyzing dataset context
          </div>
        ) : null}
      </div>

      <form
        className="mt-4 space-y-3"
        onSubmit={(event) => {
          event.preventDefault();
          const nextQuestion = question.trim();
          if (nextQuestion) {
            askMutation.mutate(nextQuestion);
          }
        }}
      >
        <textarea
          className="min-h-24 w-full resize-none rounded-3xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-zinc-100 outline-none transition placeholder:text-zinc-600 focus:border-white/25"
          disabled={disabled}
          maxLength={4000}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask about revenue trends, missing values, outliers, or what the charts imply..."
          value={question}
        />
        <Button
          className="w-full"
          disabled={disabled || !question.trim()}
          type="submit"
        >
          {askMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <SendHorizontal className="h-4 w-4" aria-hidden="true" />
          )}
          Ask AI
        </Button>
      </form>
    </section>
  );
}

function MessageBubble({ message }: { message: AIMessage }) {
  const isUser = message.role === "user";
  const Icon = isUser ? UserRound : Bot;

  return (
    <div
      className={[
        "flex gap-3 rounded-2xl border px-3 py-3",
        isUser
          ? "border-white/10 bg-white/[0.06]"
          : "border-emerald-400/15 bg-emerald-400/[0.06]",
      ].join(" ")}
    >
      <Icon
        className={
          isUser
            ? "mt-0.5 h-4 w-4 text-zinc-300"
            : "mt-0.5 h-4 w-4 text-emerald-200"
        }
        aria-hidden="true"
      />
      <div className="min-w-0 flex-1">
        <p className="text-xs uppercase tracking-wide text-zinc-500">
          {isUser ? "You" : (message.provider ?? "AI")}
        </p>
        <p className="mt-1 whitespace-pre-wrap break-words text-sm leading-6 text-zinc-200">
          {message.content}
        </p>
      </div>
    </div>
  );
}
