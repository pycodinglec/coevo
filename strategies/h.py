from random import random
def 요스(mine, yours):
    if len(yours) == 0:
        return 'C' # 첫 게임은 무조건 협력
    if yours[-1] == 'C':
        if random() < 0.1:
            return 'D'
        else:
            return 'C'
    else:
        return 'D'

