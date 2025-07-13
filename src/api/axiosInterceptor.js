import axios from 'axios';

const apiClient = axios.create({
    baseURL: '/api',
    withCredentials: true,
});

apiClient.interceptors.request.use((config) => {
    config.headers['X-GovChat-Request'] = 'true';
    return config;
});

apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            // Add refresh token logic here
            return apiClient(originalRequest);
        }
        return Promise.reject(error);
    }
);

export default apiClient;