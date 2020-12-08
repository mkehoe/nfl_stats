import csv
import random

from modules.search import GeneticAlgorithmSearch


class DraftKingsPlayer:
    def __init__(self, name: str, salary: int, projected_points: float, team: str, position: str, injured: bool):
        self.name = name
        self.salary = salary
        self.projected_points = projected_points
        self.team = team
        self.position = position
        self.injured = injured

    def __repr__(self):
        return '{} ({})'.format(self.name, self.position)


class Lineup:
    def __init__(self, qb: DraftKingsPlayer, rb_list: [DraftKingsPlayer], wr_list: [DraftKingsPlayer], te: DraftKingsPlayer, flex: DraftKingsPlayer, dst: DraftKingsPlayer):
        self.qb = qb
        self.rb_list = rb_list
        self.wr_list = wr_list
        self.te = te
        self.flex = flex
        self.dst = dst
        self.points = 0
        self.salary = 0
    
    def mixin(self, o): 
        # For cross we don't half fold but we will randomly pick pos from each
        qb = self.qb
        rb_list = self.rb_list
        wr_list = self.wr_list
        te = self.te
        flex = self.flex
        dst = self.dst
        randseq = [random.randrange(2) for i in range(9)]
        if 0 == randseq[0]:
            qb = o.qb
        for i in range(len(rb_list)):
            if 0 == randseq[1+i]:
                rb_list[i] = o.rb_list[i]
        for i in range(len(wr_list)):
            if 0 == randseq[3+i]:
                wr_list[i] = o.wr_list[i]
        if 0 == randseq[6]:
            te = o.te
        if 0 == randseq[7]:
            flex = o.flex
        if 0 == randseq[8]:
            dst = o.dst
                
        return Lineup(qb,rb_list,wr_list,te,flex,dst)

    def count(self, player: DraftKingsPlayer):
        c = 0
        if player == self.qb:
            c += 1
        if player == self.te:
            c += 1
        if player == self.flex:
            c += 1
        if player == self.dst:
            c += 1
        return c + self.rb_list.count(player) + self.wr_list.count(player)

    def index(self, player: DraftKingsPlayer):
        if player == self.qb:
            return self.qb
        if player == self.te:
            return self.te
        if player == self.flex:
            return self.flex
        if player == self.dst:
            return self.dst
        if self.rb_list.count(player) > 0:
            return self.rb_list.index(player)
        if self.wr_list.count(player) > 0:
            return self.wr_list.index(player)
        return None

    def __len__(self):
        return len(self.wr_list) + len(self.rb_list) + 4

    def __getitem__(self, item):
        if item == 0:
            return self.qb
        elif item == 6:
            return self.te
        elif item == 7:
            return self.flex
        elif item == 8:
            return self.dst
        elif item >= 1 and item <= 2:
            return self.rb_list[item-1]
        elif item >= 3 and item <=5:
            return self.wr_list[item-3]
        return None

    def __setitem__(self, key, value):
        if key == 0:
            self.qb = value
        elif key == 6:
            self.te = value
        elif key == 7:
            self.flex = value
        elif key == 8:
            self.dst = value
        elif key >= 1 and key <= 2:
            self.rb_list[key-1] = value
        elif key >= 3 and key <=5:
            self.wr_list[key-3] = value
        return None
    
    def projected_points(self):
        if self.points > 0:
            return self.points
        c = 0
        for i in range(len(self)):
            c += self[i].projected_points
        self.points = c
        return c

    def total_salary(self):
        if self.salary > 0:
            return self.salary
        c = 0
        for i in range(len(self)):
            c += self[i].salary
        self.salary = c
        return c
    
    def get_duplicates(self):
        dups = []
        
        for i in range(len(self.rb_list)):
            if self.rb_list[i] == self.flex:
                dups.append(i+1)
            for j in range(i+1,len(self.rb_list)):
                if self.rb_list[i] == self.rb_list[j]:
                    dups.append(j+1)
                    break

        for i in range(len(self.wr_list)):
            if self.wr_list[i] == self.flex:
                dups.append(i+3)
            for j in range(i+1,len(self.wr_list)):
                if self.wr_list[i] == self.wr_list[j]:
                    dups.append(j+3)
                    break
        return dups

        
        

def _read_draftkings_data(filename: str) -> [DraftKingsPlayer]:
    """
    Reads the csv file from DraftKings and returns a dictionary that
    :param filename: CSV file downloaded from DraftKings
    :return: List of DraftKingsPlayers and their information.
    """
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        players = []
        for row in reader:
            if (row['Roster Position'] == 'DST' and int(row['Salary']) > 3000) or \
               (row['Roster Position'] == 'QB' and int(row['Salary']) > 5400) or \
               (row['Roster Position'] == 'WR/FLEX' and int(row['Salary']) > 4500) or \
               (row['Roster Position'] == 'RB/FLEX' and int(row['Salary']) > 4500) or \
               (row['Roster Position'] == 'TE/FLEX' and int(row['Salary']) > 4000):
                player = DraftKingsPlayer(
                    name=row['Name'],
                    salary=int(row['Salary']),
                    projected_points=float(row['AvgPointsPerGame']),
                    team=row['TeamAbbrev'],
                    position=row['Roster Position'],
                    injured=False
                    #row['Injury Indicator'] in ['', 'P']  # Players with no injury or who are probable are "healthy"
                )
                players.append(player)
        
        return players


class DraftKingsFootballGA(GeneticAlgorithmSearch):

    def __init__(self, filename: str, salary_cap=50000, num_generations=100, population_size=20):
        GeneticAlgorithmSearch.__init__(self, num_generations=num_generations)
        self._population_size = population_size
        self._salary_cap = salary_cap
        self._all_players = _read_draftkings_data(filename)
        self._qb_list = [x for x in self._all_players if x.position == 'QB']
        self._rb_list = [x for x in self._all_players if x.position == 'RB/FLEX']
        self._wr_list = [x for x in self._all_players if x.position == 'WR/FLEX']
        self._te_list = [x for x in self._all_players if x.position == 'TE/FLEX']
        self._d_list = [x for x in self._all_players if x.position == 'DST']
        self.position_to_player_list_map = {
            'QB': self._qb_list,
            'RB/FLEX': self._rb_list,
            'WR/FLEX': self._wr_list,
            'TE/FLEX': self._te_list,
            'DST': self._d_list,
        }

    def _generate_initial_population(self) -> [Lineup]:
        population = []
        for _ in range(self._population_size):
            qb = random.choice(self._qb_list)
            rb_list = random.sample(self._rb_list, 2)
            wr_list = random.sample(self._wr_list, 3)
            te = random.choice(self._te_list)
            flex = random.choice(self._wr_list + self._rb_list)
            dst = random.choice(self._d_list)
            population.append(Lineup(qb,rb_list,wr_list,te,flex,dst))
        return population

    def _evaluate_chromosome(self, lineup: Lineup) -> float:
        return lineup.projected_points()
    
    def _evaluate_chromosome2(self, lineup: Lineup) -> int:
        return lineup.total_salary()

    @staticmethod
    def __find_player_to_replace(lineup: Lineup, position: str) -> DraftKingsPlayer:
        players_of_position = {player for player in lineup if player.position == position}
        for player in players_of_position:
            if lineup.count(player) > 1:
                return player
        raise ValueError("Unable to find duplicate players in lineup!")

    def _handle_crossover_between(self, chromosome1: Lineup, chromosome2: Lineup) -> Lineup:
        new_lineup = chromosome1.mixin(chromosome2)

        dups = new_lineup.get_duplicates()
        self.__replace_duplicate_player_in_lineup(new_lineup, dups)

        return new_lineup

    def __replace_duplicate_player_in_lineup(self, new_lineup: Lineup, dups: list):
        for p in dups:
            player = new_lineup[p]
            replacement_player = self.__randomly_choose_player_not_in(new_lineup, player.position)    
            new_lineup[p] = replacement_player

    def _handle_mutation_in(self, lineup: Lineup) -> Lineup:
        for index in range(len(lineup)):
            player = lineup[index]
            if random.randint(0, 100) < self.mutation_rate:
                # picking new random player of same position not already in lineup
                lineup[index] = self.__randomly_choose_player_not_in(lineup, player.position)
        return lineup

    def __randomly_choose_player_not_in(self, lineup: Lineup, position: str):
        p = random.choice(self.position_to_player_list_map[position])
        while lineup.count(p) != 0:
            p = random.choice(self.position_to_player_list_map[position])
        return p
        
    def _should_exclude(self, lineup: Lineup) -> bool:
        """
        Ensures that the lineups are accurate, that there are no duplicate players, and that the salary cap is met.
        :param lineup:
        :return:
        """
        if(len(lineup) != 9):
            print("Invalid lineup")
            return True
        if lineup.total_salary() > self._salary_cap:
            return True
        
        #print(str(lineup.total_salary()) + ' ' + str(lineup.projected_points()) + ' ' + str(self._salary_cap))
        
if __name__ == '__main__':
    ga = DraftKingsFootballGA('DKSalaries (5).csv')
    ga.run_search()
    best_lineup = ga.get_result()
    print('Best Lineup ${}'.format(best_lineup.total_salary()))
    for i in range(len(best_lineup)):
        print(best_lineup[i])
