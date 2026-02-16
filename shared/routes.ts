
import { z } from 'zod';
import { insertMessageSchema, messages } from './schema';

export const errorSchemas = {
  validation: z.object({
    message: z.string(),
    field: z.string().optional(),
  }),
  internal: z.object({
    message: z.string(),
  }),
};

export const api = {
  messages: {
    list: {
      method: 'GET' as const,
      path: '/api/messages' as const,
      responses: {
        200: z.array(z.custom<typeof messages.$inferSelect>()),
      },
    },
    create: {
      method: 'POST' as const,
      path: '/api/messages' as const,
      input: z.object({
        content: z.string(),
        imageUrl: z.string().optional(),
      }),
      responses: {
        201: z.custom<typeof messages.$inferSelect>(),
        500: errorSchemas.internal,
      },
    },
    clear: {
      method: 'POST' as const,
      path: '/api/messages/clear' as const,
      responses: {
        204: z.void(),
      },
    },
  },
  upload: {
    create: {
      method: 'POST' as const,
      path: '/api/upload' as const,
      // Input is multipart/form-data, not validated here by Zod body parser usually
      responses: {
        201: z.object({ url: z.string() }),
        500: errorSchemas.internal,
      },
    },
  }
};

export function buildUrl(path: string, params?: Record<string, string | number>): string {
  let url = path;
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (url.includes(`:${key}`)) {
        url = url.replace(`:${key}`, String(value));
      }
    });
  }
  return url;
}
