### Feqtures:
# DONE:
#   1. also simulate other players' card
#   2. take their current betting into account, if bold bet, then boost their card or level
#       boost by taking upper subset of simulation result
#   3. consider give up cost
#   4. set different reaction when win rate is above or below certain threshold
#   5. increasing opponents confidence upper bound as round goes on

# TO DO:
#   consider the variance of simulation output
#   apply kelly criterion
#   gradually raise bet, so that other players are more likely to call
#   bluffing based on shared cards
#   create first round cards-scoring data, save computation at round 0, but need to consider my hand...

from modules.texaspoker.lib.client_lib import State
from modules.texaspoker.lib.client_lib import Player
from modules.texaspoker.lib.client_lib import Hand
from modules.texaspoker.lib.client_lib import Decision
from modules.texaspoker.lib.client_lib import judge_two
import random
from modules.texaspoker.lib.simple_logger import file_logger as logger
import time


class bold_better():
	def __init__(self, player, total_bet, wealth):
		self.player: Player = player
		self.total_bet: float = total_bet
		self.wealth = wealth
		self.card_guess = None

class guess_cards():
	def __init__(self, cards, win_rate):
		self.cards: list = cards
		self.win_rate: float = win_rate

class ai():
	def __init__(self, risk_averse=2, log=True, record_time=True):
		self.risk_averse: float = risk_averse
		self.log: bool = log
		self.record_time: bool = record_time
		self.invest_base_lower = 2000
		self.invest_base_upper = 4000
		self.bold_better_invest_base_upper = 4000
		self.bold_better_invest_base_lower = 1000
		self.bold_better_risk_averse = 2
		self.confidence_upper_bound = {0: 0.8,
		                               1: 0.9,
		                               2: 0.95,
		                               3: 0.98}
		self.win_rate_sim_iterate = 1000
		self.guess_card_win_rate_sim_iterate = 50
		# self.target_function

	def make_decision(self, state):

		# record run time for making one decision
		if self.record_time:
			start_time = time.time()

		shared_cards = state.sharedcards.copy()
		my_id = state.currpos

		# see which round we are at, based on length of shared cards
		if len(shared_cards) == 0:
			round = 0
		elif len(shared_cards) == 3:
			round = 1
		elif len(shared_cards) == 4:
			round = 2
		else:
			round = 3

		my_cards = state.player[my_id].cards
		remain_card = list(range(0, 52))
		for x in shared_cards:
			remain_card.pop(remain_card.index(x))
		for x in my_cards:
			remain_card.pop(remain_card.index(x))

		# check how many players are still alive
		# check how many players are making bold bet (larger than big blind)
		alive_players_num = 0
		bold_better_list = []
		for player_id in range(len(state.player)):
			if state.player[player_id].active & (player_id != my_id):
				player = state.player[player_id]
				alive_players_num += 1

				total_bet = player.totalbet + player.bet
				if total_bet > 40:
					wealth = player.money + total_bet
					bold_better_list.append(bold_better(player=player, total_bet=total_bet, wealth = wealth))

		def simulate_win_rate(in_hand_cards, bold_better_list = [], iterate=self.win_rate_sim_iterate):
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

		# simulate possible in-hand cards set for bold better, calculate win rate
		if len(bold_better_list) != 0:
			guess_card_list_full = []
			for i in range(100):
				_guess_cards = []
				_remain_card = remain_card.copy()
				random.shuffle(_remain_card)
				_guess_cards.append(_remain_card.pop())
				_guess_cards.append(_remain_card.pop())
				guess_cards_win_rate = \
					simulate_win_rate(in_hand_cards=_guess_cards, iterate=self.guess_card_win_rate_sim_iterate)
				guess_card_list_full.append(guess_cards(cards=_guess_cards, win_rate=guess_cards_win_rate))
			guess_card_list_full = sorted(guess_card_list_full, key=lambda x: x.win_rate)

		if self.record_time:
			print("simulate guess cards finish --- %s seconds ---" % (time.time() - start_time))

		# assess bold better's confidence based on their betting, bayesian style
		for _bold_better in bold_better_list:
			_invest_base = min(_bold_better.wealth, self.bold_better_invest_base_upper)
			_invest_base = max(_invest_base, self.bold_better_invest_base_lower)
			confidence = (_bold_better.total_bet / _invest_base) ** (1 / self.bold_better_risk_averse)
			# set confidence upper bound for different round
			confidence = min(confidence, self.confidence_upper_bound[round])
			# take upper subset of guess cards based on confidence
			guess_card_list_part = guess_card_list_full[int(confidence * len(guess_card_list_full)):]
			guess_card_list = [i.cards for i in guess_card_list_part]
			_bold_better.card_guess = guess_card_list

		# finally, simulate my win rate given bold betters' cards guessed
		my_win_rate = simulate_win_rate(in_hand_cards=my_cards, bold_better_list = bold_better_list)

		if self.record_time:
			print("simulate guess book finish --- %s seconds ---" % (time.time() - start_time))
		# print('estimated win rate: ', my_win_rate)

		# make decision
		decision = Decision()

		delta = state.minbet - state.player[state.currpos].bet
		me = state.player[my_id]
		wealth = me.money + me.totalbet + me.bet

		def add_bet(state, total):
			# amount: 本局需要下的总注
			amount = total - state.player[state.currpos].totalbet
			assert (amount > state.player[state.currpos].bet)
			if amount > me.money:
				decision.allin = 1
				return decision
			# Obey the rule of last_raised
			min_amount = state.last_raised + state.minbet
			real_amount = max(amount, min_amount)
			# money_needed = real_amount - state.player[state.currpos].bet
			decision.raisebet = 1
			decision.amount = int(real_amount)
			return decision

		# set target total bet
		# if win rate smaller than average win rate ( 1 / number of players), fold
		if my_win_rate < 1 / (alive_players_num + 1):
			target = 0
		# if high win rate, bet based on current wealth
		elif my_win_rate > 0.75:
			base = max(state.player[state.currpos].money, self.invest_base_lower)
			base = min(base, self.invest_base_upper)
			target = my_win_rate ** self.risk_averse * base + 15
		# if modest win rate, bet based on $2000
		else:
			base = 2000
			target = my_win_rate ** self.risk_averse * base + 15
			target = min(target, wealth * 0.6)

		# if nearly broke and good win rate, all in
		if (wealth <= 300) & (my_win_rate > 0.6):
			decision.allin = 1
			return decision

		at_stake = me.totalbet + me.bet

		# make action based on target
		# if target less than minimum bet
		if (state.minbet + state.player[state.currpos].totalbet) >= target:
			# call if free to
			if delta == 0:
				decision.callbet = 1
			# compare expected loss of fold and expected loss of call, choose smaller loss
			else:
				er_giveup = - at_stake
				er_call = - (1 - my_win_rate) * (at_stake + delta) + my_win_rate * (state.moneypot)
				if er_giveup >= er_call:
					decision.giveup = 1
				else:
					decision.callbet = 1

		# if target grater than minimum bet, raise bet
		else:
			decision = add_bet(state, target)
		if self.log:
			log_text = 'estimated win rate, ' + str(my_win_rate) + ', ' + 'target, ' + str(target)
			print(log_text)
			state.logger.info(log_text)
		if self.record_time:
			print("FINISH--- %s seconds ---" % (time.time() - start_time))

		return decision


def print_card(num):
	name = ['spade', 'heart', 'diamond', 'club']
	value = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
	return '%s, %s' % (name[num % 4], value[num // 4])


if __name__ == '__main__':
	log = logger('/Users/Simon-CWG/Documents/quantresearch/Texaspoker/modules/texaspoker/AI/test')
	state = State(logger=log, totalPlayer=6, initMoney=2000, bigBlind=40, button=0)
	for i in range(100):
		cardset = list(range(0, 52))
		random.shuffle(cardset)
		state.player[0].cards = cardset[:2]
		state.currpos = 0
		state.player[1].totalbet = 80
		state.player[2].totalbet = 320
		print(print_card(cardset[0]))
		print(print_card(cardset[1]))
		simon_ai = ai()
		simon_ai.make_decision(state=state)
