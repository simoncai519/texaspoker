# also simulate other players' card
# take their current betting into account, if big bet, then boost their card or level
# boost by taking upper subset of simulation result
# consider the variance of simulation output

from modules.texaspoker.lib.client_lib import State
from modules.texaspoker.lib.client_lib import Player
from modules.texaspoker.lib.client_lib import Hand
from modules.texaspoker.lib.client_lib import Decision
from modules.texaspoker.lib.client_lib import judge_two
import random




def ai(id, state):
	shared_cards = state.sharedcards.copy()
	my_cards = state.player[id].cards
	remain_card = list(range(0, 52))
	for x in shared_cards:
		remain_card.pop(remain_card.index(x))
	for x in my_cards:
		remain_card.pop(remain_card.index(x))
	# guess other player's card strength based on their betting
	alive_players = []
	for player_id in range(len(state.player)):
		if state.player[id].active & player_id != id:
			alive_players.append(state.player[id])

	for player in alive_players:
		guess_card_list = []
		for i in range(1000):
			guess_card = []
			heap = remain_card[:]
			random.shuffle(heap)
			guess_card.append(heap.pop())
			guess_card.append(heap.pop())
			for i in range(100):
				pass

	# 模拟发牌1000次
	def simulate_win_rate(inhand_cards, other_player_cards = []):
		win_count = 0
		_remain_card = list(range(0, 52))
		for x in shared_cards:
			_remain_card.pop(remain_card.index(x))
		for x in inhand_cards:
			_remain_card.pop(remain_card.index(x))

		for i in range(1000):
			score = 0
			for player in range(len(alive_players)):
				player_cards = []
				if len(other_player_cards) == 0:
					player_cards.append(heap.pop())
					player_cards.append(heap.pop())
					player_cards = player_cards
					# player_hand = Hand(player_cards)
					other_player_cards.append(player_cards)

				else:
					pass
					# player_hand = other_player_cards[player].

			shared_cards_sim = shared_cards
			my_cards_sim = inhand_cards
			heap = remain_card[:]
			random.shuffle(heap)
			while len(shared_cards_sim) < 5:
				shared_cards_sim.append(heap.pop())
			my_cards_sim = my_cards_sim + shared_cards
			# my_hand = Hand(my_cards_sim)
			# other_player = []


			score += judge_two(my_cards_sim, player_cards)
			if score == -len(alive_players):
				win_count += 1

		win_rate = win_count / 1000

		return win_rate
	my_win_rate = simulate_win_rate(inhand_cards = my_cards)
	decision = Decision()

	def add_bet(state, total):
		# amount: 本局需要下的总注
		amount = total - state.player[state.currpos].totalbet
		assert (amount > state.player[state.currpos].bet)
		# Obey the rule of last_raised
		minamount = state.last_raised + state.minbet
		real_amount = max(amount, minamount)
		# money_needed = real_amount - state.player[state.currpos].bet
		decision.raisebet = 1
		decision.amount = int(real_amount)
		return decision

	delta = state.minbet - state.player[state.currpos].bet

	target = my_win_rate**5 * state.player[state.currpos].money
	if (state.player[state.currpos].bet + state.player[state.currpos].totalbet) >= target:
		if delta == 0:
			decision.callbet = 1
		else:
			decision.giveup = 1
	else:
		decision = add_bet(state, target)
	return decision


