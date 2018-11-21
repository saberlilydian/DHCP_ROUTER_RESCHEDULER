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

dhcp_agents = neutron_client.list_agents(agent_type='DHCP agent')
print("DHCP agents are: %s", dhcp_agents)
print('')

dhcp_agent_2_networks = {}
for dhcp_agent in dhcp_agents['agents']:
    networks = neutron_client.list_networks_on_dhcp_agent(dhcp_agent['id'])
    dhcp_agent_2_networks[dhcp_agent['id']] = networks['networks']
    print('The networks hosted on the DHCP agent: '
          '%(dhcp_agent)s are below: %(networks)s',
          {'dhcp_agent': dhcp_agent['id'], 'networks': networks})
print('')

dhcp_agent_networks_count = {}
for dhcp_agent in dhcp_agents['agents']:
    network_num = len(dhcp_agent_2_networks[dhcp_agent['id']]) \
        if dhcp_agent_2_networks[dhcp_agent['id']] else 0
    dhcp_agent_networks_count[dhcp_agent['id']]= network_num

print(dhcp_agent_networks_count)
print('')


def find_max_min(dhcp_agent_networks_count):
    max = 0
    min = 100000
    max_agent = None
    min_agent = None

    for k in dhcp_agent_networks_count.keys():
        if dhcp_agent_networks_count[k] > max:
            max = dhcp_agent_networks_count[k]
            max_agent = k
        if dhcp_agent_networks_count[k] < min:
            min = dhcp_agent_networks_count[k]
            min_agent = k

    return max_agent, min_agent


max_agent, min_agent = find_max_min(dhcp_agent_networks_count)

reschedule_network_id = dhcp_agent_2_networks[max_agent][-1]['id']
neutron_client.remove_network_from_dhcp_agent(max_agent, reschedule_network_id)
print('After remove the %(network)s from %(dhcp_agent)s',
      {'network': reschedule_network_id, 'dhcp_agent': max_agent})
print(neutron_client.list_networks_on_dhcp_agent(max_agent))
print('')

neutron_client.add_network_to_dhcp_agent(min_agent,
                                         {'network_id': reschedule_network_id})
print('After add the %(network)s to %(dhcp_agent)s',
      {'network': reschedule_network_id, 'dhcp_agent': min_agent})
print(neutron_client.list_networks_on_dhcp_agent(min_agent))
print('')

