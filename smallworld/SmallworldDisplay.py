import numpy as np
from copy import deepcopy
from SmallworldConstants import *
from SmallworldMaps import *

############################# PRINT GAME ######################################

terrains_str = [
	['', ''], # FORESTT
	['', ''], # FARMLAND
	['', ''], # HILLT
	['', ''], # SWAMPT
	['', ''], # MOUNTAIN
	['', ''], # WATER
]
powers_str = [' ', '⅏','ℵ', '⍎']

ppl_str      = [' ', 'A' , 'D' , 'E', 'g', 'G' , 'h', 'H' , 'O' , 'R' , 's', 'S' , 't', 'T' , 'W' , 'l']
ppl_decl_str = [' ', '🄐', '🄓', '🄔', '🄖', '🄖', '🄗', '🄗', '🄞', '🄡', '🄢', '🄢', '🄣', '🄣', '🄦', '🄛']
ppl_long_str = [' ', 'AMAZON','DWARF','ELF','GHOUL','GIANT','HALFLING','HUMAN','ORC','RATMAN','SKELETON','SORCERER','TRITON','TROLL','WIZARD', 'LOST_TRIBE']
power_long_str = [' ','ALCHEMIST','BERSERK','BIVOUACKING','COMMANDO','DIPLOMAT','DRAGONMASTER', 'FLYING','FOREST','FORTIFIED','HEROIC','HILL','MERCHANT','MOUNTED','PILLAGING','SEAFARING','SPIRIT','STOUT','SWAMP','UNDERWORLD','WEALTHY']
ac_or_dec_str = ['decline-spirit ppl', 'decline ppl', 'active ppl', '']
status_str = [
	'',
	'is ready to play',
	'chose new ppl',
	'abandoned',
	'attacked',
	'attacked with dice',
	'forced to abandon (amazon)',
	'redeployed',
	'to decline (stout)',
	'is waiting',
]

last_board, last_board_already_displayed = None, False

def generate_background():
	display_matrix = deepcopy(map_display)
	for y in range(DISPLAY_HEIGHT):
		for x in range(DISPLAY_WIDTH):
			area, _ = map_display[y][x]
			terrain = descr[area][0]
			display_matrix[y][x] = deepcopy(terrains_str[terrain])
			display_matrix[y][x].append('.')

	return display_matrix

def add_text(display_matrix, territories):
	for y in range(DISPLAY_HEIGHT):
		for x in range(DISPLAY_WIDTH):
			area, txt = map_display[y][x]
			if txt == 1 and territories[area,0] > 0:
				display_matrix[y][x][2] = str(territories[area,0])
				if territories[area,1] >= 0:
					display_matrix[y][x][2] += ppl_str     [ territories[area,1]]
				else:
					display_matrix[y][x][2] += ppl_decl_str[-territories[area,1]]					
			elif txt == 2:
				display_matrix[y][x][2] = f'{area:2}'
			elif txt == 3:
				display_matrix[y][x][2] = ''
				for i in range(1, 4):
					if descr[area][i]:
						display_matrix[y][x][2] += powers_str[i]
				display_matrix[y][x][2] += ' ' * (2-len(display_matrix[y][x][2]))
			elif txt == 4 and territories[area, 3:5].sum() > 0:
				if territories[area, 3:5].sum() >= IMMUNITY:
					display_matrix[y][x][2] = '**'
				else:
					display_matrix[y][x][2] = '+' + str(territories[area, 3:5].sum())
			else:
				display_matrix[y][x][2] = '  '
				
	return display_matrix

def add_legend(display_matrix, peoples):
	display_matrix[0].append(['', '  '])
	display_matrix[0].append(terrains_str[0] + ['forest'])
	display_matrix[0].append(['', ' '])
	display_matrix[0].append(terrains_str[1] + ['farmland'])
	display_matrix[0].append(['', ' '])
	display_matrix[0].append(terrains_str[2] + ['hill'])
	display_matrix[0].append(['', ' '])
	display_matrix[0].append(terrains_str[3] + ['swamp'])
	display_matrix[0].append(['', ' '])
	display_matrix[0].append(terrains_str[4] + ['mountain'])

	legend_power = '  '
	legend_power += powers_str[1] + ' = cavern , '
	legend_power += powers_str[2] + ' = magic , '
	legend_power += powers_str[3] + ' = mine , '
	display_matrix[1].append(['', legend_power])

	legend_ppl = '  '
	for i in range(NUMBER_PLAYERS):
		for j in range(3):
			ppl, power, pplinfo, powerinfo = abs(peoples[i,j,1:5])
			if ppl != NOPPL:
				short_str = ppl_str[ppl] if j == ACTIVE else ppl_decl_str[ppl]
				legend_ppl += f'{short_str} = {ppl_long_str[ppl]}'
				if power != NOPOWER:
					legend_ppl += f'+{power_long_str[power]}'
				if pplinfo != 0 or powerinfo != 0:
					pplinfo_str = str(pplinfo) if pplinfo < 64 else (str(pplinfo%64)+'*')
					pwrinfo_str = str(powerinfo) if powerinfo < 64 else (str(powerinfo%64)+'*')
					legend_ppl += f' ({pplinfo_str}-{pwrinfo_str})'
				legend_ppl += f', '
	display_matrix[2].append(['', legend_ppl])

	return display_matrix

def add_players_status(display_matrix, peoples, round_status, game_status):
	for p in range(NUMBER_PLAYERS):
		description = f'  P{p}: sc={game_status[p,6]+SCORE_OFFSET:2} #{game_status[p,3]} netwdt={round_status[p,3]}'
		description += f' - has {peoples[p,ACTIVE,0]}ppl "{ppl_str[peoples[p,ACTIVE,1]]}"'
		if peoples[p,DECLINED,1] != NOPPL:
			description += f' and "{ppl_decl_str[-peoples[p,DECLINED,1]]}"'
		if peoples[p,DECLINED_SPIRIT,1] != NOPPL:
			description += f' and "{ppl_decl_str[-peoples[p,DECLINED_SPIRIT,1]]}"'
		if round_status[p, 4] != PHASE_WAIT:
			description += f', {ac_or_dec_str[game_status[p, 4]]} {status_str[round_status[p, 4]]}'
		display_matrix[6+p].append(['', description])
	return display_matrix

def add_deck(display_matrix, visible_deck):
	for index, range_beg, range_end in [(3, 0, DECK_SIZE//2), (4, DECK_SIZE//2, DECK_SIZE)]:
		deck_str = f'  Deck:' if index == 3 else f'       '
		for i in range(range_beg, range_end):
			nb, ppl, power, coins = visible_deck[i,0], visible_deck[i,1], visible_deck[i,2], visible_deck[i,6]
			description = f'{nb}x{ppl_long_str[ppl].lower()[:8]}-{power_long_str[power].lower()[:8]}'
			if coins > 0:
				description += f'+{coins}'
			deck_str += f' {i} = {description:22}'
		display_matrix[index].append([deck_str])

	return display_matrix

def disp_to_str(display_matrix):
	disp_str = ''
	for y in range(len(display_matrix)):
		for x in range(len(display_matrix[y])):
			bgd, fgd, txt = display_matrix[y][x]
			disp_str += bgd + fgd + txt
		disp_str += ('\n' if y < len(display_matrix)-1 else '')
	return disp_str

def which_board_to_print(prev_board, cur_board):
	if prev_board is None:
		return cur_board

	prev_player = np.argwhere(prev_board.round_status[:, 4] != PHASE_WAIT)[0][0]
	prev_phase, cur_phase = prev_board.round_status[prev_player, 4], cur_board.round_status[prev_player, 4]
	if prev_phase == cur_phase or (prev_phase, cur_phase) in [(PHASE_ABANDON, PHASE_CONQUEST)]:
		return None
	if cur_phase in [PHASE_CHOOSE, PHASE_CONQ_WITH_DICE, PHASE_WAIT]:
		return cur_board
	return prev_board

def print_board(b):
	global last_board, last_board_already_displayed
	board_to_print = which_board_to_print(last_board, b)
	if board_to_print is not None and not (last_board is not None and np.array_equal(board_to_print.state, last_board.state) and last_board_already_displayed):
		display_matrix = generate_background()
		display_matrix = add_text(display_matrix, board_to_print.territories)
		display_matrix = add_legend(display_matrix, board_to_print.peoples)
		display_matrix = add_deck(display_matrix, board_to_print.visible_deck)
		display_matrix = add_players_status(display_matrix, board_to_print.peoples, board_to_print.round_status, board_to_print.game_status)
		
		display_str = disp_to_str(display_matrix)
		print(display_str)

		last_board_already_displayed = np.array_equal(board_to_print.state, b.state)		
	else:
		last_board_already_displayed = False
	last_board = deepcopy(b)

# Used for debug purposes
def print_valids(p, valids_attack, valids_special, valids_abandon, valids_redeploy, valids_specialpwr, valids_choose, valid_decline, valid_end):
	print(f'Valids: P{p} can', end='')
	if valids_attack.any():
		print(f' attack area', end='')
		for i in valids_attack.nonzero()[0]:
			print(f' {i}', end='')
		print(', or', end='')

	if valids_special.any():
		print(f' specialPPL on', end='')
		for i in valids_special.nonzero()[0]:
			print(f' {i}', end='')
		print(', or', end='')

	if valids_abandon.any():
		print(f' abandon area', end='')
		for i in valids_abandon.nonzero()[0]:
			print(f' {i}', end='')
		print(', or', end='')

	if valids_redeploy.any():
		valids_on_each = valids_redeploy[:MAX_REDEPLOY]
		if valids_on_each.any():
			maxi = valids_on_each.nonzero()[0].max()
			if maxi > 0:
				print(f' redeploy up to {maxi}ppl on each area', end='')
			else:
				print(f' skip redeploy', end='')
		else:
			print(f' redeploy on area', end='')
			for i in valids_redeploy.nonzero()[0]:
				print(f' {i-MAX_REDEPLOY}', end='')
		print(', or', end='')

	if valids_specialpwr.any():
		print(f' specialPWR on', end='')
		for i in valids_specialpwr.nonzero()[0]:
			print(f' {i}', end='')
		print(', or', end='')

	if valids_choose.any():
		print(f' chose a new people', end='')
		if np.count_nonzero(valids_choose) < 6:
			for i in valids_choose.nonzero()[0]:
				print(f' {i}', end='')
		print(', or', end='')

	if valid_decline:
		print(f' decline current people, or', end='')

	if valid_end:
		print(f' end turn', end='')

	print('.')

def move_to_str(move, player=0):
	if   move < NB_AREAS:
		area = move
		return f'Abandon {area}'
	elif move < 2*NB_AREAS:
		area = move - NB_AREAS
		return f'Attack {area}'
	elif move < 3*NB_AREAS:
		area = move - 2*NB_AREAS
		return f'Special ppl move {area}'
	elif move < 4*NB_AREAS:
		area = move - 3*NB_AREAS
		return f'Special power {area}'
	elif move < 5*NB_AREAS+MAX_REDEPLOY:
		param = move - 4*NB_AREAS
		if param == 0:
			return f'skip redeploy'
		elif param < MAX_REDEPLOY:
			return f'Redeploy {param}ppl on each area'
		else:
			return f'Redeploy 1ppl on area {param-MAX_REDEPLOY}'
	elif move < 5*NB_AREAS+MAX_REDEPLOY+DECK_SIZE:
		area = move - 5*NB_AREAS-MAX_REDEPLOY
		return f'Choose people {area}'
	elif move < 5*NB_AREAS+MAX_REDEPLOY+DECK_SIZE+1:
		return f'Decline'
	elif move < 5*NB_AREAS+MAX_REDEPLOY+DECK_SIZE+2:
		return f'Is done'
	else:
		print(f'Unknown move {move}')
		breakpoint()


