// AWS Lambda 함수 설정 파일
// 이 파일은 성능 최적화 및 콜드 스타트 지연을 줄이기 위한 설정을 정의합니다

export const lambdaConfig = {
    memorySize: 1024, // 실행 속도를 개선하기 위해 1024MB 메모리 할당
    timeout: 30, // 최대 실행 시간을 30초로 설정
    provisionedConcurrency: 5, // 콜드 스타트 지연을 최소화하기 위해 5개의 인스턴스를 유지
};