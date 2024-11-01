document.addEventListener('DOMContentLoaded', () => {
    const boardElement = document.getElementById('board');
    const turnInfo = document.getElementById('turn-info');
    let player = null;
    let isGameFinished = false;  // 게임 종료 상태를 추적합니다.

    function renderBoard(board) {
        boardElement.innerHTML = ''; // 이전 보드 내용 제거
        for (let y = 0; y < 16; y++) {
            const row = document.createElement('tr'); // 테이블 행 생성
            for (let x = 0; x < 16; x++) {
                const cell = document.createElement('td'); // 테이블 셀 생성
                cell.dataset.x = x;
                cell.dataset.y = y;
    
                const stone = board.find(stone => stone.x === x && stone.y === y);
                const stoneDiv = document.createElement('div'); // 돌을 표시할 div 생성
    
                if (stone) {
                    // player1은 흑돌, player2는 백돌
                    stoneDiv.classList.add(stone.player === 1 ? 'player1' : 'player2');
                    cell.appendChild(stoneDiv);
                }
    
                cell.addEventListener('click', () => makeMove(x, y));
                row.appendChild(cell); // 셀을 행에 추가
            }
            boardElement.appendChild(row); // 행을 보드에 추가
        }
    }

    async function makeMove(x, y) {
        if (player === null || isGameFinished) return;

        const response = await fetch('/status');
        const data = await response.json();
        if (data.current_turn !== player || data.is_finished) return;

        const res = await fetch('/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ x, y, player })
        });

        const result = await res.json();
        if (result.status === "error") {
            alert(result.message);
        } else if (result.status === "win") {
            const winnerMessage = `Player ${result.winner} wins!`;
            
            // 모든 플레이어에게 알림 표시
            alert(winnerMessage);
            
            isGameFinished = true; // 게임 종료 상태 설정
            updateBoard(); // 보드 업데이트
        
            // 2초 후에 /end로 이동
            setTimeout(() => {
                window.location.href = '/end'; // /end로 이동
            }, 2000);
        }
        else {
            updateBoard(); // 보드 업데이트
        }


    }

    async function updateBoard() {
        const response = await fetch('/status');
        const data = await response.json();

        isGameFinished = data.is_finished;  // 게임 종료 상태 갱신
        renderBoard(data.board);
        turnInfo.textContent = isGameFinished ? "Game Over" : `Player ${data.current_turn}'s Turn`;
        if(isGameFinished){
            setTimeout(() => {
                window.location.href = '/end'; // /end로 이동
            }, 2000);
        }
    }

    async function joinGame() {
        const response = await fetch('/join', { method: 'POST' });
        const data = await response.json();

        if (data.status === "error") {
            alert(data.message);
        } else {
            player = data.player;
            alert(`You are Player ${player}`);
            updateBoard();
        }
    }

    joinGame();
    setInterval(updateBoard, 1000);
});
