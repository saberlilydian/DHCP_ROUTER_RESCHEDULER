from keystoneauth1 import identity
from keystoneauth1 import session
from neutronclient.v2_0 import client
import os


_CREDENTIALS = {}
OS_PREFIX = "OS_"
OS_REQUIRED_KEYS = [
    'auth_url',
    'username',
    'password',
    'project_name',
    'project_domain_id'
]

# Example value for credentials
# auth_url='http://192.168.0.10/identity/v3'
# username='admin'
# password='admin'
# project_name='demo'
# project_domain_id='default'
# user_domain_id='default'

for key in OS_REQUIRED_KEYS:
    env_key = OS_PREFIX + key.upper()
    value = os.environ.get(env_key)
    if not value:
        print("Missing %s in environment vars."
              "Openstack environment vars should be loaded before "
              "running this script", env_key)
    _CREDENTIALS[key] = value

auth = identity.Password(auth_url=_CREDENTIALS['auth_url'],
                         username=_CREDENTIALS['username'],
                         password=_CREDENTIALS['password'],
                         project_name=_CREDENTIALS['project_name'],
                         project_domain_id=_CREDENTIALS['project_domain_id'],
                         user_domain_id='default')

sess = session.Session(auth=auth)
neutron_client = client.Client(session=sess)

l3_agents = neutron_client.list_agents(agent_type='L3 agent')
print('The l3 agents are %s', l3_agents)
print('')

routers = neutron_client.list_routers()
print('The routers are %s', routers)
print('')

l3_agent_2_routers = {}
for l3_agent in l3_agents['agents']:
    routers = neutron_client.list_routers_on_l3_agent(l3_agent['id'])
    l3_agent_2_routers[l3_agent['id']] = routers['routers']
    print('The routers hosted on the L3 agent: '
          '%(l3_agent)s are below: %(routers)s',
          {'l3_agent': l3_agent['id'], 'routers': routers})
print('')

l3_agent_routers_count = {}
for l3_agent in l3_agents['agents']:
    router_num = len(l3_agent_2_routers[l3_agent['id']]) \
        if l3_agent_2_routers[l3_agent['id']] else 0
    l3_agent_routers_count[l3_agent['id']]= router_num

print(l3_agent_routers_count)
print('')


def find_max_min(l3_agent_routers_count):
    max = 0
    min = 100000
    max_agent = None
    min_agent = None

    for k in l3_agent_routers_count.keys():
        if l3_agent_routers_count[k] > max:
            max = l3_agent_routers_count[k]
            max_agent = k
        if l3_agent_routers_count[k] < min:
            min = l3_agent_routers_count[k]
            min_agent = k

    return max_agent, min_agent


max_agent, min_agent = find_max_min(l3_agent_routers_count)

reschedule_router_id = l3_agent_2_routers[max_agent][-1]['id']
neutron_client.remove_router_from_l3_agent(max_agent, reschedule_router_id)
print('After remove the %(router)s from %(l3_agent)s',
      {'router': reschedule_router_id, 'l3_agent': max_agent})
print(neutron_client.list_routers_on_l3_agent(max_agent))
print('')

neutron_client.add_router_to_l3_agent(min_agent,
                                      {'router_id': reschedule_router_id})
print('After add the %(router)s to %(l3_agent)s',
      {'router': reschedule_router_id, 'l3_agent': min_agent})
print(neutron_client.list_routers_on_l3_agent(min_agent))
print('')
