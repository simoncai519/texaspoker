from time import sleep
import communicate.dealer_pb2 as dealer_pb2
import communicate.dealer_pb2_grpc as rpc

# V1.4
# 0 黑桃 1 红桃 2 方片 3 草花
# 牌的id: 0-51

'''
牌面level编号
    皇家同花顺：10
    同花顺    ：9
    四条      ：8
    葫芦      ：7
    同花      ：6
    顺子      ：5
    三条      ：4
    两对      ：3
    一对      ：2
    高牌      ：1
'''

'''
DealerRequest message Definition:
type:
    0   heartbeat
    1   response from server for state update
    2   request from server for decision
    3   request from server for state control
    4   response from server for client init
    5   response from server for game over
status:
    -1  uninitialized
'''
MessageType_HeartBeat       = 0
MessageType_StateUpdate     = 1
MessageType_GameDecision    = 2
MessageType_StateControl    = 3
MessageType_ClientInit      = 4
MessageType_GameOver        = 5
MessageType_InvalidToken    = 6
MessageType_GameStarted     = 7
MessageType_IllegalDecision     = 8

#ClientState_Uninitialized   = -1
#ClientState_Connected       = 1
#ClientState_Disconnected    = 2

## InitStatus when ClientInit
InitStatus_InGameRejected   = -2    # user already in game, and connected, and rejected
InitStatus_InQueueRejected  = -1    # user already in queue, and connected, and rejected
InitStatus_InQueue          = 0     # user added in queue
InitStatus_InGameContinue   = 1     # user already in game, and disconnected, and continue game
InitStatus_InQueueReInit    = 2     # user already in queue, and disconnected, and continue in queue

GameStatus_Reseted          = 0
GameStatus_Started          = 1
GameStatus_Running          = 2
GameStatus_Finished         = 3

SERVER_TIMEOUT_SECONDS      = 15


# alter the card id into color
def id2color(card):
    return card % 4

# alter the card id into number
def id2num(card):
    return card // 4

'''
hand.level
牌面等级：高牌 1	一对 2	两对 3	三条 4	顺子 5	同花 6	葫芦 7	四条 8	同花顺 9	皇家同花顺：10

'''
def judge_exist(x):
    if x >= 1:
        return True
    return False

# poker hand of 7 card
class Hand(object):
    def __init__(self, cards):
        cards = cards[:]
        self.level = 0
        self.cnt_num = [0] * 13
        self.cnt_color = [0] * 4
        self.cnt_num_eachcolor = [[0 for col in range(13)] for row in range(4)]
        self.maxnum = -1
        self.single = []
        self.pair = []
        self.tripple = []
        self.nums = []
        for x in cards:
            self.cnt_num[id2num(x)] += 1
            self.cnt_color[id2color(x)] += 1
            self.cnt_num_eachcolor[id2color(x)][id2num(x)] += 1
            self.nums.append(id2num(x))

        self.judge_num_eachcolor = [[] for i in range(4)]

        for i in range(4):
            self.judge_num_eachcolor[i] = list(map(judge_exist, self.cnt_num_eachcolor[i]))


        self.nums.sort(reverse=True)
        for i in range(12, -1, -1):
            if self.cnt_num[i] == 1:
                self.single.append(i)
            elif self.cnt_num[i] == 2:
                self.pair.append(i)
            elif self.cnt_num[i] == 3:
                self.tripple.append(i)
        self.single.sort(reverse=True)
        self.pair.sort(reverse=True)
        self.tripple.sort(reverse=True)

        # calculate the level of the poker hand
        for i in range(4):
            if self.judge_num_eachcolor[i][8:13].count(True) == 5:
                self.level = 10
                return


        for i in range(4):

            for j in range(7, -1, -1):
                if self.judge_num_eachcolor[i][j:j+5].count(True) == 5:
                    self.level = 9
                    self.maxnum = j + 4
                    return
            if self.judge_num_eachcolor[i][12] and self.judge_num_eachcolor[i][:4].count(True) == 4:
                    self.level = 9
                    self.maxnum = 3
                    return



        for i in range(12, -1, -1):
            if self.cnt_num[i] == 4:
                self.maxnum = i
                self.level = 8
                for j in range(4):
                    self.nums.remove(i)
                return


        tripple = self.cnt_num.count(3)
        if tripple > 1:
            self.level = 7
            return
        elif tripple > 0:
            if self.cnt_num.count(2) > 0:
                self.level = 7
                return

        for i in range(4):
            if self.cnt_color[i] >= 5:
                self.nums = []
                for card in cards:
                    if id2color(card) == i:
                        self.nums.append(id2num(card))
                self.nums.sort(reverse=True)
                self.nums = self.nums[:5]
                self.maxnum = self.nums[0]
                self.level = 6
                return

        for i in range(8, -1, -1):
            flag = 1
            for j in range(i, i + 5):
                if self.cnt_num[j] == 0:
                    flag = 0
                    break
            if flag == 1:
                self.maxnum = i + 4
                self.level = 5
                return
        if self.cnt_num[12] and list(map(judge_exist, self.cnt_num[:4])).count(True) == 4:
            self.maxnum = 3
            self.level = 5
            return


        for i in range(12, -1, -1):
            if self.cnt_num[i] == 3:
                self.maxnum = i
                self.level = 4
                self.nums.remove(i)
                self.nums.remove(i)
                self.nums.remove(i)
                self.nums = self.nums[:min(len(self.nums), 2)]
                return


        if self.cnt_num.count(2) > 1:
            self.level = 3
            return


        for i in range(12, -1, -1):
            if self.cnt_num[i] == 2:
                self.maxnum = i
                self.level = 2

                self.nums.remove(i)
                self.nums.remove(i)
                self.nums = self.nums[:min(len(self.nums), 3)]
                return


        if self.cnt_num.count(1) == 7:
            self.level = 1
            self.nums = self.nums[:min(len(self.nums), 5)]
            return

        self.level = -1

    def __str__(self):
        return 'level = %s' % self.level


def cmp(x,y):  # x < y return 1
    if x > y: return -1
    elif x == y: return 0
    else: return 1

# find the bigger of two poker hand(7 cards), if cards0 < cards1 then return 1, cards0 > cards1 return -1, else return 0
def judge_two(cards0, cards1):
    hand0 = Hand(cards0)
    hand1 = Hand(cards1)
    if hand0.level > hand1.level:
        return -1
    elif hand0.level < hand1.level:
        return 1
    else:
        if hand0.level in [5, 9]:
            return cmp(hand0.maxnum, hand1.maxnum)
        elif hand0.level in [1, 2, 4]:
            t = cmp(hand0.maxnum, hand1.maxnum)
            if t == 1: return 1
            elif t == -1: return -1
            else:
                if hand0.nums < hand1.nums:
                    return 1
                elif hand0.nums == hand1.nums:
                    return 0
                else:
                    return -1

        elif hand0.level == 6:
            if hand0.nums < hand1.nums:
                return 1
            elif hand0.nums > hand1.nums:
                return -1
            else:
                return 0

        elif hand0.level == 8:
            t = cmp(hand0.maxnum, hand1.maxnum)
            if t == 1:
                return 1
            elif t == -1:
                return -1
            else:
                return cmp(hand0.nums[0], hand1.nums[0])

        elif hand0.level == 3:
            if cmp(hand0.pair[0], hand1.pair[0]) != 0:
                return cmp(hand0.pair[0], hand1.pair[0])
            elif cmp(hand0.pair[1], hand1.pair[1]) != 0:
                return cmp(hand0.pair[1], hand1.pair[1])
            else:
                hand0.pair = hand0.pair[2:]
                hand1.pair = hand1.pair[2:]
                tmp0 = hand0.pair + hand0.pair + hand0.single
                tmp0.sort(reverse=True)
                tmp1 = hand1.pair + hand1.pair + hand1.single
                tmp1.sort(reverse=True)
                if tmp0[0] < tmp1[0]:
                    return 1
                elif tmp0[0] == tmp1[0]:
                    return 0
                else:
                    return -1

        elif hand0.level == 7:
            if cmp(hand0.tripple[0], hand1.tripple[0]) != 0:
                return cmp(hand0.tripple[0], hand1.tripple[0])
            else:
                tmp0 = hand0.pair
                tmp1 = hand1.pair
                if len(hand0.tripple) > 1:
                    tmp0.append(hand0.tripple[1])
                if len(hand1.tripple) > 1:
                    tmp1.append(hand1.tripple[1])
                tmp0.sort(reverse=True)
                tmp1.sort(reverse=True)
                if tmp0 < tmp1:
                    return 1
                elif tmp0 == tmp1:
                    return 0
                else:
                    return -1
        else:
            pass
            # assert 0
        return 0

class Player(object):

    def __init__(self, initMoney, state):
        self.active = True      # if the player is active(haven't giveups)
        self.money = initMoney  # money player has
        self.bet = 0            # the bet in this round
        self.cards = []         # private cards
        self.allin = 0          # if the player has all in
        self.totalbet = 0       # the bet in total(all round)
        self.state = state      # state

        ## user data
        self.username = ''

        ## session data
        self.token = ''
        self.connected = False
        self.last_msg_time = None
        self.game_over_sent = False

    # raise the bet by amount
    def raisebet(self, amount):
        self.money -= amount
        self.bet += amount
        assert self.money > 0

    # player allin
    def allinbet(self):
        self.bet += self.money
        self.allin = 1
        self.money = 0

    def getcards(self):
        return self.cards + self.state.sharedcards

    def __str__(self):
        return 'player: active = %s, money = %s, bet = %s, allin = %s' % (self.active, self.money, self.bet, self.allin)



class State(object):
    def __init__(self, logger, totalPlayer, initMoney, bigBlind, button):
        ''' class to hold the game '''
        self.totalPlayer = totalPlayer # total players in the game
        self.bigBlind = bigBlind       # bigBlind, every bet should be multiple of smallBlind which is half of bigBlind.
        self.button = button           # the button position
        self.currpos = 0               # current position
        self.playernum = totalPlayer   # active player number
        self.moneypot = 0              # money in the pot
        self.minbet = bigBlind         # minimum bet to call in this round, total bet
        self.sharedcards = []          # shared cards in the game
        self.turnNum = 0               # 0, 1, 2, 3 for pre-flop round, flop round, turn round and river round
        self.last_raised = bigBlind    # the amount of bet raise last time
        self.player = []               # All players. You can check them to help your decision. The 'cards' field of other player is not visiable for sure.
        for i in range(totalPlayer):
            self.player.append(Player(initMoney, self))

        self.logger = logger

    def set_user_money(self, initMoney):
        for i in range(self.totalPlayer):
            self.player[i].money = initMoney[i]
            print('user at pos {} has {}'.format(i, self.player[i].money), flush=True)

    def __str__(self):
        return 'state: currpos = %s, playernum = %s, moneypot = %s, minbet = %s, last_raised = %s' \
               % (self.currpos, self.playernum, self.moneypot, self.minbet, self.last_raised)

    def restore(self, turn, button, bigBlind):      # restore the state before each round
        self.turnNum = turn
        self.currpos = button
        self.minbet = 0
        self.last_raised = bigBlind

    def update(self, totalPlayer):                       # update the state after each round
        for i in range(totalPlayer):
            self.player[i].totalbet += self.player[i].bet
            self.player[i].bet = 0

    # judge if the round is over
    def round_over(self):
        if self.playernum == 1:
            return 1
        for i in range(self.totalPlayer):
            if (self.player[i].active is True) and (self.player[i].allin == 0):
                return 0
        for i in range(self.totalPlayer):
            if self.player[i].active is True and (self.player[i].bet != self.minbet and self.player[i].allin == 0):
                return 0
        if self.turnNum != 0 and self.minbet == 0:
            return 0
        return 1

    # calculate the next position
    def nextpos(self, pos):
        self.currpos = (pos + 1) % self.totalPlayer
        return self.currpos


class Decision(object):
    giveup = 0   # 弃牌
    allin = 0    # 全押
    check = 0    # 过牌
    callbet = 0  # 跟注
    raisebet = 0 # 加注
    amount = 0   # 本轮中加注到amount

    def clear(self):
        self.giveup = self.allin = self.check = self.callbet = self.raisebet = self.amount = 0

    def update(self, a):
        self.giveup = a[0]
        self.allin = a[1]
        self.check = a[2]
        self.callbet = a[3]
        self.raisebet = a[4]
        self.amount = a[5]

    def isValid(self):
        if self.giveup + self.allin + self.check + self.callbet + self.raisebet == 1:
            if self.raisebet == 1 and self.amount == 0:
                return False
            return True
        return False

    def fix(self):
        amount = self.amount
        setname = ''
        for k, v in self.__dict__.items():
            if v == 1 and k != 'amount':
                setname = k
            setattr(self, k, 0)
        if setname == '':
            setattr(self, 'giveup', 1)
        else:
            setattr(self, setname, 1)
            if setname == 'raisebet':
                if amount != 0:
                    setattr(self, 'amount', amount)
                else:
                    setattr(self, 'callbet', 1)
                    setattr(self, 'raisebet', 0)


    def __str__(self):
        return 'giveup=%s, allin=%s, check=%s, callbet=%s, raisebet=%s, amount=%s' % (self.giveup,self.allin,self.check,
                                                                            self.callbet, self.raisebet, self.amount)
