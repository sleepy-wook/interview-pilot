"use client";

import type { ChatMessage as ChatMessageType } from "@/lib/types";
import { PERSONA_CONFIG, QUALITY_CONFIG } from "@/lib/constants";

interface Props {
  message: ChatMessageType;
}

export default function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";
  const persona = message.persona;
  const pConfig = persona ? PERSONA_CONFIG[persona] : null;
  const quality = message.analysis?.quality;
  const qConfig = quality ? QUALITY_CONFIG[quality] : null;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[75%] ${isUser ? "order-1" : "order-2"}`}
      >
        {/* Persona label */}
        {!isUser && pConfig && (
          <div className="flex items-center gap-1.5 mb-1">
            <span className="text-base">{pConfig.icon}</span>
            <span
              className="text-xs font-medium"
              style={{ color: pConfig.color }}
            >
              {pConfig.label}
            </span>
            {message.topic && (
              <span className="text-xs text-gray-400">
                &middot; {message.topic}
              </span>
            )}
          </div>
        )}

        {/* Message bubble */}
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? "bg-blue-600 text-white rounded-br-md"
              : "border rounded-bl-md"
          }`}
          style={
            !isUser && pConfig
              ? {
                  backgroundColor: pConfig.bgColor,
                  borderColor: pConfig.borderColor,
                  color: "#1f2937",
                }
              : undefined
          }
        >
          {message.text}
        </div>

        {/* Analysis badge (for user answers) */}
        {isUser && qConfig && (
          <div className="flex items-center justify-end gap-2 mt-1">
            <span
              className="text-xs px-2 py-0.5 rounded-full font-medium"
              style={{ backgroundColor: qConfig.bgColor, color: qConfig.color }}
            >
              {qConfig.label}
            </span>
            {message.analysis && (
              <span className="text-xs text-gray-400">
                Confidence: {message.analysis.confidence_score}%
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
