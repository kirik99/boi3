## Packages
react-markdown | Rendering markdown in chat responses
framer-motion | Smooth animations for messages and UI elements
lucide-react | Beautiful icons
clsx | Utility for constructing className strings conditionally
tailwind-merge | Utility for merging Tailwind classes safely

## Notes
The backend provides a chat integration with separate routes for text/audio.
We will build a chat interface that supports text and potentially images/audio if extended, but starting with the provided schema.
The prompt mentions `messages` table with `imageUrl`, but the installed integration `shared/models/chat.ts` has `conversations` and `messages`.
I will adapt to use the `conversations` + `messages` structure from the installed integration as it's the actual code on disk.
The integration allows for text-based chat.
Audio capabilities are available in `client/replit_integrations/audio` if needed, but I will focus on a high-quality text chat first as requested by the schema in the prompt, adapting it to the conversation model.
