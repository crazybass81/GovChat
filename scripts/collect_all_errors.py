#!/usr/bin/env python3
"""
GovChat 전체 오류 로그 수집 및 디버깅 리뷰 생성
"""

import boto3
import json
import subprocess
import os
from datetime import datetime, timedelta

def collect_lambda_errors():
    """Lambda 함수 오류 로그 수집"""
    logs_client = boto3.client('logs', region_name='us-east-1')
    
    functions = [
        'GovChat-ChatbotLambda',
        'GovChat-SearchLambda', 
        'GovChat-MatchLambda',
        'GovChat-ExtractLambda',
        'GovChat-ExternalSyncLambda'
    ]
    
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=12)
    
    lambda_errors = {}
    
    for func in functions:
        try:
            response = logs_client.filter_log_events(
                logGroupName=f'/aws/lambda/{func}',
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000),
                filterPattern='ERROR'
            )
            
            errors = []
            for event in response.get('events', []):
                errors.append({
                    'timestamp': datetime.fromtimestamp(event['timestamp']/1000).isoformat(),
                    'message': event['message'].strip(),
                    'logStream': event.get('logStreamName', '')
                })
            
            lambda_errors[func] = errors
            
        except Exception as e:
            lambda_errors[func] = [{'error': f'수집 실패: {str(e)}'}]
    
    return lambda_errors

def collect_cdk_errors():
    """CDK 배포 오류 수집"""
    try:
        # 최근 CDK 로그 확인
        result = subprocess.run(['cdk', 'ls'], capture_output=True, text=True, cwd='infra')
        if result.returncode != 0:
            return {'cdk_status': f'CDK 오류: {result.stderr}'}
        
        return {'cdk_status': 'OK'}
    except Exception as e:
        return {'cdk_status': f'CDK 확인 실패: {str(e)}'}

def collect_git_errors():
    """Git 상태 및 최근 커밋 오류 확인"""
    try:
        # Git 상태 확인
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        uncommitted = result.stdout.strip()
        
        # 최근 커밋 로그
        result = subprocess.run(['git', 'log', '--oneline', '-5'], capture_output=True, text=True)
        recent_commits = result.stdout.strip()
        
        return {
            'uncommitted_changes': uncommitted.split('\n') if uncommitted else [],
            'recent_commits': recent_commits.split('\n') if recent_commits else []
        }
    except Exception as e:
        return {'git_error': str(e)}

def collect_test_errors():
    """Python 및 프론트엔드 테스트 오류 수집"""
    test_errors = []
    
    try:
        # Python 테스트 실행
        result = subprocess.run(['python', '-m', 'pytest', 'tests/', '-v'], capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            test_errors.append({
                'type': 'python_test_error',
                'error': result.stdout[-1000:] + result.stderr[-500:]
            })
        
        # 프론트엔드 테스트 실행
        result = subprocess.run(['npm', 'test'], capture_output=True, text=True, cwd='frontend', timeout=60)
        if result.returncode != 0:
            test_errors.append({
                'type': 'frontend_test_error',
                'error': result.stdout[-500:]
            })
        
    except Exception as e:
        test_errors.append({
            'type': 'test_collection_error',
            'error': str(e)
        })
    
    return test_errors

def collect_frontend_errors():
    """Next.js 프론트엔드 오류 수집"""
    frontend_errors = []
    
    try:
        # Next.js 빌드 오류 확인
        result = subprocess.run(['npm', 'run', 'build'], capture_output=True, text=True, cwd='frontend', timeout=60)
        if result.returncode != 0:
            frontend_errors.append({
                'type': 'build_error',
                'error': result.stderr[:500]
            })
        
        # TypeScript 오류 확인
        result = subprocess.run(['npx', 'tsc', '--noEmit'], capture_output=True, text=True, cwd='frontend', timeout=30)
        if result.returncode != 0:
            frontend_errors.append({
                'type': 'typescript_error',
                'error': result.stdout[:500]
            })
        
        # 로그 파일 확인
        if os.path.exists('frontend/dev.log'):
            with open('frontend/dev.log', 'r') as f:
                log_content = f.read()
                if 'error' in log_content.lower():
                    frontend_errors.append({
                        'type': 'dev_log_error',
                        'error': log_content[-500:]
                    })
        
    except Exception as e:
        frontend_errors.append({
            'type': 'collection_error',
            'error': str(e)
        })
    
    return frontend_errors

def collect_api_errors():
    """API 테스트 오류 수집"""
    api_base = "https://l2iyczn1ge.execute-api.us-east-1.amazonaws.com/prod"
    
    endpoints = [
        {'path': '/search?q=test', 'method': 'GET'},
        {'path': '/question', 'method': 'POST', 'data': '{"message":"test"}'},
        {'path': '/match', 'method': 'POST', 'data': '{"query":"test"}'},
        {'path': '/extract', 'method': 'POST', 'data': '{"text":"test"}'}
    ]
    
    api_errors = []
    
    for endpoint in endpoints:
        try:
            if endpoint['method'] == 'GET':
                cmd = ['curl', '-s', f"{api_base}{endpoint['path']}"]
            else:
                cmd = ['curl', '-s', '-X', endpoint['method'], 
                       '-H', 'Content-Type: application/json',
                       '-d', endpoint['data'], f"{api_base}{endpoint['path']}"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                api_errors.append({
                    'endpoint': endpoint['path'],
                    'error': f'curl 실패: {result.stderr}'
                })
            else:
                try:
                    response = json.loads(result.stdout)
                    if 'error' in response or 'Internal server error' in result.stdout:
                        api_errors.append({
                            'endpoint': endpoint['path'],
                            'error': response.get('error', result.stdout)
                        })
                except:
                    if 'error' in result.stdout.lower():
                        api_errors.append({
                            'endpoint': endpoint['path'],
                            'error': result.stdout
                        })
                        
        except Exception as e:
            api_errors.append({
                'endpoint': endpoint['path'],
                'error': str(e)
            })
    
    return api_errors

def generate_debug_review(all_errors):
    """디버깅 리뷰 생성"""
    
    review = {
        'timestamp': datetime.now().isoformat(),
        'period': '12 hours',
        'summary': {},
        'priority_issues': [],
        'recommendations': []
    }
    
    # 요약 생성
    lambda_error_count = sum(len(errors) for errors in all_errors['lambda_errors'].values() 
                           if isinstance(errors, list))
    api_error_count = len(all_errors['api_errors'])
    frontend_error_count = len(all_errors['frontend_errors'])
    test_error_count = len(all_errors['test_errors'])
    
    review['summary'] = {
        'test_errors': test_error_count,
        'frontend_errors': frontend_error_count,
        'lambda_errors': lambda_error_count,
        'api_errors': api_error_count,
        'cdk_status': all_errors['cdk_errors']['cdk_status'],
        'git_uncommitted': len(all_errors['git_status']['uncommitted_changes'])
    }
    
    # 우선순위 이슈 식별
    if api_error_count > 0:
        review['priority_issues'].append({
            'level': 'HIGH',
            'issue': 'API 엔드포인트 오류',
            'count': api_error_count,
            'details': all_errors['api_errors'][:3]
        })
    
    if lambda_error_count > 5:
        review['priority_issues'].append({
            'level': 'HIGH', 
            'issue': 'Lambda 함수 다수 오류',
            'count': lambda_error_count
        })
    
    # 권장사항 생성
    if '/question' in str(all_errors['api_errors']):
        review['recommendations'].append('ChatbotLambda 함수 의존성 및 import 경로 확인 필요')
    
    if 'ImportModuleError' in str(all_errors['lambda_errors']):
        review['recommendations'].append('Lambda 레이어 및 패키지 의존성 재검토 필요')
    
    if all_errors['git_status']['uncommitted_changes']:
        review['recommendations'].append('미커밋 변경사항 정리 후 배포 권장')
    
    return review

def save_error_logs(all_errors, review):
    """오류 로그와 리뷰를 파일로 저장"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 전체 오류 로그 저장
    error_file = f'logs/all_errors_{timestamp}.json'
    with open(error_file, 'w', encoding='utf-8') as f:
        json.dump(all_errors, f, indent=2, ensure_ascii=False)
    
    # 디버깅 리뷰 저장
    review_file = f'logs/debug_review_{timestamp}.json'
    with open(review_file, 'w', encoding='utf-8') as f:
        json.dump(review, f, indent=2, ensure_ascii=False)
    
    # 마크다운 리뷰 생성
    md_file = f'logs/debug_review_{timestamp}.md'
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(f"# GovChat 디버깅 리뷰\n\n")
        f.write(f"**생성일시**: {review['timestamp']}\n")
        f.write(f"**분석 기간**: {review['period']}\n\n")
        
        f.write("## 📊 요약\n\n")
        f.write(f"- Lambda 오류: {review['summary']['lambda_errors']}개\n")
        f.write(f"- API 오류: {review['summary']['api_errors']}개\n")
        f.write(f"- CDK 상태: {review['summary']['cdk_status']}\n")
        f.write(f"- 미커밋 파일: {review['summary']['git_uncommitted']}개\n\n")
        
        if review['priority_issues']:
            f.write("## 🚨 우선순위 이슈\n\n")
            for issue in review['priority_issues']:
                f.write(f"### {issue['level']}: {issue['issue']}\n")
                f.write(f"- 발생 횟수: {issue['count']}\n")
                if 'details' in issue:
                    for detail in issue['details']:
                        f.write(f"- {detail['endpoint']}: {detail['error'][:100]}...\n")
                f.write("\n")
        
        if review['recommendations']:
            f.write("## 💡 권장사항\n\n")
            for rec in review['recommendations']:
                f.write(f"- {rec}\n")
    
    return error_file, review_file, md_file

def main():
    """메인 실행 함수"""
    
    print("🔍 GovChat 오류 로그 수집 시작...")
    
    # 모든 오류 수집
    all_errors = {
        'test_errors': collect_test_errors(),
        'frontend_errors': collect_frontend_errors(),
        'lambda_errors': collect_lambda_errors(),
        'cdk_errors': collect_cdk_errors(),
        'git_status': collect_git_errors(),
        'api_errors': collect_api_errors()
    }
    
    print("📊 디버깅 리뷰 생성 중...")
    
    # 디버깅 리뷰 생성
    review = generate_debug_review(all_errors)
    
    # 파일 저장
    error_file, review_file, md_file = save_error_logs(all_errors, review)
    
    print(f"\n✅ 수집 완료!")
    print(f"- 전체 오류 로그: {error_file}")
    print(f"- 디버깅 리뷰: {review_file}")
    print(f"- 마크다운 리뷰: {md_file}")
    
    # 요약 출력
    print(f"\n📋 요약:")
    print(f"- Lambda 오류: {review['summary']['lambda_errors']}개")
    print(f"- API 오류: {review['summary']['api_errors']}개")
    print(f"- 우선순위 이슈: {len(review['priority_issues'])}개")

if __name__ == '__main__':
    main()