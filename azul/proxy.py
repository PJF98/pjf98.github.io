from MCTS import MCTS
from AzulGame import AzulGame as Game
from AzulLogic import move_to_str
import numpy as np
from js import document

g, board, mcts, player = None, None, None, 0
history = []  # Previous states (new to old, not current). Each is an array with player and board and action


class dotdict(dict):
    def __getattr__(self, name):
        return self[name]


def init_game(numMCTSSims):
    global g, board, mcts, player, history

    mcts_args = dotdict({
        'numMCTSSims': numMCTSSims,
        'fpu': 0.05,
        'cpuct': 0.5,
        'universes': 4,
        'prob_fullMCTS': 1.,
        'forced_playouts': False,
        'no_mem_optim': False,
        })

    g = Game()
    board = g.getInitBoard()
    mcts = MCTS(g, None, mcts_args)
    player = 0
    valids = g.getValidMoves(board, player)
    end = [0, 0]

    return player, end, valids


def getNextState(action):
    global g, board, mcts, player, history
    history.insert(0, [player, np.copy(board), action])
    board, player = g.getNextState(board, player, action)
    end = g.getGameEnded(board, player)
    valids = g.getValidMoves(board, player)
    return player, end, valids


def changeDifficulty(numMCTSSims):
    global g, board, mcts, player, history
    mcts.args.numMCTSSims = numMCTSSims
    print('Difficulty changed to', mcts.args.numMCTSSims)


async def guessBestAction():
    global g, board, mcts, player, history
    probs, _, _ = await mcts.getActionProb(g.getCanonicalForm(board, player), force_full_search=True)
    g.board.copy_state(board, True)  # g.board was in canonical form, set it back to normal form
    best_action = max(range(len(probs)), key=lambda x: probs[x])

    # Compute good moves
    print('List of best moves found by AI:')
    sorted_probs = sorted([(action, p) for action, p in enumerate(probs)], key=lambda x: x[1], reverse=True)
    for i, (action, p) in enumerate(sorted_probs):
        if p < sorted_probs[0][1] / 3. or i >= 3:
            break
        print(f'{int(100*p)}% [{action}] {move_to_str(action)}')

    move_sgmt = document.getElementById("moveSgmt")
    move_sgmt.innerHTML = f"AI plays {move_to_str(best_action)}"
    return best_action


def revert_to_previous_move(player_asking_revert):
    global g, board, mcts, player, history
    if len(history) > 0:
        # Revert to the previous 0 before a 1, or first 0 from game
        for index, state in enumerate(history):
            if (state[0] == player_asking_revert) and (index+1 == len(history) or history[index+1][0] != player_asking_revert):
                break
        print(f'index={index} / {len(history)}')

        # Actually revert, and update history
        # print(f'Board to revert: {state[1]}')
        player, board = state[0], state[1]
        history = history[index+1:]

    end = g.getGameEnded(board, player)
    valids = g.getValidMoves(board, player)
    return player, end, valids


def get_last_action():
    global g, board, mcts, player, history

    if len(history) < 1:
        return None
    return history[0][2]

# -----------------------------------------------------------------------------


def get_scores():
    return g.board.scores.tolist()


def getBoard():
    color_map = {
        -1: "#eee",   # empty / unassigned
        0: "blue",
        1: "yellow",
        2: "red",
        3: "black",
        4: "white",
        5: "green",   # first player token (centre)
    }

    wall_colors = ["blue", "yellow", "red", "black", "white"]

    def render_tiles(arr, duplicates=False, show_count=False, gap=8, text_gap=6):
        html = '<div style="display:flex; gap:{}px; justify-content:center; align-items:flex-start;">'.format(gap)
        for colour, count in enumerate(arr):
            if count == 0 and not show_count:
                continue
            num_circles = int(count) if duplicates else 1
            html += '<div style="display:flex; flex-direction:column; align-items:center;">'
            html += '<div style="display:flex; gap:{}px; margin-top:{}px;">'.format(gap, text_gap)
            for _ in range(num_circles):
                html += f'<span style="display:inline-block; width:24px; height:24px; border-radius:50%; background:{color_map[colour]}; border:1px solid #333;"></span>'
            html += '</div>'
            if show_count:
                html += f'<div style="font-size:14px; font-weight:bold; margin-top:4px;">{int(count)}</div>'
            html += '</div>'
        html += '</div>'
        return html

    def render_staircase(player_idx):
        html = '<div style="margin:0;">'
        for row in range(5):
            row_len = row + 1
            colour = g.board.player_colours[player_idx][row]
            count = g.board.player_row_numbers[player_idx][row]

            html += '<div style="margin:0 0 2px 0; height:22px; display:flex; align-items:center;">'
            for i in range(row_len):
                if i < count and colour != -1:
                    html += f'<span style="display:inline-block; width:22px; height:22px; margin-right:2px; border-radius:50%; background:{color_map[colour]}; border:1px solid #333;"></span>'
                else:
                    html += '<span style="display:inline-block; width:22px; height:22px; margin-right:2px; border-radius:50%; background:#f9f9f9; border:1px dashed #ccc;"></span>'
            html += '</div>'
        # Discards row (keep same height)
        discards = min(g.board.player_row_numbers[player_idx][5], 7)
        discard_values = [-1, -1, -2, -2, -2, -3, -3]
        html += '<div style="display:flex; gap:4px; margin-left:2px; margin-top:4px; align-items:flex-start;">'
        for i in range(discards):
            html += '<div style="text-align:center; display:flex; flex-direction:column; align-items:center;">'
            html += f'<span style="display:inline-block; width:12px; height:16px; font-weight:bold; color:red; line-height:16px;">&#10005;</span>'
            html += f'<span style="font-size:10px; line-height:10px;">{discard_values[i]}</span>'
            html += '</div>'
        html += '</div>'

        html += '</div>'
        return html

    def render_wall(player_idx):
        wall_start = 0 if player_idx == 0 else 5
        html = '<div style="display:flex; flex-direction:column; gap:2px; margin-left:10px;">'
        for row in range(5):
            html += '<div style="display:flex; gap:4px;">'
            for col in range(5):
                color_idx = (col - row) % 5
                val = g.board.player_walls[wall_start + row, col]
                opacity = 1.0 if val == 1 else 0.2
                html += f'<span style="display:inline-block; width:22px; height:22px; border-radius:3px; background:{wall_colors[color_idx]}; opacity:{opacity}; border:1px solid #333;"></span>'
            html += '</div>'
        html += '</div>'
        return html

    # Start assembling HTML
    result = ''

    # Styled scores with bag display
    result += '''
    <div style="border:1px solid #333; padding:10px; border-radius:6px; display:inline-block; margin-bottom:10px; background:#f0f0f0;">
        <div style="margin-bottom:6px; font-weight:bold;"><strong>Player 1 Score:</strong> {}</div>
        <div style="margin-bottom:6px; font-weight:bold;"><strong>Player 2 Score:</strong> {}</div>
        <div style="margin-top:10px; font-weight:bold;"><strong>Bag:</strong><br>{}</div>
    </div><br><br>
    '''.format(
        g.board.scores[0][0],
        g.board.scores[0][1],
        render_tiles(g.board.bag[0, :5], duplicates=False, show_count=True)
    )

    # Factories all in one row
    result += '<div style="display:flex; gap:10px; margin-bottom:10px;">'
    for i, factory in enumerate(g.board.factories):
        if sum(factory) > 0:
            result += f'<div style="border:1px solid #333; padding:5px; text-align:center; border-radius:6px; min-width:120px;">'
            result += f'<span style="font-weight:bold; font-size:16px;">F{i+1}</span><br>' + render_tiles(factory[:5], duplicates=True)
            result += '</div>'
    result += '</div>'

    # Centre
    result += '<div style="margin-bottom:10px; border:1px solid #333; padding:5px; display:inline-block; border-radius:6px;">'
    result += '<span style="font-weight:bold; font-size:16px;">C</span><br>' + render_tiles(g.board.centre[0, :6], duplicates=True)
    result += '</div><br><br>'

    # Player 1 staircase + wall
    fp1 = '<span style="display:inline-block; width:16px; height:16px; border-radius:50%; background:green; margin-left:4px;"></span>' if g.board.player_colours[0][5] == 1 else ''
    result += f'<h3>Player 1 {fp1}</h3>'
    result += '<div style="display:flex; gap:20px; align-items:flex-start;">'
    result += render_staircase(0)
    result += render_wall(0)  # now slightly bigger with margin-left
    result += '</div>'

    # Player 2 staircase + wall
    fp2 = '<span style="display:inline-block; width:16px; height:16px; border-radius:50%; background:green; margin-left:4px;"></span>' if g.board.player_colours[1][5] == 1 else ''
    result += f'<h3>Player 2 {fp2}</h3>'
    result += '<div style="display:flex; gap:20px; align-items:flex-start;">'
    result += render_staircase(1)
    result += render_wall(1)
    result += '</div>'

    return result
