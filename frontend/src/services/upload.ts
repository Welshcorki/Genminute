import api from './api';

export interface UploadProgress {
  step: 'upload' | 'validation' | 'conversion' | 'stt' | 'chunking' | 'mindmap' | 'complete' | 'error';
  message: string;
  icon?: string;
  redirect?: string;
}

export interface UploadOptions {
  file: File;
  title: string;
  meetingDate?: string;
  onProgress?: (progress: UploadProgress) => void;
  onError?: (error: string) => void;
  onComplete?: (meetingId: string) => void;
}

/**
 * 파일 업로드 및 SSE 스트림 처리
 */
export const uploadFile = async (options: UploadOptions): Promise<void> => {
  const { file, title, meetingDate, onProgress, onError, onComplete } = options;

  // FormData 생성
  const formData = new FormData();
  formData.append('audio_file', file);
  formData.append('title', title);
  if (meetingDate) {
    formData.append('meeting_date', meetingDate);
  }

  try {
    // SSE 스트림으로 업로드 요청
    const response = await fetch(`${api.defaults.baseURL}/upload`, {
      method: 'POST',
      body: formData,
      credentials: 'include', // 쿠키 포함
    });

    if (!response.ok || !response.headers.get('content-type')?.includes('text/event-stream')) {
      throw new Error('서버에서 올바른 응답을 받지 못했습니다.');
    }

    // ReadableStream을 읽고 SSE 메시지 파싱
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('응답 스트림을 읽을 수 없습니다.');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || ''; // 마지막 불완전한 줄은 buffer에 유지

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data: UploadProgress = JSON.parse(line.substring(6));
            
            if (data.step === 'error') {
              onError?.(data.message || '업로드 중 오류가 발생했습니다.');
              return;
            }

            if (data.step === 'complete') {
              // redirect URL에서 meeting_id 추출
              const meetingIdMatch = data.redirect?.match(/\/view\/([^\/]+)/);
              const meetingId = meetingIdMatch ? meetingIdMatch[1] : '';
              onComplete?.(meetingId);
              return;
            }

            onProgress?.(data);
          } catch (parseError) {
            console.error('SSE 메시지 파싱 오류:', parseError);
          }
        }
      }
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '서버와 통신 중 오류가 발생했습니다.';
    onError?.(errorMessage);
    throw error;
  }
};

