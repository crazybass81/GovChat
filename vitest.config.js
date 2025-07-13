import { defineConfig } from 'vitest';

export default defineConfig({
    test: {
        globals: true,
        environment: 'jsdom',
        coverage: {
            provider: 'istanbul',
            reporter: ['text', 'html'],
        },
    },
});
