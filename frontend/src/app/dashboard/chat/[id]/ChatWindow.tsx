import { ChatMessage } from '@/components/chatbot/ChatMessage';

{messages.map((message, index) => (
  <ChatMessage
    key={index}
    message={message}
    userName={userName}
    botName={chatbot?.name || 'Assistant'}
  />
))} 