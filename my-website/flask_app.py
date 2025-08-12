import os
import sqlite3
import pandas as pd
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

_root_dir = os.path.dirname(os.path.abspath(__file__))
_static_folder = os.path.join(_root_dir, 'src')

app = Flask(__name__, static_folder=_static_folder, static_url_path='')

# DB 초기화 함수
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        password TEXT NOT NULL
    )''')
    
    # 야자 관리 테이블 생성
    c.execute('''CREATE TABLE IF NOT EXISTS yaja_students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        period INTEGER NOT NULL,
        student_name TEXT NOT NULL,
        student_code TEXT NOT NULL,
        student_number TEXT NOT NULL,
        reason TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 학특사 테이블 생성
    c.execute('''CREATE TABLE IF NOT EXISTS hagteugsa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        max_members INTEGER NOT NULL,
        creator_name TEXT NOT NULL,
        creator_code TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 학특사 참여자 테이블 생성
    c.execute('''CREATE TABLE IF NOT EXISTS hagteugsa_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hagteugsa_id INTEGER NOT NULL,
        member_name TEXT NOT NULL,
        member_code TEXT NOT NULL,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (hagteugsa_id) REFERENCES hagteugsa (id) ON DELETE CASCADE
    )''')
    
    # 수행평가 테이블 생성
    c.execute('''CREATE TABLE IF NOT EXISTS suhang (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL,
        title TEXT NOT NULL,
        deadline TEXT NOT NULL,
        description TEXT NOT NULL,
        creator_name TEXT NOT NULL,
        creator_code TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

init_db()

# 루트 경로 핸들러 (Health Check용)
@app.route('/')
def index():
    return app.send_static_file('index.html')

# Health Check 엔드포인트
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'message': 'Flask app is running'}, 200

# 회원가입 API
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    user_id = data.get('id')
    name = data.get('name')
    pw = data.get('password')
    if not user_id or not name or not pw:
        return {'success': False, 'msg': '모든 항목을 입력하세요.'}, 400
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE id=?', (user_id,))
    if c.fetchone():
        conn.close()
        return {'success': False, 'msg': '이미 존재하는 아이디입니다.'}, 409
    pw_hash = generate_password_hash(pw)
    c.execute('INSERT INTO users (id, name, password) VALUES (?, ?, ?)', (user_id, name, pw_hash))
    conn.commit()
    conn.close()
    return {'success': True}

# 로그인 API
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user_id = data.get('id')
    pw = data.get('password')
    if not user_id or not pw:
        return {'success': False, 'msg': '모든 항목을 입력하세요.'}, 400
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT password, name FROM users WHERE id=?', (user_id,))
    row = c.fetchone()
    conn.close()
    if not row or not check_password_hash(row[0], pw):
        return {'success': False, 'msg': '아이디 또는 비밀번호가 올바르지 않습니다.'}, 401
    return {'success': True, 'name': row[1]}

# 야자 학생 추가 API
@app.route('/api/yaja/add', methods=['POST'])
def add_yaja_student():
    try:
        data = request.json
        date = data.get('date')
        periods = data.get('periods')  # 배열
        student_name = data.get('student_name')
        student_code = data.get('student_code')
        student_number = data.get('student_number')
        reason = data.get('reason')
        
        if not all([date, periods, student_name, student_code, student_number, reason]):
            return {'success': False, 'msg': '모든 필드를 입력하세요.'}, 400
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # 각 차시별로 데이터 삽입
        for period in periods:
            c.execute('''INSERT INTO yaja_students 
                         (date, period, student_name, student_code, student_number, reason)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (date, period, student_name, student_code, student_number, reason))
        
        conn.commit()
        conn.close()
        
        return {'success': True}
    except Exception as e:
        return {'success': False, 'msg': str(e)}, 500

# 야자 학생 목록 조회 API
@app.route('/api/yaja/list/<date>')
def get_yaja_students(date):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute('''SELECT id, period, student_name, student_code, student_number, reason
                     FROM yaja_students WHERE date = ? ORDER BY period, student_name''', (date,))
        
        rows = c.fetchall()
        conn.close()
        
        # 차시별로 정리
        students = {1: [], 2: [], 3: []}
        for row in rows:
            student_data = {
                'id': row[0],
                'name': row[2],
                'code': row[3],
                'studentNumber': row[4],
                'reason': row[5]
            }
            students[row[1]].append(student_data)
        
        return {'success': True, 'data': students}
    except Exception as e:
        return {'success': False, 'msg': str(e)}, 500

# 야자 학생 삭제 API
@app.route('/api/yaja/delete/<int:student_id>', methods=['DELETE'])
def delete_yaja_student(student_id):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute('DELETE FROM yaja_students WHERE id = ?', (student_id,))
        
        if c.rowcount == 0:
            conn.close()
            return {'success': False, 'msg': '해당 학생을 찾을 수 없습니다.'}, 404
        
        conn.commit()
        conn.close()
        
        return {'success': True}
    except Exception as e:
        return {'success': False, 'msg': str(e)}, 500

# 학특사 관련 API들

# 학특사 생성 API
@app.route('/api/hagteugsa/create', methods=['POST'])
def create_hagteugsa():
    try:
        data = request.json
        title = data.get('title')
        description = data.get('description')
        max_members = data.get('max_members')
        creator_name = data.get('creator_name')
        creator_code = data.get('creator_code')
        
        if not all([title, description, max_members, creator_name, creator_code]):
            return {'success': False, 'msg': '모든 필드를 입력하세요.'}, 400
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # 학특사 생성
        c.execute('''INSERT INTO hagteugsa (title, description, max_members, creator_name, creator_code)
                     VALUES (?, ?, ?, ?, ?)''',
                  (title, description, max_members, creator_name, creator_code))
        
        hagteugsa_id = c.lastrowid
        
        # 생성자를 첫 번째 멤버로 추가
        c.execute('''INSERT INTO hagteugsa_members (hagteugsa_id, member_name, member_code)
                     VALUES (?, ?, ?)''',
                  (hagteugsa_id, creator_name, creator_code))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'id': hagteugsa_id}
    except Exception as e:
        return {'success': False, 'msg': str(e)}, 500

# 학특사 목록 조회 API
@app.route('/api/hagteugsa/list')
def get_hagteugsa_list():
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # 학특사 목록과 각각의 멤버 수 조회
        c.execute('''SELECT h.id, h.title, h.description, h.max_members, h.creator_name,
                            COUNT(hm.id) as current_members
                     FROM hagteugsa h
                     LEFT JOIN hagteugsa_members hm ON h.id = hm.hagteugsa_id
                     GROUP BY h.id
                     ORDER BY h.created_at DESC''')
        
        rows = c.fetchall()
        
        hagteugsa_list = []
        for row in rows:
            # 각 학특사의 멤버 목록 조회
            c.execute('''SELECT member_name FROM hagteugsa_members 
                         WHERE hagteugsa_id = ? ORDER BY joined_at''', (row[0],))
            members = [member[0] for member in c.fetchall()]
            
            hagteugsa_list.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'max_members': row[3],
                'creator_name': row[4],
                'current_members': row[5],
                'members': members
            })
        
        conn.close()
        return {'success': True, 'data': hagteugsa_list}
    except Exception as e:
        return {'success': False, 'msg': str(e)}, 500

# 학특사 참여 API
@app.route('/api/hagteugsa/join', methods=['POST'])
def join_hagteugsa():
    try:
        data = request.json
        hagteugsa_id = data.get('hagteugsa_id')
        member_name = data.get('member_name')
        member_code = data.get('member_code')
        
        if not all([hagteugsa_id, member_name, member_code]):
            return {'success': False, 'msg': '모든 필드를 입력하세요.'}, 400
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # 학특사 정보 조회
        c.execute('SELECT max_members FROM hagteugsa WHERE id = ?', (hagteugsa_id,))
        hagteugsa = c.fetchone()
        if not hagteugsa:
            conn.close()
            return {'success': False, 'msg': '존재하지 않는 학특사입니다.'}, 404
        
        # 현재 참여자 수 확인
        c.execute('SELECT COUNT(*) FROM hagteugsa_members WHERE hagteugsa_id = ?', (hagteugsa_id,))
        current_count = c.fetchone()[0]
        
        if current_count >= hagteugsa[0]:
            conn.close()
            return {'success': False, 'msg': '모집이 마감되었습니다!'}, 400
        
        # 이미 참여했는지 확인
        c.execute('SELECT id FROM hagteugsa_members WHERE hagteugsa_id = ? AND member_name = ?', 
                  (hagteugsa_id, member_name))
        if c.fetchone():
            conn.close()
            return {'success': False, 'msg': '이미 참여하셨습니다!'}, 400
        
        # 참여자 추가
        c.execute('''INSERT INTO hagteugsa_members (hagteugsa_id, member_name, member_code)
                     VALUES (?, ?, ?)''',
                  (hagteugsa_id, member_name, member_code))
        
        conn.commit()
        conn.close()
        
        return {'success': True}
    except Exception as e:
        return {'success': False, 'msg': str(e)}, 500

# 학특사 삭제 API
@app.route('/api/hagteugsa/delete/<int:hagteugsa_id>', methods=['DELETE'])
def delete_hagteugsa(hagteugsa_id):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # 멤버 먼저 삭제
        c.execute('DELETE FROM hagteugsa_members WHERE hagteugsa_id = ?', (hagteugsa_id,))
        
        # 학특사 삭제
        c.execute('DELETE FROM hagteugsa WHERE id = ?', (hagteugsa_id,))
        
        if c.rowcount == 0:
            conn.close()
            return {'success': False, 'msg': '해당 학특사를 찾을 수 없습니다.'}, 404
        
        conn.commit()
        conn.close()
        
        return {'success': True}
    except Exception as e:
        return {'success': False, 'msg': str(e)}, 500

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/meal')
def get_meal_data():
    try:
        # CSV 파일 읽기
        csv_file = os.path.join(_root_dir, 'food_calender.csv')
        df = pd.read_csv(csv_file, encoding='utf-8')
        
        # 오늘 날짜 기준으로 이번 주 월요일 찾기
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        
        # 이번 주 날짜들 생성 (월~금)
        week_dates = []
        for i in range(5):
            date = monday + timedelta(days=i)
            week_dates.append(date.strftime('%Y%m%d'))
        
        # 급식 데이터 필터링 및 파싱
        meal_data = []
        for i, date_str in enumerate(week_dates):
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            day_names = ['월', '화', '수', '목', '금']
            day_name = day_names[i]
            
            # 해당 날짜의 급식 데이터 찾기
            day_meal = df[df['급식일자'] == int(date_str)]
            
            if not day_meal.empty:
                # 요리명에서 메뉴 추출 (HTML 태그 제거)
                menu_text = day_meal.iloc[0]['요리명']
                # <br/> 태그를 기준으로 분리하고 알레르기 정보 제거
                menu_items = []
                for item in menu_text.split('<br/>'):
                    # 괄호 안의 알레르기 정보 제거
                    clean_item = item.split('(')[0].strip()
                    if clean_item:
                        menu_items.append(clean_item)
                
                # 칼로리 정보 추출
                calories = day_meal.iloc[0]['칼로리정보']
                calories_num = f"{calories.split(' ')[0]}kcal" if pd.notna(calories) else '칼로리: 정보없음'
            else:
                # 데이터가 없는 경우 기본 메뉴
                menu_items = ['급식 정보가 없습니다']
                calories_num = '칼로리: 정보없음'

            # 오늘인지 확인
            is_today = date_obj.date() == today.date()
            
            meal_data.append({
                'date': date_obj.strftime('%Y-%m-%d'),
                'day': f'{day_name}요일',
                'menu': menu_items,
                'calories': calories_num,
                'isToday': is_today
            })
        
        return jsonify({
            'success': True,
            'data': meal_data,
            'message': f'이번 주 급식 정보 ({monday.strftime("%m월 %d일")} ~ {(monday + timedelta(days=4)).strftime("%m월 %d일")})'
        })
        
    except Exception as e:
        print(f"급식 데이터 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '급식 데이터를 불러오는데 실패했습니다.'
        })

# 수행평가 목록 조회 API
@app.route('/api/suhang/list', methods=['GET'])
def get_suhang_list():
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''SELECT id, subject, title, deadline, description, creator_name, creator_code, created_at 
                     FROM suhang ORDER BY deadline ASC''')
        
        suhang_list = []
        for row in c.fetchall():
            suhang_list.append({
                'id': row[0],
                'subject': row[1],
                'title': row[2],
                'deadline': row[3],
                'description': row[4],
                'creator_name': row[5],
                'creator_code': row[6],
                'created_at': row[7]
            })
        
        conn.close()
        return jsonify({
            'success': True,
            'data': suhang_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': str(e)
        })

# 수행평가 추가 API
@app.route('/api/suhang/add', methods=['POST'])
def add_suhang():
    try:
        data = request.json
        subject = data.get('subject')
        title = data.get('title')
        deadline = data.get('deadline')
        description = data.get('description')
        creator_name = data.get('creator_name')
        creator_code = data.get('creator_code')
        
        if not all([subject, title, deadline, description, creator_name, creator_code]):
            return jsonify({
                'success': False,
                'msg': '모든 필드를 입력해주세요.'
            })
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''INSERT INTO suhang (subject, title, deadline, description, creator_name, creator_code)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (subject, title, deadline, description, creator_name, creator_code))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'msg': '수행평가가 성공적으로 추가되었습니다.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': str(e)
        })

# 수행평가 삭제 API
@app.route('/api/suhang/delete/<int:suhang_id>', methods=['DELETE'])
def delete_suhang(suhang_id):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # 수행평가 존재 확인
        c.execute('SELECT creator_name, creator_code FROM suhang WHERE id = ?', (suhang_id,))
        suhang = c.fetchone()
        
        if not suhang:
            conn.close()
            return jsonify({
                'success': False,
                'msg': '해당 수행평가를 찾을 수 없습니다.'
            })
        
        # 수행평가 삭제
        c.execute('DELETE FROM suhang WHERE id = ?', (suhang_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'msg': '수행평가가 성공적으로 삭제되었습니다.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': str(e)
        })

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)