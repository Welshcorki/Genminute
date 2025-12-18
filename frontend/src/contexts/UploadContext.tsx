/**
 * 전역 업로드 상태 관리 Context
 * - 페이지 이동 시에도 업로드 상태 유지
 * - 진행 중인 업로드 목록 관리
 * - 업로드 취소 기능
 */
import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { uploadFile } from '../services/upload';
import type { UploadProgress } from '../services/upload';

// 업로드 작업 상태
export interface UploadTask {
  id: string;
  fileName: string;
  title: string;
  progress: UploadProgress | null;
  status: 'uploading' | 'complete' | 'error';
  errorMessage?: string;
  meetingId?: string;
  abortController?: AbortController;
}

interface UploadContextType {
  activeTasks: UploadTask[];
  addUpload: (file: File, title: string, meetingDate?: string) => Promise<string | null>;
  removeTask: (id: string) => void;
  cancelTask: (id: string) => void;
  clearCompletedTasks: () => void;
}

const UploadContext = createContext<UploadContextType | null>(null);

export const UploadProvider = ({ children }: { children: ReactNode }) => {
  const [activeTasks, setActiveTasks] = useState<UploadTask[]>([]);

  // 작업 추가
  const addTask = useCallback((task: UploadTask) => {
    setActiveTasks(prev => [...prev, task]);
  }, []);

  // 작업 업데이트
  const updateTask = useCallback((id: string, updates: Partial<UploadTask>) => {
    setActiveTasks(prev =>
      prev.map(task => (task.id === id ? { ...task, ...updates } : task))
    );
  }, []);

  // 작업 제거
  const removeTask = useCallback((id: string) => {
    setActiveTasks(prev => prev.filter(task => task.id !== id));
  }, []);

  // 작업 취소
  const cancelTask = useCallback((id: string) => {
    setActiveTasks(prev => {
      const task = prev.find(t => t.id === id);
      if (task?.abortController) {
        task.abortController.abort();
      }
      return prev.filter(t => t.id !== id);
    });
  }, []);

  // 완료된 작업 모두 제거
  const clearCompletedTasks = useCallback(() => {
    setActiveTasks(prev => prev.filter(task => task.status === 'uploading'));
  }, []);

  // 업로드 시작 (전역 관리)
  const addUpload = useCallback(async (
    file: File,
    title: string,
    meetingDate?: string
  ): Promise<string | null> => {
    const taskId = `upload-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const abortController = new AbortController();

    // 초기 작업 추가
    const newTask: UploadTask = {
      id: taskId,
      fileName: file.name,
      title,
      progress: { step: 'upload', message: '업로드 준비 중...' },
      status: 'uploading',
      abortController,
    };
    addTask(newTask);

    return new Promise((resolve) => {
      uploadFile({
        file,
        title,
        meetingDate,
        onProgress: (progress) => {
          updateTask(taskId, { progress });
        },
        onError: (error) => {
          updateTask(taskId, {
            status: 'error',
            errorMessage: error,
            progress: { step: 'error', message: error },
          });
          resolve(null);
        },
        onComplete: (meetingId) => {
          updateTask(taskId, {
            status: 'complete',
            meetingId,
            progress: { step: 'complete', message: '완료!' },
          });
          resolve(meetingId);
        },
      }).catch(() => {
        // 에러는 onError에서 처리됨
      });
    });
  }, [addTask, updateTask]);

  return (
    <UploadContext.Provider
      value={{
        activeTasks,
        addUpload,
        removeTask,
        cancelTask,
        clearCompletedTasks,
      }}
    >
      {children}
    </UploadContext.Provider>
  );
};

export const useUpload = () => {
  const context = useContext(UploadContext);
  if (!context) {
    throw new Error('useUpload must be used within UploadProvider');
  }
  return context;
};

export default UploadContext;

