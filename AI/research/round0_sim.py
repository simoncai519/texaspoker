import random
import sys
sys.path.append("/Users/Simon-CWG/Documents/quantresearch/Texaspoker")
from modules.texaspoker.lib.client_lib import judge_two
from modules.texaspoker.AI.simon_ai import guess_cards

shared_cards = []
alive_players_num = 5

def simulate_win_rate(in_hand_cards, bold_better_list = [], iterate=5000):
    win_count = 0
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
        for _bold_better in bold_better_list:
            player_cards = random.choice(_bold_better.card_guess)
            other_players_cards_sim.append(player_cards)
            for x in player_cards:
                if x in _remain_card_sim:
                    _remain_card_sim.pop(_remain_card_sim.index(x))

        for player in range(alive_players_num - len(bold_better_list)):
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
    return win_rate

from itertools import combinations

full_card_set = combinations(list(range(0, 52)), 2)
full_card_set = list(full_card_set)


pair_score = {}
for index in range(len(full_card_set)):
	print(index)
	pair = full_card_set[index]
	pair_score[pair] = simulate_win_rate(list(pair))

import pickle

pickle.dump(pair_score, open('pair_score_sorted_v2', 'wb'))