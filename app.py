from flask import Flask, render_template, redirect, url_for, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = 'gomoku.db'

def get_db_connection():
    """데이터베이스 연결을 설정합니다."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL;')  # WAL 모드 설정
    return conn

def init_db():
    """데이터베이스를 초기화합니다."""
    conn = get_db_connection()
    conn.execute('DROP TABLE IF EXISTS board')
    conn.execute('DROP TABLE IF EXISTS game_status')
    
    conn.execute('''
        CREATE TABLE board (
            x INTEGER,
            y INTEGER,
            player INTEGER
        )
    ''')
    conn.execute('''
        CREATE TABLE game_status (
            game_id INTEGER PRIMARY KEY,
            current_turn INTEGER,
            is_finished BOOLEAN,
            player1_assigned BOOLEAN DEFAULT 0,
            player2_assigned BOOLEAN DEFAULT 0
        )
    ''')
    conn.execute('INSERT INTO game_status (game_id, current_turn, is_finished) VALUES (1, 1, 0)')
    conn.commit()
    conn.close()

def reset_database():
    """게임 데이터를 초기화합니다."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM board")
    cursor.execute("UPDATE game_status SET current_turn = 1, is_finished = 0, player1_assigned = 0, player2_assigned = 0 WHERE game_id = 1")
    conn.commit()
    conn.close()

def check_victory(x, y, player):
    """승리 조건을 체크합니다."""
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]  # 가로, 세로, 두 대각선
    conn = get_db_connection()

    for dx, dy in directions:
        count = 1  # 현재 돌을 포함한 카운트 시작

        # 한 방향으로 연속된 돌 세기
        for i in range(1, 5):
            nx, ny = x + dx * i, y + dy * i
            stone = conn.execute('SELECT * FROM board WHERE x = ? AND y = ? AND player = ?', (nx, ny, player)).fetchone()
            if stone:
                count += 1
            else:
                break

        # 반대 방향으로 연속된 돌 세기
        for i in range(1, 5):
            nx, ny = x - dx * i, y - dy * i
            stone = conn.execute('SELECT * FROM board WHERE x = ? AND y = ? AND player = ?', (nx, ny, player)).fetchone()
            if stone:
                count += 1
            else:
                break

        if count >= 5:
            conn.close()
            return True

    conn.close()
    return False

@app.route('/')
def home():
    """메인 페이지를 렌더링합니다."""
    return render_template('main.html')

@app.route('/end', methods=['GET'])
def end():
    """게임 종료 시 데이터베이스를 초기화하고 메인 페이지로 리다이렉트합니다."""
    reset_database()  # 게임 데이터를 초기화합니다.
    return redirect(url_for('home'))

def reset_database():
    """게임 데이터를 초기화합니다."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM board")
    cursor.execute("UPDATE game_status SET current_turn = 1, is_finished = 0, player1_assigned = 0, player2_assigned = 0 WHERE game_id = 1")
    conn.commit()
    conn.close()

@app.route('/move', methods=['POST'])
def make_move():
    """플레이어의 이동을 처리합니다."""
    data = request.get_json()
    x, y, player = data['x'], data['y'], data['player']

    conn = get_db_connection()
    try:
        existing = conn.execute('SELECT * FROM board WHERE x = ? AND y = ?', (x, y)).fetchone()
        if existing:
            return jsonify({"status": "error", "message": "Position already occupied"})

        conn.execute('INSERT INTO board (x, y, player) VALUES (?, ?, ?)', (x, y, player))

        # 승리 조건 검사
        if check_victory(x, y, player):
            conn.execute('UPDATE game_status SET is_finished = 1 WHERE game_id = 1')
            conn.commit()
            return jsonify({"status": "win", "winner": player})

        # 턴 변경
        conn.execute('UPDATE game_status SET current_turn = ? WHERE game_id = 1', (3 - player,))
        conn.commit()
        
        return jsonify({"status": "success"})
    except sqlite3.OperationalError as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        conn.close()

@app.route('/reset')
def reset_db():
    """게임 데이터를 초기화합니다."""
    try:

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM board")
        cursor.execute("UPDATE game_status SET current_turn = 1, is_finished = 0, player1_assigned = 0, player2_assigned = 0 WHERE game_id = 1")
        conn.commit()

        return render_template('main.html')
    except Exception as e:
        # 오류가 발생하면 JSON 형태로 오류 메시지를 반환
        return jsonify({"status": "error", "message": str(e)})
    finally :
        conn.close()


@app.route('/status', methods=['GET'])
def get_status():
    """게임 상태와 보드를 반환합니다."""
    conn = get_db_connection()
    board = conn.execute('SELECT * FROM board').fetchall()
    game_status = conn.execute('SELECT * FROM game_status WHERE game_id = 1').fetchone()
    conn.close()

    return jsonify({
        "board": [{"x": row["x"], "y": row["y"], "player": row["player"]} for row in board],
        "current_turn": game_status["current_turn"],
        "is_finished": game_status["is_finished"]
    })

@app.route('/join', methods=['POST'])
def join_game():
    """게임에 참가하는 플레이어를 할당합니다."""
    conn = get_db_connection()
    try:
        game_status = conn.execute('SELECT * FROM game_status WHERE game_id = 1').fetchone()

        if not game_status['player1_assigned']:
            player = 1
            conn.execute('UPDATE game_status SET player1_assigned = 1 WHERE game_id = 1')
        elif not game_status['player2_assigned']:
            player = 2
            conn.execute('UPDATE game_status SET player2_assigned = 1 WHERE game_id = 1')
        else:
            return jsonify({"status": "error", "message": "Game is already full."})

        conn.commit()
        return jsonify({"player": player})
    except sqlite3.OperationalError as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        conn.close()

@app.route('/start')
def start_game():
    """게임 시작 페이지를 렌더링합니다."""
    mode = request.args.get('mode')  # 쿼리 파라미터에서 'mode' 값을 가져옵니다.
    if mode == 'blind':
        return render_template('index.html')  # 블라인드 모드일 경우 index1.html 렌더링
    elif mode == 'normal':
        return render_template('index1.html')  # 일반 모드일 경우 index.html 렌더링
    return "게임 모드가 선택되지 않았습니다.", 400

if __name__ == '__main__':
    init_db()  # 앱 시작 시 데이터베이스 초기화
    app.run(host='0.0.0.0', port=5000, debug=True)
