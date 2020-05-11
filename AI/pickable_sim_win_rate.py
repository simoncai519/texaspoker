import random
from modules.texaspoker.lib.client_lib import judge_two

def pickable_simulate_win_rate(guess_card_, iterate=22, alive_players_num = 5):
	in_hand_cards = guess_card_.cards
	win_count = 0
	shared_cards = guess_card_.shared_cards
	_remain_card = list(range(0, 52))
	for x in shared_cards:
		_remain_card.pop(_remain_card.index(x))
	for x in in_hand_cards:
		_remain_card.pop(_remain_card.index(x))

	# iterate, simulate unguessed players' cards, shared cards
	for i in range(iterate):
		_remain_card_sim = _remain_card.copy()
		other_players_cards_sim = []

		random.shuffle(_remain_card_sim)

		for player in range(alive_players_num):
			player_cards = []
			player_cards.append(_remain_card_sim.pop())
			player_cards.append(_remain_card_sim.pop())
			# player_hand = Hand(player_cards)
			other_players_cards_sim.append(player_cards)

		shared_cards_sim = shared_cards.copy()
		my_cards_sim = in_hand_cards.copy()
		random.shuffle(_remain_card_sim)
		while len(shared_cards_sim) < 5:
			shared_cards_sim.append(_remain_card_sim.pop())

		my_cards_shared_cards_sim = my_cards_sim + shared_cards_sim
		# my_hand = Hand(my_cards_sim)

		win = 0
		even = 0
		assert (alive_players_num == len(other_players_cards_sim))
		survive = True
		for other_player_cards_sim in other_players_cards_sim:
			compare = judge_two(other_player_cards_sim + shared_cards_sim, my_cards_shared_cards_sim)
			if compare == 0:
				even += 1
			if compare == -1:
				survive = False
			if compare == 1:
				win += 1
		if win == alive_players_num:
			win_count += 1
		# if even, counted as
		elif survive == True:
			win_count += 1 / (even + 1)

	win_rate = win_count / iterate
	guess_card_.win_rate = win_rate
	return guess_card_

import functools

'''

def round2_iter_func(item):
	guess_cards_ = item.guess_cards_round2
	item._remain_card_comb
	if last_card not in guess_cards_.cards:
		guess_cards_.rank_list.append(_remain_card_comb.index(guess_cards_.cards) / len(_remain_card_comb))
	return remain_card_comb_class
	
'''