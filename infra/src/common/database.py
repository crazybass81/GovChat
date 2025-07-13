"""
데이터베이스 연결 및 쿼리 공통 모듈
"""

import os
import psycopg2
import boto3
from psycopg2.extras import RealDictCursor
from aws_lambda_powertools import Logger

logger = Logger()


class DatabaseConnection:
    """PostgreSQL 데이터베이스 연결 관리"""
    
    def __init__(self):
        self.connection = None
        self._connect()
    
    def _connect(self):
        """데이터베이스 연결"""
        try:
            # RDS 연결 정보 가져오기
            ssm = boto3.client('ssm')
            
            db_host = ssm.get_parameter(Name='/govchat/db/host')['Parameter']['Value']
            db_name = ssm.get_parameter(Name='/govchat/db/name')['Parameter']['Value']
            db_user = ssm.get_parameter(Name='/govchat/db/user')['Parameter']['Value']
            db_password = ssm.get_parameter(
                Name='/govchat/db/password',
                WithDecryption=True
            )['Parameter']['Value']
            
            self.connection = psycopg2.connect(
                host=db_host,
                database=db_name,
                user=db_user,
                password=db_password,
                port=5432,
                cursor_factory=RealDictCursor
            )
            
            logger.info("Database connection established")
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def execute_query(self, query, params=None):
        """SELECT 쿼리 실행"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            self.connection.rollback()
            raise
    
    def execute_update(self, query, params=None):
        """INSERT/UPDATE/DELETE 쿼리 실행"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Update execution error: {e}")
            self.connection.rollback()
            raise
    
    def execute_insert_returning(self, query, params=None):
        """INSERT 쿼리 실행 후 결과 반환"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                self.connection.commit()
                return result
        except Exception as e:
            logger.error(f"Insert returning execution error: {e}")
            self.connection.rollback()
            raise
    
    def close(self):
        """연결 종료"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")


# 전역 데이터베이스 연결 인스턴스
_db_connection = None


def get_db_connection():
    """데이터베이스 연결 인스턴스 반환"""
    global _db_connection
    
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    
    return _db_connection


def execute_query(query, params=None):
    """쿼리 실행 헬퍼 함수"""
    db = get_db_connection()
    return db.execute_query(query, params)


def execute_update(query, params=None):
    """업데이트 실행 헬퍼 함수"""
    db = get_db_connection()
    return db.execute_update(query, params)


def execute_insert_returning(query, params=None):
    """INSERT 후 결과 반환 헬퍼 함수"""
    db = get_db_connection()
    return db.execute_insert_returning(query, params)