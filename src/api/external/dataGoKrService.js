import axios from 'axios';
import { logger } from '../logger.js';

export class DataGoKrService {
    constructor(apiKey, dbClient) {
        this.apiKey = apiKey;
        this.db = dbClient;
        this.baseUrl = 'https://api.data.go.kr';
    }

    async searchPolicies(keyword, page = 1, numOfRows = 100) {
        try {
            const response = await axios.get(`${this.baseUrl}/1360000/SupportPolicyService/getSupportPolicyList`, {
                params: {
                    serviceKey: this.apiKey,
                    keyword: keyword,
                    pageNo: page,
                    numOfRows: numOfRows,
                    type: 'json'
                },
                timeout: 10000
            });

            if (response.data.response?.header?.resultCode === '00') {
                return response.data.response.body.items || [];
            } else {
                throw new Error(`API Error: ${response.data.response?.header?.resultMsg}`);
            }
        } catch (error) {
            logger.error('External API search failed', { 
                error: error.message, 
                keyword, 
                page 
            });
            throw error;
        }
    }

    async syncPolicies(keywords = ['청년', '창업', '중소기업', '지원사업']) {
        const syncResults = {
            total: 0,
            inserted: 0,
            updated: 0,
            errors: []
        };

        try {
            for (const keyword of keywords) {
                try {
                    const policies = await this.searchPolicies(keyword);
                    
                    for (const policy of policies) {
                        try {
                            const result = await this.upsertPolicy(policy);
                            
                            syncResults.total++;
                            if (result.action === 'insert') {
                                syncResults.inserted++;
                            } else {
                                syncResults.updated++;
                            }
                        } catch (error) {
                            syncResults.errors.push({
                                policyId: policy.policyId,
                                error: error.message
                            });
                        }
                    }
                } catch (error) {
                    syncResults.errors.push({
                        keyword,
                        error: error.message
                    });
                }
            }

            logger.info('Policy sync completed', syncResults);
            return syncResults;
        } catch (error) {
            logger.error('Policy sync failed', { error: error.message });
            throw error;
        }
    }

    async upsertPolicy(policyData) {
        try {
            const mappedData = this.mapExternalData(policyData);
            
            const existingResult = await this.db.query(
                'SELECT project_id FROM projects WHERE policy_external_id = $1',
                [mappedData.policy_external_id]
            );

            if (existingResult.rows.length > 0) {
                const updateResult = await this.db.query(
                    `UPDATE projects SET 
                        title = $1, description = $2, agency = $3, 
                        target_audience = $4, support_content = $5, 
                        application_period = $6, last_updated = CURRENT_TIMESTAMP
                    WHERE policy_external_id = $7 AND source = 'external'
                    RETURNING project_id`,
                    [
                        mappedData.title, mappedData.description, mappedData.agency,
                        mappedData.target_audience, mappedData.support_content,
                        mappedData.application_period, mappedData.policy_external_id
                    ]
                );

                return { 
                    action: 'update', 
                    projectId: updateResult.rows[0]?.project_id 
                };
            } else {
                const insertResult = await this.db.query(
                    `INSERT INTO projects (
                        policy_external_id, title, description, agency,
                        target_audience, support_content, application_period, source
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'external')
                    RETURNING project_id`,
                    [
                        mappedData.policy_external_id, mappedData.title, 
                        mappedData.description, mappedData.agency,
                        mappedData.target_audience, mappedData.support_content,
                        mappedData.application_period
                    ]
                );

                return { 
                    action: 'insert', 
                    projectId: insertResult.rows[0].project_id 
                };
            }
        } catch (error) {
            logger.error('Upsert policy failed', { 
                error: error.message, 
                policyId: policyData.policyId 
            });
            throw error;
        }
    }

    mapExternalData(policyData) {
        return {
            policy_external_id: policyData.policyId,
            title: policyData.policyName || '',
            description: policyData.policyContent || '',
            agency: policyData.organName || '',
            target_audience: policyData.target || '',
            support_content: policyData.supportContent || '',
            application_period: policyData.applyPeriod || ''
        };
    }
}