def 팃포투탯(mine, yours):
    n = len(mine)
    if n == 0 or n == 1:
        return 'C'
    else:
        if yours[-1] == 'D' and yours[-2] == 'D':
            return 'D'
        else:
            return 'C'
