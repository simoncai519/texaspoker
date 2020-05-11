'''
    AI: v1_1版本
    详见AI-v1.1_interpretation.txt
'''
from modules.texaspoker.lib.client_lib import State
from modules.texaspoker.lib.client_lib import Player
from modules.texaspoker.lib.client_lib import Hand
from modules.texaspoker.lib.client_lib import Decision
import random

def ai(id, state):
    weight = [0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
    remain_card = list(range(0, 52))
    cards = state.sharedcards + state.player[id].cards
    num = len(cards)
    for x in cards:
        remain_card.pop(remain_card.index(x))
    cnt = [0 for col in range(11)]
    # 模拟发牌1000次
    for i in range(1000):
        heap = remain_card[:]
        mycards = cards[:]
        random.shuffle(heap)
        while len(mycards) != 7:
            mycards.append(heap.pop())
        hand = Hand(mycards)
        level = hand.level
        cnt[level] += weight[level]

    # sum为评估值
    sum = 0
    for x in cnt:
        sum += x / 1000

    decision = Decision()
    totalbet = 0
    delta = state.minbet - state.player[state.currpos].bet
    if delta >= state.player[state.currpos].money:
        totalbet = 1000
    else:
        totalbet = state.player[state.currpos].totalbet + state.minbet

    if num == 2:
        # 两张牌
        if cards[0] != cards[1]:
            # 非对子
            if max(cards) <= 8 and 0 not in cards:
                # 最大不超过9：若跟注后超过100，放弃。否则跟注
                if totalbet <= 100:
                    decision.callbet = 1
                else:
                    decision.giveup = 1
            if max(cards) <= 11 and 0 not in cards:
                # 最大为10-Q：若跟注后超过150，放弃。否则跟注
                if totalbet <= 150:
                    decision.callbet = 1
                else:
                    decision.giveup = 1
            else:
                # 最大为K-A： 若跟注后超过200，放弃。否则跟注
                if totalbet <= 200:
                    decision.callbet = 1
                else:
                    decision.giveup = 1
        else:
            # 对子
            if max(cards) <= 11 and 0 not in cards:
                # 对子，不超过Q：跟注。若跟注后低于200，加注到200以上
                if totalbet < 200:
                    decision = add_bet(state, 200)
                else:
                    decision.callbet = 1
            else:
                # 双A、双K：跟注。若跟注后低于300，加注到300
                if totalbet < 300:
                    decision = add_bet(state, 300)
                else:
                    decision.callbet = 1

    elif num == 5:
        # 五张牌
        if sum < 4:
            # 直接放弃
            decision.giveup = 1
        elif sum >= 4 and sum < 10:
            # 若跟注后超过150，放弃。否则跟注
            # 若已下的注额大于200, 且本次需跟注额不大于50， 则跟注
            if totalbet < 150:
                    decision.callbet = 1
            elif state.player[state.currpos].totalbet + state.player[state.currpos].bet > 200 and delta < 50:
                decision.callbet = 1
            else:
                decision.giveup = 1
        elif sum >= 10 and sum < 20:
            # 跟注。若跟注后低于300，加注到300
            if totalbet < 300:
                decision = add_bet(state, 300)
            else:
                decision.callbet = 1
        elif sum >= 20 and sum < 50:
            # 跟注。若跟注后低于600，加注到600
            if totalbet < 600:
                decision = add_bet(state, 600)
            else:
                decision.callbet = 1
        else:
            # allin
            decision.allin = 1

    elif num == 6:
        # 六张牌
        if sum < 2:
            # 直接放弃
            decision.giveup = 1
        elif sum >= 2 and sum < 8:
            # 若跟注后超过300，放弃。否则跟注
            # 若已下的注额大于200, 且本次需跟注额不大于50， 则跟注
            if totalbet < 300:
                    decision.callbet = 1
            elif state.player[state.currpos].totalbet + state.player[state.currpos].bet > 200 and delta < 50:
                decision.callbet = 1
            else:
                decision.giveup = 1
        elif sum >= 8 and sum < 20:
            # 跟注。若跟注后低于300，加注到300
            if totalbet < 300:
                decision = add_bet(state, 300)
            else:
                decision.callbet = 1
        elif sum >= 20 and sum < 40:
            # 跟注。若跟注后低于600，加注到600
            if totalbet < 600:
                decision = add_bet(state, 600)
            else:
                decision.callbet = 1
        else:
            # allin
            decision.allin = 1

    elif num == 7:
        # 七张牌
        if level == 7:
            # allin
            decision.allin = 1
        elif level == 6:
            # 跟注，若跟注后低于600，加注到600
            if totalbet < 600:
                decision = add_bet(state, 600)
            else:
                decision.callbet = 1
        elif level == 5:
            # 跟注，若跟注后低于500，加注到500
            if totalbet < 500:
                decision = add_bet(state, 500)
            else:
                decision.callbet = 1
        elif level == 4:
            # 跟注，若跟注后低于400，加注到400
            if totalbet < 400:
                decision = add_bet(state, 400)
            else:
                decision.callbet = 1

        elif level == 3:
            # 若跟注后超过500，放弃。否则跟注。若跟注后低于300，加注到300
            # 若已下的注额大于200, 且本次需跟注额不大于50， 则跟注
            if totalbet < 300:
                decision = add_bet(state, 300)
            elif totalbet < 500:
                decision.callbet = 1
            elif state.player[state.currpos].totalbet + state.player[state.currpos].bet > 200 and delta < 50:
                decision.callbet = 1
            else:
                decision.giveup = 1
        elif level == 2:
            if cards.count(0) == 2 or cards.count(12) == 2:
                # 双A双K 若跟注后超过200，放弃。否则跟注
                # 若已下的注额大于200, 且本次需跟注额不大于50， 则跟注
                if totalbet < 200:
                    decision.callbet = 1
                elif state.player[state.currpos].totalbet + state.player[state.currpos].bet > 200 and delta < 50:
                    decision.callbet = 1
                else:
                    decision.giveup = 1
            else:
                # 不超过双Q 若跟注后超过200，放弃。否则跟注
                if totalbet > 200:
                    decision.giveup = 1
                else:
                    decision.callbet = 1
        elif level == 1:
            decision.giveup = 1
        else:
            print('the num of cards is {}'.format(num))
            assert(0)
    if decision.callbet == 1 and delta == state.player[state.currpos].money:
        decision.callbet = 0
        decision.allin = 1
    if decision.callbet == 1 and state.minbet == 0:
        t = random.randint(0,2)
        if t == 0:
            decision.callbet = 0
            decision.raisebet = 1
            decision.amount = state.bigBlind
    return decision
# add_bet: 将本局总注额加到total

def add_bet(state, total):
    # amount: 本局需要下的总注
    amount = total - state.player[state.currpos].totalbet
    assert(amount > state.player[state.currpos].bet)
    # Obey the rule of last_raised
    minamount = state.last_raised + state.minbet
    real_amount = max(amount, minamount)
    # money_needed = real_amount - state.player[state.currpos].bet
    decision = Decision()
    decision.raisebet = 1
    decision.amount = real_amount
    return decision
