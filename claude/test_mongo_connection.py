#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB 연결 테스트 및 실제 데이터 수집
"""

import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from mongodb_service import MongoDBService
    from claude.data_collector import BlogDataCollector
    MONGODB_AVAILABLE = True
except ImportError as e:
    print(f"MongoDB 모듈 import 실패: {e}")
    MONGODB_AVAILABLE = False


def test_mongodb_connection():
    """MongoDB 연결 테스트"""
    if not MONGODB_AVAILABLE:
        print("❌ MongoDB 모듈을 불러올 수 없습니다.")
        return False
    
    try:
        # MongoDB 서비스 초기화
        db_service = MongoDBService()
        print("✅ MongoDB 연결 성공")
        
        # 데이터베이스 목록 확인
        databases = db_service.client.list_database_names()
        user_dbs = [db for db in databases if db not in ['admin', 'local', 'config']]
        print(f"📊 사용자 데이터베이스: {user_dbs}")
        
        # 각 데이터베이스의 컬렉션 확인
        for db_name in user_dbs[:3]:  # 처음 3개만 확인
            db_service.set_db_name(db_name)
            collections = db_service.db.list_collection_names()
            print(f"  {db_name}: {collections}")
            
            # 간단한 데이터 확인
            for collection in ['morphemes', 'expressions', 'templates'][:2]:
                if collection in collections:
                    count = db_service.db[collection].count_documents({})
                    print(f"    - {collection}: {count}개 문서")
        
        return True
        
    except Exception as e:
        print(f"❌ MongoDB 연결 실패: {e}")
        return False


def collect_real_data():
    """실제 MongoDB 데이터 수집"""
    print("\n" + "="*60)
    print("실제 MongoDB 데이터 수집 시작")
    print("="*60)
    
    collector = BlogDataCollector()
    
    # 실제 데이터베이스 확인
    databases = collector.get_available_databases()
    print(f"발견된 실제 데이터베이스: {databases}")
    
    if not databases:
        print("수집할 데이터베이스가 없습니다.")
        return
    
    # 사용자에게 선택 옵션 제공
    print("\n수집 옵션:")
    print("1. 모든 데이터베이스 수집")
    print("2. 특정 데이터베이스 선택")
    print("3. 취소")
    
    try:
        choice = input("선택하세요 (1-3): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n취소되었습니다.")
        return
    
    if choice == "1":
        # 모든 데이터베이스 수집
        print("\n모든 데이터베이스 수집 중...")
        all_data = collector.collect_all_databases()
        
    elif choice == "2":
        # 특정 데이터베이스 선택
        print("\n사용 가능한 데이터베이스:")
        for i, db_name in enumerate(databases, 1):
            print(f"  {i}. {db_name}")
        
        try:
            db_choice = input("번호를 선택하세요: ").strip()
            db_index = int(db_choice) - 1
            
            if 0 <= db_index < len(databases):
                selected_db = databases[db_index]
                print(f"\n선택된 데이터베이스: {selected_db}")
                
                # 선택된 데이터베이스만 수집
                db_data = collector.collect_database_data(selected_db)
                all_data = {
                    "collection_info": {
                        "collected_at": collector._get_demo_data("")["collected_at"],
                        "collector_version": "1.0",
                        "mongodb_available": MONGODB_AVAILABLE
                    },
                    "databases": {selected_db: db_data}
                }
            else:
                print("잘못된 선택입니다.")
                return
                
        except (ValueError, EOFError, KeyboardInterrupt):
            print("취소되었습니다.")
            return
    
    else:
        print("취소되었습니다.")
        return
    
    # 데이터 저장
    print("\n파일 저장 중...")
    saved_files = collector.save_data(all_data, format_type="both")
    
    print(f"\n✅ 실제 데이터 수집 완료!")
    print(f"저장된 파일:")
    for file_path in saved_files:
        print(f"  - {file_path}")
    
    # 통계 출력
    total_dbs = len(all_data.get("databases", {}))
    print(f"📊 총 {total_dbs}개 데이터베이스 수집 완료")
    
    # 첫 번째 텍스트 파일 일부 미리보기
    text_files = [f for f in saved_files if f.endswith('.txt')]
    if text_files:
        print(f"\n📖 미리보기 ({Path(text_files[0]).name}):")
        print("-" * 40)
        with open(text_files[0], 'r', encoding='utf-8') as f:
            preview = f.read(500)  # 첫 500자
            print(preview)
            if len(preview) == 500:
                print("...")


def main():
    """메인 함수"""
    print("MongoDB 연결 테스트 및 데이터 수집")
    print("="*50)
    
    # MongoDB 연결 테스트
    connection_ok = test_mongodb_connection()
    
    if connection_ok:
        # 실제 데이터 수집
        collect_real_data()
    else:
        print("\nMongoDB 연결이 실패했으므로 데모 데이터를 사용합니다.")
        print("데모 데이터 수집을 원하시면 data_collector.py를 실행하세요.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"\n예상치 못한 오류: {e}")