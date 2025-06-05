def 테스터(mine, yours):
    n = len(mine)
    if n == 0:
        return 'D'
    elif n == 1:
        return 'C'
    elif n == 2:
        return 'C'
    else:
        if yours[1] == 'D':
            return yours[-1]
        else:
            if mine[-1] == 'C':
                return 'D'
            else:
                return 'C'
