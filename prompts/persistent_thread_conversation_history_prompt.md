# Fix ProofLens AI Conversation History — Persistent Thread-Based Chat

## Objective

Fix the existing ProofLens AI chat history behavior so that multiple questions and follow-up messages within the same conversation are stored under one persistent conversation thread, similar to ChatGPT's conversation history.

**Current problem:** Every question submitted by the user is creating a separate history entry. This makes the sidebar cluttered and prevents users from experiencing a continuous conversation.

**Expected behavior:** One conversation should contain multiple user questions and AI responses. A new history item should be created only when the user intentionally starts a new conversation.

## 1. Required Conversation Behavior

Implement the following behavior using the existing architecture:

1. When the user starts a new conversation and submits the first question, create one conversation/thread record.
2. Store the first question and its AI response inside that conversation.
3. When the user asks another question in the same active conversation, append the new user message and AI response to the existing conversation.
4. Continue appending all subsequent questions and answers to that same conversation until the user starts another conversation.
5. Do not create a separate sidebar history item for every question.
6. Display one history item per conversation, not one item per message or question.
7. When the user clicks an existing history item, restore the complete conversation.
