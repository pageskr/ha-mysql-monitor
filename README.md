# MySQL Monitor Integration for Home Assistant

이 통합은 Home Assistant에서 MySQL 서버를 종합적으로 모니터링할 수 있게 해줍니다.

## 주요 기능

- **시스템 리소스 모니터링**: CPU, 메모리 사용량
- **MySQL 성능 메트릭**: 연결, 쿼리, InnoDB 통계
- **데이터베이스 분석**: 크기, 테이블 수, 행 수 추적
- **고급 모니터링**: 트랜잭션, 복제 상태

## 설치 방법

1. `ha-mysql-monitor` 폴더의 `custom_components/mysql_monitor` 디렉토리를 Home Assistant의 `custom_components` 폴더로 복사
2. Home Assistant 재시작
3. 설정 > 기기 및 서비스 > 통합 추가 > "MySQL Monitor" 검색
4. MySQL 연결 정보 입력

## 보안 권장사항

읽기 전용 사용자 생성:
```sql
CREATE USER 'ha_monitor'@'%' IDENTIFIED BY '강력한_비밀번호';
GRANT SELECT, SHOW VIEW, REPLICATION CLIENT, PROCESS ON *.* TO 'ha_monitor'@'%';
GRANT SELECT ON performance_schema.* TO 'ha_monitor'@'%';
FLUSH PRIVILEGES;
```

## 제작자

**Pages in Korea (pages.kr)** (@pageskr)

## 라이선스

이 통합은 Home Assistant 커뮤니티를 위해 제공됩니다.

## 문의

문제 또는 기능 요청: https://github.com/pageskr/ha-mysql-monitor/issues
