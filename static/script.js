document.addEventListener('DOMContentLoaded', () => {
    const boardElement = document.getElementById('board');
    const turnInfo = document.getElementById('turn-info');
    let player = null;
    let isGameFinished = false;

    function renderBoard(board) {
        boardElement.innerHTML = '';
        for (let y = 0; y < 16; y++) {
            const row = document.createElement('tr');
            for (let x = 0; x < 16; x++) {
                const cell = document.createElement('td');
                cell.dataset.x = x;
                cell.dataset.y = y;

                const stone = board.find(stone => stone.x === x && stone.y === y);
                if (stone) {
                    const stoneDiv = document.createElement('div');
                    stoneDiv.classList.add(stone.player === 1 ? 'player1' : 'player2');
                    cell.appendChild(stoneDiv);
                }

                cell.addEventListener('click', () => makeMove(x, y));
                row.appendChild(cell);
            }
            boardElement.appendChild(row);
        }
    }

    async function makeMove(x, y) {
        if (!player || isGameFinished) return;

        const res = await fetch('/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ x, y, player })
        });
        const result = await res.json();

        if (result.status === "error") {
            alert(result.message);
        } else {
            await updateGameState(result.is_finished, result.winner);
        }
    }

    async function updateGameState(finished, winner = null) {
        const response = await fetch('/status');
        const data = await response.json();

        isGameFinished = finished ?? data.is_finished;
        renderBoard(data.board);
        turnInfo.textContent = isGameFinished 
            ? `Game Over${winner ? ` - Player ${winner} wins!` : ''}` 
            : `Player ${data.current_turn}'s Turn`;

        if (isGameFinished) {
            setTimeout(() => window.location.href = '/end', 2000);
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
            updateGameState(); // 초기 보드 업데이트
        }
    }

    joinGame();
    setInterval(updateGameState, 1000);
});
