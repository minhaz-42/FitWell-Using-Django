Conversation system
===================

Design notes
------------

- Conversations are stored in the `Conversation` model (`core.models`).
- Each conversation has `last_read_at` (DateTime) used to compute `unread_count` on the API.
- The `conversation_list_api` supports pagination via `limit` and `offset` query params and returns the following fields per conversation:
  - `id`, `title`, `pinned`, `unread_count`, `last_message`, `last_message_type`, `last_message_timestamp`, `updated_at`, `message_count`

Client behavior
---------------

- When the client opens a conversation via `/api/conversations/<id>/`, the server sets `last_read_at` to now, effectively marking messages as read.
- When sending a message via `/api/v1/chat`, the server returns `conversation_id` and `conversation_title` which the client uses to update the sidebar and keep subsequent messages in the same conversation.

Notes for developers
--------------------
- If you change the default callable for generating `Conversation.id`, ensure it's serializable for Django migrations (avoid lambdas).
- To add unread counters client-side, read `unread_count` from the `conversation_list_api` response.
