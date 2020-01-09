import requests
import json
import time
import sched


class APIReader:
    def __init__(self, gui=None):
        worldstate_data_path = "..\\warframe-worldstate-data\\data\\"
        self.fissures = None
        with open('resources\\fissureModifiers.json') as fissures_file:
            self.fissures = json.load(fissures_file)

        self.sol_nodes = None
        with open('resources\\solNodes.json') as sol_nodes_file:
            self.sol_nodes = json.load(sol_nodes_file)

        self.mission_types = None
        with open('resources\\missionTypes.json') as mission_types_file:
            self.mission_types = json.load(mission_types_file)

        self.api_str = "http://content.warframe.com/dynamic/worldState.php"
        if gui is not None:
            self.gui = gui
        self.active_mission_details = set()
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.exit_now = False
        self.next_event = None
        self.rate = 30

    def set_rate(self, val):
        self.rate = val

    def run(self, blocking=True):
        self.update()
        self.scheduler.run(blocking=False)
        while blocking and not self.exit_now:
            time.sleep(1)

    def update(self):
        response = requests.get(self.api_str)
        json_response = response.json()
        active_missions = json_response['ActiveMissions']
        l = len(self.active_mission_details)
        need_update = False
        for active_mission in active_missions:
            sol_node = self.sol_nodes[active_mission['Node']]
            enemy = sol_node['enemy']
            name = sol_node['value']
            node_type = sol_node['type']
            expire = float(int(active_mission['Expiry']['$date']['$numberLong']))/1000
            modifier = self.fissures[active_mission['Modifier']]['value']
            details = (modifier, name, node_type, expire)
            self.active_mission_details.add(details)
            if l < len(self.active_mission_details):
                self.scheduler.enterabs(expire + 1, 1, self.filter_expired_missions)
                need_update = True
            if self.gui is None:
                print('{} {} {} {}'.format(modifier, name, node_type, expire))
        cur_time = time.time()
        if not self.exit_now:
            self.next_event = self.scheduler.enterabs(cur_time+self.rate, 1, self.update)
        if need_update:
            self.update_table()

    def cancel_event(self):
        self.exit_now = True
        self.scheduler.cancel(self.next_event)

    def filter_expired_missions(self):
        cur_time = time.time()
        if any(x[3] <= cur_time for x in self.active_mission_details):
            self.active_mission_details = {x for x in self.active_mission_details if x[3] > cur_time}
            self.update_table()

    def update_table(self):
        if self.gui is not None:
            mission_list = list(self.active_mission_details)
            sorted_mission_list = sorted(mission_list, key=lambda tup: tup[0])
            self.gui.update_mission_table(sorted_mission_list)


if __name__ == "__main__":
    api = APIReader()
    api.run()