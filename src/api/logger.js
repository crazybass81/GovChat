import { Logger, Tracer, Metrics } from '@aws-lambda-powertools/logger';

// AWS Lambda Powertools를 사용하여 관측 가능성을 강화합니다
// Logger: 디버깅 및 모니터링을 위한 구조화된 로그를 캡처
// Tracer: 분산 추적을 위한 실행 흐름을 추적
// Metrics: 성능 분석을 위한 사용자 정의 메트릭 기록

const logger = new Logger({ serviceName: 'gov-support-chat' });
const tracer = new Tracer({ serviceName: 'gov-support-chat' });
const metrics = new Metrics({ namespace: 'GovSupportChat' });

export { logger, tracer, metrics };