// Voice API
import { API_BASE_URL } from '@/constants/api';

/**
 * Create a voice memory by uploading an audio file
 * Uses fetch directly for multipart/form-data support
 */
export const createVoiceMemory = async (
  audio: File, 
  _occurred_at?: string
): Promise<{
  id: number;
  user_id: string;
  content: string;
  summary: string | null;
  topics: string[] | null;
  entities: string[] | null;
  source: string;
  created_at: string;
  occurred_at: string | null;
}> => {
  const formData = new FormData();
  // @ts-ignore - File is compatible with Blob in React Native
  formData.append('audio', audio);
  
  const response = await fetch(`${API_BASE_URL}/memories/voice`, {
    method: 'POST',
    body: formData,
    headers: {
      'X-User-ID': 'dev-user',
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to create voice memory' }));
    throw new Error(error.detail || 'Failed to create voice memory');
  }
  
  return response.json();
};

export const voiceApi = {
  create: createVoiceMemory,
};

export default {
  create: createVoiceMemory,
};