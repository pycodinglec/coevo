def 프리드먼(mine, yours):
    n = len(mine)
    if n == 0:
        return 'C'
    else:
        if mine[-1] == 'D':
            return 'D'
        else:
            if yours[-1] == 'C':
                return 'C'
            else:
                return 'D'
