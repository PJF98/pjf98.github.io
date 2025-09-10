// Variables to declare in game code
// let game = new Splendor();
// let move_sel = new MoveSelector();
// const sizeCB = [1, 25, 3];
// const sizeV = [1, onnxOutputSize];
// const list_of_files;


/* =================== */
/* =====  ONNX   ===== */
/* =================== */

let onnxSession;

// Function called by python code
async function predict(canonicalBoard, valids) {
  const cb_js = Float32Array.from(canonicalBoard.toJs({create_proxies: false}));
  const vs_js = Uint8Array.from(valids.toJs({create_proxies: false}));
  const tensor_board = new ort.Tensor('float32', cb_js, sizeCB);
  const tensor_valid = new ort.Tensor('bool'   , vs_js, sizeV);
  // console.log('canonicalboard:', tensor_board);
  // console.log('valid:', tensor_valid);
  const results = await globalThis.onnxSession.run({ board: tensor_board, valid_actions: tensor_valid });
  // console.log('results:', results);
  return {pi: Array.from(results.pi.data), v: Array.from(results.v.data)}
}

async function loadONNX(model) {
  globalThis.onnxSession = await ort.InferenceSession.create(defaultModelFileName);
  console.log('Loaded default ONNX');
}

/* =================== */
/* =====  LOGIC  ===== */
/* =================== */

class AbstractGame {
  constructor() {
    if (this.constructor == AbstractGame) {
      throw new Error("Abstract classes can't be instantiated.");
    }

    this.py = null;             // Python wrapper
    this.nextPlayer = 0;        // ID of next player
    this.previousPlayer = null; // ID of previous player
    this.gameEnded = [0, 0];    // Has player P won, for each player
    this.gameMode = 'P0';       // "P0" or "P1" to define which player is human or "AI" for AIs only or "human" for no AI
    this.numMCTSSims = 25;      // Number of MCTS simulations per move

    // To define in extended class
    this.validMoves = null;     // Array boolean with valid moves 
  }

  init_game() {
    this.nextPlayer = 0;
    this.previousPlayer = null;
    this.gameEnded = [0, 0];
    this.gameMode = 'P0';
    this.validMoves.fill(false);
    
    // Python init
    if (this.py == null) {
      console.log('Now importing python module');
      this.py = pyodide.pyimport("proxy");
    }
    let data_tuple = this.py.init_game(this.numMCTSSims).toJs({create_proxies: false});
    [this.nextPlayer, this.gameEnded, this.validMoves] = data_tuple;

    this.post_init_game();
  }

  move(action, isManualMove) {
    if (this.is_ended()) {
      console.log('Cant move, game is finished');
    } else if (!this.validMoves[action]) {
      console.log('Not a valid action', this.validMoves);
    } else {
      this.pre_move(action, isManualMove);

      // Actually move
      this.previousPlayer = this.nextPlayer;
      let data_tuple = this.py.getNextState(action).toJs({create_proxies: false});
      [this.nextPlayer, this.gameEnded, this.validMoves] = data_tuple;

      this.post_move(action, isManualMove);
    }  
  }

  async ai_guess_and_move() {
    if (this.is_ended()) {
      console.log('Not guessing, game is finished');
      return;
    }
    await this.ready_to_guess();
    const best_action = await this.py.guessBestAction();
    this.move(best_action, false);
  }

  async ready_to_guess() {  
  }

  revert_to_previous_human_move() {
    let player = this.who_is_human();
    let data_tuple = this.py.revert_to_previous_move(player).toJs({create_proxies: false});
    [this.nextPlayer, this.gameEnded, this.validMoves] = data_tuple;
    this.previousPlayer = null;
    this.post_set_data();
  }

  // ----- UTILS METHODS -----

  change_difficulty(numMCTSSims) {
    this.numMCTSSims = Number(numMCTSSims);
    this.py.changeDifficulty(this.numMCTSSims);
  }

  is_ended() {
    return this.gameEnded.some(x => !!x);
  }

  is_human_player(player) {
    if (this.gameMode == 'AI') {
      return false;
    } else if (this.gameMode == 'Human') {
      return true;
    }


    if (player == 'next') {
      player = this.nextPlayer;
    } else if (player == 'previous') {
      player = this.previousPlayer;
    }
    return player == ((this.gameMode == 'P0') ? 0 : 1);
  }

  who_is_human() {
    return (this.gameMode == 'P0') ? 0 : 1;
  }

  // ----- METHODS TO EXTEND -----

  post_init_game() {}
  pre_move(action, isManualMove) {}
  post_move(action, isManualMove) {}
  post_set_data() {}
  has_changed_on_last_move(item_vector) {}
}

/* =================== */
/* ===== DISPLAY ===== */
/* =================== */


class AbstractDisplay {
  refreshBoard() {}

  refreshButtons(loading=false) {}
}

class AbstractMoveSelector {
  constructor() {
    this.stage = 0;
    this.resetAndStart();
  }

  resetAndStart() {
    this.reset();
    this.start();
  }

  reset() { }

  start() { }

  // return move, or -1 if move is undefined
  getMove() {}

  edit() {}
}

/* =================== */
/* ===== ACTIONS ===== */
/* =================== */

let ai_play_promise = Promise.resolve();

async function ai_play_one_move() {
  refreshButtons(loading=true);
  let aiPlayer = game.nextPlayer;
  while ((game.nextPlayer == aiPlayer) && game.gameEnded.every(x => !x)) {
    await game.ai_guess_and_move();
    refreshBoard();
  }
  refreshButtons(loading=false);
}

async function ai_play_if_needed_async() {
  let did_ai_played = false;
  while (game.gameEnded.every(x => !x) && !game.is_human_player('next')) {
    await ai_play_one_move();
    
    did_ai_played = true;
    refreshBoard();
    refreshButtons();
    changeMoveText(moveToString(game.lastMove, 'AI'), 'add');
  }

  if (did_ai_played) {
    move_sel.resetAndStart();
  }
  refreshBoard();
  refreshButtons();
}

ai_play_if_needed = function(...args) {
  ai_play_promise = ai_play_if_needed_async.apply(this, args);
  return ai_play_promise;
};

async function changeGameMode(mode) {
  game.gameMode = mode;
  await ai_play_promise;
  move_sel.resetAndStart();
  await ai_play_if_needed();
}


function reset() {
  game.init_game();
  move_sel.resetAndStart();

  refreshBoard();
  refreshPlayersText();
  refreshButtons();
  changeMoveText();
}

function cancel_and_undo() {
  if (move_sel.stage == 0) {
    game.revert_to_previous_human_move();
  }
  move_sel.resetAndStart();

  refreshBoard();
  refreshButtons();
  changeMoveText();
}


function edit() {
  move_sel.edit();
  refreshBoard();
  refreshButtons();
  refreshPlayersText();
}

/* =================== */
/* ===== PYODIDE ===== */
/* =================== */

// init Pyodide and stuff
async function init_code() {
  pyodide = await loadPyodide({ fullStdLib: false });
  await pyodide.loadPackage("numpy");

  // Always reload files freshly into /home/pyodide
  for (const [filename_in, filename_out] of list_of_files) {
    try {
      // Delete old file if it exists
      pyodide.FS.unlink(filename_out);
    } catch (e) {
      // Ignore if file didn't exist
    }

    const response = await fetch(filename_in, { cache: "no-store" }); // bypass browser cache
    const data = await response.arrayBuffer();
    pyodide.FS.writeFile(filename_out, new Uint8Array(data));
  }

  // Build a Python list of module names based on your list_of_files
  const modules = list_of_files
    .map(([_, filename_out]) => filename_out.replace(".py", ""))
    .join(", ");

  // Reload all those modules if they were already imported
  await pyodide.runPythonAsync(`
import sys, importlib
for mod in [${modules.split(", ").map(m => `"${m}"`).join(", ")}]:
    if mod in sys.modules:
        importlib.reload(sys.modules[mod])
  `);

  loadONNX(); // Not "await" on purpose
  console.log("Loaded python code, pyodide ready");
}

async function main(usePyodide=true) {
  refreshButtons(loading=true);

  if (usePyodide) {
    await init_code();
  }
  game.init_game();
  move_sel.resetAndStart();

  refreshBoard();
  refreshPlayersText();
  refreshButtons();
  changeMoveText();
}

let pyodide = null;
