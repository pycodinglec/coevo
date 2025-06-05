import os
from random import randint

def payoff(x, y):
    """payoff matrix presents score of each cases"""
    cooperate = ['c', 'C']
    defect = ['d', 'D']
    if x in cooperate and y in cooperate:
        return (3, 3)
    elif x in cooperate and y in defect:
        return (0, 5)
    elif x in defect and y in cooperate:
        return (5, 0)
    elif x in defect and y in defect:
        return (1, 1)
    else:
        print('error occured when using payoff function. check the variables below.')
        print(f'x:{x}, y:{y}')
        raise Exception

def get_strategies(directory):
    """gets strategy files in directory 'strategies/'"""
    def check_code_of_a_strategy(strategy_code):
        """checks the lines of strategy_code and returns function name if there's no problem"""
        def_count = strategy_code.count('def ')
        if def_count != 1:
            print(f"make the number of 'def' from {def_count} to 1")
            raise Exception
        elif ';' in strategy_code:
            print('using semicolon(;) is forbidden.')
            print('delete all the semicolon(s) in your strategy code file.')
            raise Exception
        else:
            # then there's no problem. so,
            pass
        code_lines = strategy_code.split('\n')
        for line in code_lines:
            if line == '':
                continue
            # extracting function name from strategy file
            if line.startswith('def ') and '(' in line and ')' in line and ':' in line:
                strategy_name = line.split('(')[0].split()[-1]
            elif line.startswith('\n') or line.startswith('\t') or line.startswith(' ') or line.startswith('#') or line.startswith("'") or line.startswith('"'):
                continue
            elif line.startswith('from') or line.startswith('import'):
                if ' os' in line:
                    print('Using os module is forbidden.')
                    raise Exception
                else:
                    continue
            else:
                print(f'check the line below:\n{line}')
                print('[principles]')
                print('you may not use use globals in strategy file.')
                print("""line should startswith...   (#, ', ", from, import, def)""")                
                raise Exception
        return strategy_name

    strategyfiles = os.listdir(directory)
    if '__pycache__' in strategyfiles:
        strategyfiles.remove('__pycache__')

    # this dict is for gathering the name of each function in strategy files
    # key: file name
    # value: function name in the file name
    strategies = {}

    for strategyfile in strategyfiles:
        with open(directory+'/'+strategyfile, 'r', encoding="utf-8") as f:
            print(f"checking file'{strategyfile}'    ...    ", end = '')
            strategy_code = f.read()
            strategy_name = check_code_of_a_strategy(strategy_code)
            if strategy_name in strategies:
                print(f"strategy name {strategy_name} is already exists")
                raise Exception
            strategies[strategyfile.rstrip('.py')] = strategy_name
            print(f"strategy '{strategy_name}' was found.")
    return strategies

def play_full_league(directory, strategies):
    # 1 match consists of n rounds games
    n = randint(200, 400)
    total_records = {}
    print("playing full leagues...")

    # importing 
    modules = list(strategies.keys())
    for module in modules:
        exec(f'from {directory}.{module} import {strategies[module]}')

    # make pairs before league
    pairs_of_strategies = []
    for i in range(len(modules)):
        for j in range(i, len(modules)):
            pairs_of_strategies.append((strategies[modules[i]], strategies[modules[j]]))

    # league start
    for pair_of_strategies in pairs_of_strategies:
        available_decisions = ['c', 'd', 'C', 'D']
        left = pair_of_strategies[0]
        right = pair_of_strategies[1]
        left_decisions = []
        right_decisions = []
        for i in range(n):
            left_decision = eval(f'{left}({left_decisions}, {right_decisions})')
            right_decision = eval(f'{right}({right_decisions}, {left_decisions})')
            if left_decision in available_decisions and right_decision in available_decisions:
                left_decisions.append(left_decision)
                right_decisions .append(right_decision)
            else:
                print('all the decisions should be cooperate(C) or defect(D), but something else was returned.')
                raise Exception
        total_records[pair_of_strategies] = (left_decisions, right_decisions)
    return total_records

def make_report(strategies, total_records):
    """after deriving scores from records, generates report"""
    strategies_list = list(strategies.values())

    # initializing
    total_scores = {}
    obtained_scores = {}
    given_scores = {}
    for left in strategies_list:
        obtained_scores[left] = 0
        given_scores[left] = 0
        for right in strategies_list:
            total_scores[(left, right)] = 0
    
    # derives total_scores from total_records
    for pairs_of_strategies in list(total_records.keys()):
        for i in range(len(total_records[pairs_of_strategies][0])):
            left_score, right_score = payoff(total_records[pairs_of_strategies][0][i], total_records[pairs_of_strategies][1][i])
            # in case of mirror-match, average score will be used(so, 0.5 score exists)
            if pairs_of_strategies[0] == pairs_of_strategies[1]:
                total_scores[(pairs_of_strategies[0], pairs_of_strategies[1])] += (left_score+right_score)/2
            else:
                total_scores[(pairs_of_strategies[0], pairs_of_strategies[1])] += left_score
                total_scores[(pairs_of_strategies[1], pairs_of_strategies[0])] += right_score
                
    # derives obtained and given scores from total scores
    for left in strategies_list:
        for right in strategies_list:
            obtained_scores[left] += total_scores[(left, right)]
            given_scores[right] += total_scores[(left, right)]

    # generates report
    from time import time
    now = int(time())
    x = len(strategies)
    report_file = f'report_file_{now}.csv'
    f = open(report_file, 'w')
    strategy_files = list(strategies.keys())
    
    f.write('file,strategy\n')
    for i in range(len(strategy_files)):            
        f.write(f'{strategy_files[i]},{strategies[strategy_files[i]]}\n')
    f.write('\n')
    total_match = int(x*(x+1)/2)
    rounds_of_each_match = len(list(total_records.values())[0][0])
    f.write(f'matches (A),{total_match}\n')
    f.write(f'rounds (B),{rounds_of_each_match}\n')
    f.write(f'total games (A*B),{total_match*rounds_of_each_match}\n\n')
    
    f.write('score table')
    for strategy_j in strategies_list:
        f.write(f',{strategy_j}')
    f.write(',sum,ranking\n')
    for strategy_i in strategies_list:
        f.write(f'{strategy_i}')
        for strategy_j in strategies_list:
            f.write(f',{total_scores[(strategy_i, strategy_j)]}')    
        f.write(f',{obtained_scores[strategy_i]},{sorted(obtained_scores.values(), reverse = True).index(obtained_scores[strategy_i])+1}\n')
    f.write('sum')
    for strategy_j in strategies_list:
        f.write(f',{given_scores[strategy_j]}')
    f.write('\n')
    f.write('ranking')
    for strategy_j in strategies_list:
        f.write(f',{sorted(given_scores.values(), reverse = True).index(given_scores[strategy_j])+1}')
    f.write('\n\n')
    
    f.write('ranking,strategy,obtained\n')
    obtained_scores = sorted(obtained_scores.items(), key = lambda x:x[1], reverse = True)
    for i in range(len(obtained_scores)):
        f.write(f'{i+1},{obtained_scores[i][0]},{obtained_scores[i][1]}\n')
    f.write('\n')
    
    f.write('ranking,strategy,given\n')
    given_scores = sorted(given_scores.items(), key = lambda x:x[1], reverse = True)
    for i in range(len(given_scores)):
        f.write(f'{i+1},{given_scores[i][0]},{given_scores[i][1]}\n')
    f.close()
    return report_file

if __name__ == '__main__':
    # directory where strategy files are located.
    directory = 'strategies'

    # strategies is dictionary type
    # keys are filenames without '.py' and values are function names
    strategies = get_strategies(directory)

    # total_records is dictionary type
    # keys are pairs of strategies which had actual match in league
    # after game league, a bunch of lists consist of 'C'(Cooperate) and 'D'(Defect) are returned as values of a dictionary
    total_records = play_full_league(directory, strategies)

    # csv report file can be derived from strategies information and game records
    report_file = make_report(strategies, total_records)

    # message below presents success of whole process
    print(f'{report_file} was successfully generated')
