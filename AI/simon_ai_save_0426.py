### Feqtures:
# 1. also simulate other players' card, done
# 2. take their current betting into account, if big bet, then boost their card or level
#    boost by taking upper subset of simulation result, done
#   2.1 only consider bold-better, for computation efficiency, done
# 3. consider give up cost, done
# 4. set different reaction when win rate is above or below certain threshold, done
# 5. consider the variance of simulation output
# 6. apply kelly criterion
# 7. gradually raise bet, so that other players are more likely to call
# 8. increasing confidence bar as round goes on, done
# 9. bluffing based on sharedcards
# 10. create first round cards-scoring data, save computation at round 0, but need to consider my hand...
# 11. modify decision when win rate is where high

from modules.texaspoker.lib.client_lib import State
from modules.texaspoker.lib.client_lib import Player
from modules.texaspoker.lib.client_lib import Hand
from modules.texaspoker.lib.client_lib import Decision
from modules.texaspoker.lib.client_lib import judge_two
import random
from modules.texaspoker.lib.simple_logger import file_logger as logger
import time





def ai(id, state, risk_averse = 2, log = True):
	start_time = time.time()
	shared_cards = state.sharedcards.copy()
	if len(shared_cards) == 0:
		round = 0
	elif len(shared_cards) == 3:
		round = 1
	elif len(shared_cards) == 4:
		round = 2
	else:
		round = 3
	my_cards = state.player[id].cards
	remain_card = list(range(0, 52))
	for x in shared_cards:
		remain_card.pop(remain_card.index(x))
	for x in my_cards:
		remain_card.pop(remain_card.index(x))
	# guess other player's card strength based on their betting
	alive_players = []
	for player_id in range(len(state.player)):
		if state.player[player_id].active & (player_id != id):
			alive_players.append(state.player[player_id])
	bold_better = []
	for alive_player in alive_players:
		total = alive_player.totalbet + alive_player.bet
		if total > 40:
			bold_better.append(alive_player)

	def simulate_win_rate(inhand_cards, other_player_cards=[], iterate = 1000):
		win_count = 0
		_remain_card = list(range(0, 52))
		for x in shared_cards:
			_remain_card.pop(_remain_card.index(x))
		for x in inhand_cards:
			_remain_card.pop(_remain_card.index(x))

		for i in range(iterate):
			heap = _remain_card.copy()
			other_player_cards_sim = []

			random.shuffle(heap)
			for player in range(len(other_player_cards)):
				player_cards = random.choice(other_player_cards[player])
				other_player_cards_sim.append(player_cards)
				for x in player_cards:
					if x in heap:
						heap.pop(heap.index(x))

			for player in range(len(alive_players) - len(other_player_cards)):
				player_cards = []
				player_cards.append(heap.pop())
				player_cards.append(heap.pop())
				# player_hand = Hand(player_cards)
				other_player_cards_sim.append(player_cards)

			shared_cards_sim = shared_cards.copy()
			my_cards_sim = inhand_cards.copy()
			random.shuffle(heap)
			while len(shared_cards_sim) < 5:
				shared_cards_sim.append(heap.pop())
			my_cards_sim = my_cards_sim + shared_cards_sim
			# my_hand = Hand(my_cards_sim)
			# other_player = []

			score = 0
			even = 0
			assert (len(alive_players) == len(other_player_cards_sim))
			for player in range(len(alive_players)):
				compare = judge_two(my_cards_sim, other_player_cards_sim[player] + shared_cards_sim)
				if compare == 0:
					even += 1
				score += compare
			if score == -len(alive_players):
				win_count += 1
			if even == alive_players:
				win_count += 0.5

		win_rate = win_count / iterate
		return win_rate

	guess_book = []

	guess_card_list_full = []
	if len(bold_better) != 0:
		for i in range(100):
			guess_card = []
			heap = remain_card[:]
			random.shuffle(heap)
			guess_card.append(heap.pop())
			guess_card.append(heap.pop())
			guess_card_win_rate = simulate_win_rate(inhand_cards = guess_card, iterate = 50)
			guess_card_list_full.append([guess_card, guess_card_win_rate])
		guess_card_list_full = sorted(guess_card_list_full, key=lambda x: x[1])

	print("--- %s seconds ---" % (time.time() - start_time))

	for player_id in range(len(bold_better)):
		cache_wealth = alive_players[player_id].money + alive_players[player_id].bet + alive_players[player_id].totalbet
		cache_invest_base = min(cache_wealth, 4000)
		cache_invest_base = max(cache_invest_base, 1000)
		confidence = (alive_players[player_id].bet / cache_invest_base) ** (1/2)
		if round == 0:
			confidence = min(confidence, 0.8)
		elif round == 1:
			confidence = min(confidence, 0.9)
		elif round == 2 :
			confidence = min(confidence, 0.95)
		elif round == 3:
			confidence = min(confidence, 0.98)
		guess_card_list_part = guess_card_list_full[int(confidence * len(guess_card_list_full)) :]
		guess_card_list = [i[0] for i in guess_card_list_part]
		guess_book.append(guess_card_list)


	my_win_rate = simulate_win_rate(inhand_cards = my_cards, other_player_cards = guess_book)
	print("--- %s seconds ---" % (time.time() - start_time))
	# print('estimated win rate: ', my_win_rate)
	decision = Decision()

	delta = state.minbet - state.player[state.currpos].bet
	me = state.player[id]
	wealth = me.money + me.totalbet + me.bet
	
	def add_bet(state, total):
		# amount: 本局需要下的总注
		amount = total - state.player[state.currpos].totalbet
		assert (amount > state.player[state.currpos].bet)
		if amount > me.money:
			decision.allin = 1
			return decision
		# Obey the rule of last_raised
		minamount = state.last_raised + state.minbet
		real_amount = max(amount, minamount)
		# money_needed = real_amount - state.player[state.currpos].bet
		decision.raisebet = 1
		decision.amount = int(real_amount)
		return decision
	
	if my_win_rate < 1 / (len(alive_players) + 1):
		target = 0
	elif my_win_rate > 0.75:
		base = max(state.player[state.currpos].money, 2000)
		base = min(base, 4000)
		target = my_win_rate ** risk_averse * base + 15
	else:
		base = 2000
		target = my_win_rate ** risk_averse * base + 15
		target = 0.6 * min(target, wealth * 0.6)
	
	if (wealth <= 300) & (my_win_rate > 0.6):
		decision.allin = 1
		return decision
	
	at_stake = state.player[id].totalbet + state.player[id].bet

	if (state.minbet + state.player[state.currpos].totalbet) >= target:
		if delta == 0:
			decision.callbet = 1
		else:
			er_giveup = - at_stake
			er_call = - (1 - my_win_rate) * (at_stake + delta) + my_win_rate * (state.moneypot)
			if er_giveup >= er_call:
				decision.giveup = 1
			else:
				decision.callbet = 1
	else:
		decision = add_bet(state, target)
	if log:
		log_text = 'estimated win rate, ' + str(my_win_rate) + ', ' + 'target, ' + str(target)
		print(log_text)
		state.logger.info(log_text)
	print("FINISH--- %s seconds ---" % (time.time() - start_time))
	return decision

def printcard(num):
    name = ['spade', 'heart', 'diamond', 'club']
    value = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    return '%s, %s' %(name[num%4], value[num//4])

if __name__ == '__main__':
	log = logger('/Users/Simon-CWG/Documents/quantresearch/Texaspoker/modules/texaspoker/AI/test')
	state = State(logger=log, totalPlayer=6, initMoney=2000, bigBlind=40, button=0)
	for i in range(100):
		cardset = list(range(0, 52))
		random.shuffle(cardset)
		state.player[0].cards = cardset[:2]
		print(printcard(cardset[0]))
		print(printcard(cardset[1]))
		ai(id = 0, state = state, log = True)
