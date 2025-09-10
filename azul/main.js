// Import common/game.js before this file

/* =================== */
/* =====  CONST  ===== */
/* =================== */

// Here are common constants between nogod and god modes.
// Check also constants_*.js

const directions_char = ['↖', '↑', '↗', '←', 'Ø', '→', '↙', '↓', '↘'];

const green = '#21BA45';
const red   = '#DB2828';

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

/* =================== */
/* ===== DISPLAY ===== */
/* =================== */

function userMove() {
  let move = Number(document.getElementById('userMoveID').value);
  game.move(move, true);
  move_sel.reset();
  refreshBoard();
  refreshButtons();

  ai_play_if_needed();
}

function refreshBoard() {
  console.log('refresh board');
  document.getElementById('boardSgmt').innerHTML = game.getBoard();
}

function refreshButtons(loading=false) {
  console.log('refresh buttons');
  if (!loading) {
    allBtn.style = "";
    loadingBtn.style = "display: none";
  }
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
