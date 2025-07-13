import express from 'express';
import { ProjectService } from '../projects/projectService.js';
import { DataGoKrService } from '../external/dataGoKrService.js';
import { authenticateToken, requireAdmin, rateLimiter } from '../middleware/authMiddleware.js';
import { logger } from '../logger.js';

const router = express.Router();
const generalRateLimit = rateLimiter(100, 15 * 60 * 1000);
const adminRateLimit = rateLimiter(50, 15 * 60 * 1000);

export function createProjectRoutes(dbClient) {
    const projectService = new ProjectService(dbClient);
    const dataGoKrService = new DataGoKrService(process.env.DATA_GO_KR_API_KEY, dbClient);

    // 프로젝트 목록 조회
    router.get('/', authenticateToken, generalRateLimit, async (req, res) => {
        try {
            const { keyword, agency, limit = 20, offset = 0 } = req.query;
            
            const filters = {
                keyword,
                agency,
                limit: parseInt(limit),
                offset: parseInt(offset)
            };

            const projects = await projectService.getProjects(filters);
            res.json({ projects });
        } catch (error) {
            logger.error('Get projects endpoint error', { error: error.message });
            res.status(500).json({ error: '프로젝트 조회 중 오류가 발생했습니다.' });
        }
    });

    // 프로젝트 상세 조회
    router.get('/:id', authenticateToken, generalRateLimit, async (req, res) => {
        try {
            const { id } = req.params;
            const project = await projectService.getProjectById(parseInt(id));
            res.json({ project });
        } catch (error) {
            logger.error('Get project by ID endpoint error', { error: error.message });
            res.status(404).json({ error: error.message });
        }
    });

    // 프로젝트 생성 (관리자 전용)
    router.post('/', authenticateToken, requireAdmin, adminRateLimit, async (req, res) => {
        try {
            const projectData = req.body;
            const adminId = req.user.userId;

            const project = await projectService.createProject(projectData, adminId);
            res.status(201).json({
                message: '프로젝트가 성공적으로 생성되었습니다.',
                project
            });
        } catch (error) {
            logger.error('Create project endpoint error', { error: error.message });
            res.status(400).json({ error: error.message });
        }
    });

    // 프로젝트 수정 (관리자 전용)
    router.put('/:id', authenticateToken, requireAdmin, adminRateLimit, async (req, res) => {
        try {
            const { id } = req.params;
            const projectData = req.body;
            const adminId = req.user.userId;

            const project = await projectService.updateProject(parseInt(id), projectData, adminId);
            res.json({
                message: '프로젝트가 성공적으로 수정되었습니다.',
                project
            });
        } catch (error) {
            logger.error('Update project endpoint error', { error: error.message });
            res.status(400).json({ error: error.message });
        }
    });

    // 프로젝트 삭제 (관리자 전용)
    router.delete('/:id', authenticateToken, requireAdmin, adminRateLimit, async (req, res) => {
        try {
            const { id } = req.params;
            const adminId = req.user.userId;

            await projectService.deleteProject(parseInt(id), adminId);
            res.json({ message: '프로젝트가 성공적으로 삭제되었습니다.' });
        } catch (error) {
            logger.error('Delete project endpoint error', { error: error.message });
            res.status(400).json({ error: error.message });
        }
    });

    return router;
}