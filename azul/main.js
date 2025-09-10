// Import common/game.js before this file

/* =================== */
/* =====  CONST  ===== */
/* =================== */


const list_of_files = [
  ['azul/Game.py', 'Game.py'],
  ['azul/proxy.py', 'proxy.py'],
  ['azul/MCTS.py', 'MCTS.py'],
  ['azul/AzulGame.py', 'AzulGame.py'],
  ['azul/AzulLogic.py', 'AzulLogic.py'],
  ['azul/AzulLogicNumba.py', 'AzulLogicNumba.py'],
];

const defaultModelFileName = 'azul/model.onnx';

const sizeCB = [1, 23, 6];
const sizeV = [1, 180];

/* =================== */
/* =====  UTILS  ===== */
/* =================== */

/* =================== */
/* =====  LOGIC  ===== */
/* =================== */

class Azul extends AbstractGame {
  constructor() {
    super()
    this.validMoves = Array(sizeV[1]); this.validMoves.fill(false);
  }

  post_init_game() {
  }

  pre_move(action, manualMove) {
  }

  post_move(action, manualMove) {
  }

  post_set_data() {
  }

  has_changed_on_last_move(item_vector) {
    return 0;
  }

  getBoard() {
    return this.py.getBoard();
  }
}

class MoveSelector extends AbstractMoveSelector {}

function moveToString(move, gameMode) {
  return ''
}

function submitMove() {
  // Get dropdown values
  const factory = $('#factorySelect').dropdown('get value');
  const colour = $('#colourSelect').dropdown('get value');
  const line = $('#lineSelect').dropdown('get value');

  // Mapping for factory
  const factoryMap = { 'C': 0, 'F1': 1, 'F2': 2, 'F3': 3, 'F4': 4, 'F5': 5 };

  // Mapping for colour
  const colourMap = { 'Blue': 0, 'Yellow': 1, 'Red': 2, 'Black': 3, 'White': 4 };

  // Mapping for line
  const lineMap = { '1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5 };

  // Encode into move number
  const move = 30 * factoryMap[factory] + 6 * colourMap[colour] + lineMap[line];

  // Push into the original input so userMove() works unchanged
  document.getElementById('userMoveID').value = move;

  const moveBtn = document.getElementById('moveBtn');

  if (!game.validMoves[move]) {
    // Flash red if invalid
    moveBtn.classList.add('red');
    setTimeout(() => moveBtn.classList.remove('red'), 200);
    return;
  }

  // Otherwise perform the move
  userMove();

  // Flash green for valid move
  moveBtn.classList.add('green');
  setTimeout(() => moveBtn.classList.remove('green'), 200);
}

/* =================== */
/* ===== DISPLAY ===== */
/* =================== */

function userMove() {
  let move = Number(document.getElementById('userMoveID').value);
  game.move(move, true);
  move_sel.reset();
  refreshBoard();
  const moveSgmt = document.getElementById('moveSgmt');
  moveSgmt.textContent = `Player plays ${game.py.move_to_str(move)}`;

  ai_play_if_needed();
}

function refreshBoard() {
  console.log('refresh board');
  const boardSgmt = document.getElementById('boardSgmt');

  // Get full board HTML from Python
  let boardHTML = game.py.getBoard();

  // Access final scores from Python
  const scores = game.py.g.board.scores.toJs ? game.py.g.board.scores.toJs() : game.py.g.board.scores;
  const p1Score = scores[0][0];
  const p2Score = scores[0][1];

  // Create a temporary DOM element to manipulate HTML
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = boardHTML;

  if (game.gameEnded.some(x => !!x)) {
    // Remove factories and centre
    tempDiv.querySelectorAll('div[style*="min-width:120px"], div[style*="margin-bottom:10px; border:1px solid #333; padding:5px"]').forEach(el => el.remove());

    let winnerText = '';
    if (game.gameEnded[0]) winnerText = 'Player 1 wins!';
    else if (game.gameEnded[1]) winnerText = 'Player 2 wins!';
    else winnerText = 'Tie!';

    // Add final score header at the top
    const scoreDiv = document.createElement('div');
    scoreDiv.style = "text-align:center; padding:10px; border:1px solid #333; border-radius:6px; background:#f0f0f0; margin-bottom:10px;";
    scoreDiv.innerHTML = `
      <h2>Game Over</h2>
      <p><strong>Final Scores:</strong></p>
      <p>Player 1: ${p1Score}</p>
      <p>Player 2: ${p2Score}</p>
      <h3>${winnerText}</h3>
    `;
    tempDiv.prepend(scoreDiv);
  }

  // Render the modified HTML
  boardSgmt.innerHTML = tempDiv.innerHTML;
}

function refreshButtons(loading=false) {
}

function refreshPlayersText() {
}

function changeMoveText() {
}

/* =================== */
/* ===== ACTIONS ===== */
/* =================== */


var game = new Azul();
var move_sel = new MoveSelector();
