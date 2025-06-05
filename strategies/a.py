def 팃포탯(mine, yours):
    if len(yours) == 0:
        return 'C' # 첫 게임은 무조건 협력
    if yours[-1] == 'C':
        return 'C'
    else:   # 불필요하지만 논리 구조가 잘 보이도록 해주는 else
        return 'D'
