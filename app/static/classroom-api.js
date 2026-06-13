/**
 * 课堂伴侣云端API适配器
 * 所有业务数据通过后端API持久化，localStorage仅用于auth_token和UI偏好
 */
const ClassroomAPI = {
    baseURL: '/api/v1/classroom',
    currentSessionId: null,

    getToken: () => {
        return localStorage.getItem('auth_token') || '';
    },

    request: async (url, options = {}) => {
        const token = ClassroomAPI.getToken();
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };

        if (token) {
            headers.Authorization = `Bearer ${token}`;
        }

        const response = await fetch(url, {
            ...options,
            headers,
            credentials: 'same-origin'
        });

        if (!response.ok) {
            let message = `请求失败 (${response.status})`;
            try {
                const errorData = await response.json();
                message = errorData.message || errorData.detail || message;
            } catch (error) {
                // Keep fallback message.
            }
            throw new Error(message);
        }

        const data = await response.json();
        if (data.code !== 0) {
            throw new Error(data.message || '请求失败');
        }
        return data.data;
    },

    bootstrap: async () => {
        return await ClassroomAPI.request(`${ClassroomAPI.baseURL}/bootstrap`);
    },

    getClasses: async () => {
        return await ClassroomAPI.request(`${ClassroomAPI.baseURL}/classes`);
    },

    getStudents: async (classId) => {
        return await ClassroomAPI.request(`${ClassroomAPI.baseURL}/classes/${classId}/students`);
    },

    getQuestionBanks: async () => {
        return await ClassroomAPI.request(`${ClassroomAPI.baseURL}/question-banks`);
    },

    getQuestions: async (filters = {}) => {
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                params.append(key, value);
            }
        });
        return await ClassroomAPI.request(`${ClassroomAPI.baseURL}/questions?${params.toString()}`);
    },

    createSession: async (classId, title, mode = 'normal') => {
        const session = await ClassroomAPI.request(`${ClassroomAPI.baseURL}/sessions`, {
            method: 'POST',
            body: JSON.stringify({ class_id: classId, title, mode })
        });
        ClassroomAPI.currentSessionId = session.id;
        return session;
    },

    getSession: async (sessionId) => {
        return await ClassroomAPI.request(`${ClassroomAPI.baseURL}/sessions/${sessionId}`);
    },

    saveSessionState: async (sessionId, state, version = 1) => {
        return await ClassroomAPI.request(`${ClassroomAPI.baseURL}/sessions/${sessionId}/state`, {
            method: 'PATCH',
            body: JSON.stringify({ state, version })
        });
    },

    getSessionState: async (sessionId) => {
        return await ClassroomAPI.request(`${ClassroomAPI.baseURL}/sessions/${sessionId}/state`);
    },

    finishSession: async (sessionId) => {
        return await ClassroomAPI.request(`${ClassroomAPI.baseURL}/sessions/${sessionId}/finish`, {
            method: 'POST'
        });
    },

    createDrawRecord: async (studentId, questionId, result, scoreDelta = 0, note = '') => {
        if (!ClassroomAPI.currentSessionId) {
            throw new Error('请先创建课堂会话');
        }
        return await ClassroomAPI.request(
            `${ClassroomAPI.baseURL}/sessions/${ClassroomAPI.currentSessionId}/draws`,
            {
                method: 'POST',
                body: JSON.stringify({
                    student_id: studentId,
                    question_id: questionId,
                    result,
                    score_delta: scoreDelta,
                    note
                })
            }
        );
    },

    getDrawRecords: async (sessionId) => {
        return await ClassroomAPI.request(`${ClassroomAPI.baseURL}/sessions/${sessionId}/draws`);
    }
};

window.ClassroomAPI = ClassroomAPI;
