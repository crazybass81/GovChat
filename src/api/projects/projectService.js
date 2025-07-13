import { logger } from '../logger.js';

export class ProjectService {
    constructor(dbClient) {
        this.db = dbClient;
    }

    async getProjects(filters = {}) {
        try {
            let query = 'SELECT * FROM projects WHERE active = TRUE';
            const params = [];
            let paramIndex = 1;

            if (filters.keyword) {
                query += ` AND (title ILIKE $${paramIndex} OR description ILIKE $${paramIndex})`;
                params.push(`%${filters.keyword}%`);
                paramIndex++;
            }

            if (filters.agency) {
                query += ` AND agency = $${paramIndex}`;
                params.push(filters.agency);
                paramIndex++;
            }

            query += ' ORDER BY created_at DESC';

            if (filters.limit) {
                query += ` LIMIT $${paramIndex}`;
                params.push(filters.limit);
                paramIndex++;
            }

            if (filters.offset) {
                query += ` OFFSET $${paramIndex}`;
                params.push(filters.offset);
            }

            const result = await this.db.query(query, params);
            return result.rows;
        } catch (error) {
            logger.error('Get projects failed', { error: error.message, filters });
            throw error;
        }
    }

    async getProjectById(projectId) {
        try {
            const result = await this.db.query(
                'SELECT * FROM projects WHERE project_id = $1 AND active = TRUE',
                [projectId]
            );

            if (result.rows.length === 0) {
                throw new Error('프로젝트를 찾을 수 없습니다.');
            }

            return result.rows[0];
        } catch (error) {
            logger.error('Get project by ID failed', { error: error.message, projectId });
            throw error;
        }
    }

    async createProject(projectData, adminId) {
        try {
            const {
                title, description, agency, target_audience,
                support_content, application_period, application_method,
                required_documents, contact_info, reference_url
            } = projectData;

            const result = await this.db.query(
                `INSERT INTO projects (
                    title, description, agency, target_audience,
                    support_content, application_period, application_method,
                    required_documents, contact_info, reference_url, source
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'manual')
                RETURNING *`,
                [title, description, agency, target_audience,
                 support_content, application_period, application_method,
                 required_documents, contact_info, reference_url]
            );

            const project = result.rows[0];

            await this.logAdminAction(adminId, 'CREATE_PROJECT', 'project', project.project_id, {
                title: project.title,
                agency: project.agency
            });

            logger.info('Project created successfully', { 
                projectId: project.project_id, 
                adminId,
                title: project.title 
            });

            return project;
        } catch (error) {
            logger.error('Create project failed', { error: error.message, adminId });
            throw error;
        }
    }

    async updateProject(projectId, projectData, adminId) {
        try {
            const updateFields = [];
            const params = [];
            let paramIndex = 1;

            Object.entries(projectData).forEach(([key, value]) => {
                if (value !== undefined && key !== 'project_id') {
                    updateFields.push(`${key} = $${paramIndex}`);
                    params.push(value);
                    paramIndex++;
                }
            });

            if (updateFields.length === 0) {
                throw new Error('업데이트할 필드가 없습니다.');
            }

            updateFields.push(`last_updated = CURRENT_TIMESTAMP`);
            params.push(projectId);

            const query = `UPDATE projects SET ${updateFields.join(', ')} WHERE project_id = $${paramIndex} RETURNING *`;
            const result = await this.db.query(query, params);

            if (result.rows.length === 0) {
                throw new Error('프로젝트를 찾을 수 없습니다.');
            }

            const project = result.rows[0];

            await this.logAdminAction(adminId, 'UPDATE_PROJECT', 'project', projectId, {
                updatedFields: Object.keys(projectData),
                title: project.title
            });

            logger.info('Project updated successfully', { projectId, adminId });

            return project;
        } catch (error) {
            logger.error('Update project failed', { error: error.message, projectId, adminId });
            throw error;
        }
    }

    async deleteProject(projectId, adminId) {
        try {
            const result = await this.db.query(
                'UPDATE projects SET active = FALSE, last_updated = CURRENT_TIMESTAMP WHERE project_id = $1 RETURNING title',
                [projectId]
            );

            if (result.rows.length === 0) {
                throw new Error('프로젝트를 찾을 수 없습니다.');
            }

            await this.logAdminAction(adminId, 'DELETE_PROJECT', 'project', projectId, {
                title: result.rows[0].title
            });

            logger.info('Project deleted successfully', { projectId, adminId });

            return { success: true };
        } catch (error) {
            logger.error('Delete project failed', { error: error.message, projectId, adminId });
            throw error;
        }
    }

    async logAdminAction(adminId, action, targetType, targetId, details) {
        try {
            await this.db.query(
                'INSERT INTO admin_logs (admin_id, action, target_type, target_id, details) VALUES ($1, $2, $3, $4, $5)',
                [adminId, action, targetType, targetId, JSON.stringify(details)]
            );
        } catch (error) {
            logger.error('Admin log failed', { error: error.message, adminId, action });
        }
    }
}